"""Sandboxed file read/write service with ETag concurrency control.

ALL file operations in the application must go through this service.
No router or other service may read/write files directly.

Security model:
  - Every path is resolved to its real path via Path.resolve() BEFORE
    comparing against the allowlist.  This defeats symlink traversal.
  - /opt/homebrew/.../openclaw/ is read-only.
  - ~/.openclaw/ (and workspace-* siblings) are read/write.
  - Any path that resolves outside these roots raises PermissionError.
  - Atomic writes: write to .tmp, then os.rename().  Never leaves a
    partial write on disk.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
import structlog

from app.config import Settings

logger = structlog.get_logger(__name__)

# Language detection map (file extension → Monaco language id)
_LANGUAGE_MAP: dict[str, str] = {
    ".md": "markdown",
    ".py": "python",
    ".json": "json",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".js": "javascript",
    ".jsx": "javascriptreact",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".env": "plaintext",
    ".txt": "plaintext",
    ".css": "css",
    ".html": "html",
    ".xml": "xml",
    ".sql": "sql",
}

# Read-only roots — writes are rejected even if the path is inside these
_READ_ONLY_ROOTS: list[Path] = [
    Path("/opt/homebrew/lib/node_modules/openclaw"),
]


class FileService:
    """Sandboxed file access with ETag-based optimistic concurrency control.

    Args:
        settings: Application settings (provides OPENCLAW_HOME).
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise FileService.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        # Read/write root — every path must be inside this after resolve()
        self._rw_root: Path = settings.OPENCLAW_HOME.resolve()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_file(self, path: Path) -> tuple[str, str]:
        """Read a file and return (content, etag).

        Args:
            path: Absolute path to the file.

        Returns:
            Tuple of (file content as string, ETag string).

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the path is outside the allowed sandbox.
        """
        real = self._check_path(path, write=False)
        if not real.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not real.is_file():
            raise FileNotFoundError(f"Not a file: {path}")

        # Read bytes once; derive both etag and decoded content from the same read.
        async with aiofiles.open(real, "rb") as fh:
            raw = await fh.read()

        etag = self._hash_bytes(raw)
        content = raw.decode("utf-8", errors="replace")
        return content, etag

    async def write_file(self, path: Path, content: str, if_match: str | None) -> str:
        """Write content to a file atomically, with ETag concurrency check.

        Args:
            path: Absolute path to the target file.
            content: UTF-8 content to write.
            if_match: Client's If-Match ETag value.  If provided and the file
                      exists, the current ETag must match or a conflict is raised.

        Returns:
            New ETag for the written file.

        Raises:
            PermissionError: Path is outside the sandbox or in a read-only root.
            ETagMismatchError: File changed since the client last read it.
        """
        from app.middleware.error_handler import ETagMismatchError  # avoid circular at module level

        real = self._check_path(path, write=True)

        # ETag concurrency check (only if the file already exists)
        if if_match is not None and real.exists():
            async with aiofiles.open(real, "rb") as fh:
                existing_bytes = await fh.read()
            current = self._hash_bytes(existing_bytes)
            if current != if_match:
                raise ETagMismatchError(
                    f"File has changed since last read (ETag mismatch: "
                    f"expected {if_match!r}, got {current!r})",
                    current_etag=current,
                )

        # Ensure parent directory exists
        real.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: .tmp → rename
        tmp = real.with_suffix(real.suffix + ".tmp")
        try:
            async with aiofiles.open(tmp, "w", encoding="utf-8") as fh:
                await fh.write(content)
            os.rename(tmp, real)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise

        new_etag = self._hash_bytes(content.encode("utf-8"))
        logger.info(
            "file_written",
            path=str(real),
            bytes=len(content.encode()),
            etag=new_etag,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return new_etag

    def compute_etag(self, path: Path) -> str:
        """Compute a content-hash ETag for a file.

        Uses SHA-1 of the file's raw bytes, truncated to 16 hex chars.
        Content-based hashing avoids the same-second race condition that
        mtime:size ETags have when two writes occur within one second.

        Args:
            path: Absolute path to the file (must exist).

        Returns:
            16-character hex ETag string.
        """
        return self._hash_bytes(path.read_bytes())

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        """Return a 16-char hex SHA-1 hash of *data*.

        Args:
            data: Raw bytes to hash.

        Returns:
            16-character lowercase hex string.
        """
        return hashlib.sha1(data, usedforsecurity=False).hexdigest()[:16]

    def get_mtime(self, path: Path) -> datetime:
        """Return the last-modified time of a file as UTC datetime.

        Args:
            path: Absolute path to the file.

        Returns:
            UTC datetime of last modification.
        """
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    @staticmethod
    def detect_language(filename: str) -> str:
        """Detect the Monaco language identifier for a filename.

        Args:
            filename: Bare filename or path string.

        Returns:
            Monaco language identifier string.
        """
        suffix = Path(filename).suffix.lower()
        return _LANGUAGE_MAP.get(suffix, "plaintext")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_path(self, path: Path, *, write: bool) -> Path:
        """Resolve path and verify it is inside the allowed sandbox.

        Resolution happens FIRST so symlinks cannot escape the sandbox.

        Args:
            path: Path to check (may be relative or contain symlinks).
            write: Whether this is a write operation.

        Returns:
            The real (resolved) Path.

        Raises:
            PermissionError: If the resolved path is outside the sandbox,
                             or if write=True and path is inside a read-only root.
        """
        try:
            real = path.resolve()
        except OSError as exc:
            raise PermissionError(f"Cannot resolve path: {path}") from exc

        # Check against read/write root (OPENCLAW_HOME and workspace siblings)
        # We allow any path under the parent of OPENCLAW_HOME that starts with
        # workspace or agents — but the simplest safe rule is: must be under
        # the same parent dir as OPENCLAW_HOME.
        openclaw_parent = self._rw_root.parent

        # Must be under ~/.openclaw/ OR under a workspace-* / agents/ sibling
        # that lives in the same parent directory.
        allowed = (
            real == self._rw_root
            or str(real).startswith(str(self._rw_root) + os.sep)
            # workspace-coder, workspace-analyst, etc.
            or str(real).startswith(str(openclaw_parent / "workspace"))
            or str(real).startswith(str(self._rw_root / "workspace"))
            or str(real).startswith(str(self._rw_root / "agents"))
        )

        if not allowed:
            # Also allow read-only roots (for installed skill files, etc.)
            for ro_root in _READ_ONLY_ROOTS:
                try:
                    ro_resolved = ro_root.resolve()
                except OSError:
                    continue
                if real == ro_resolved or str(real).startswith(str(ro_resolved) + os.sep):
                    if write:
                        raise PermissionError(
                            f"Access denied: {real} is in a read-only root ({ro_root})"
                        )
                    return real  # read is fine

            raise PermissionError(
                f"Access denied: {real} is outside the allowed sandbox "
                f"(root: {self._rw_root})"
            )

        # Block writes to read-only roots even when inside OPENCLAW_HOME
        if write:
            for ro_root in _READ_ONLY_ROOTS:
                try:
                    ro_resolved = ro_root.resolve()
                except OSError:
                    continue
                if real == ro_resolved or str(real).startswith(str(ro_resolved) + os.sep):
                    raise PermissionError(
                        f"Access denied: {real} is in a read-only root ({ro_root})"
                    )

        return real
