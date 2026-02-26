"""OpenClaw configuration read/write service.

Handles:
  - Reading openclaw.json with secret redaction.
  - Writing openclaw.json with ETag concurrency control.
  - Backup rotation (max 10 backups kept).
  - Preserving __REDACTED__ values from the original file.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import structlog

from app.config import Settings
from app.models.config import ConfigResponse, ConfigValidateResponse, ConfigWriteRequest
from app.services.file_service import FileService

logger = structlog.get_logger(__name__)

# Keys whose string values should be replaced with __REDACTED__
_SECRET_PATTERN = re.compile(
    r"(key|token|secret|password|apikey|api_key|auth|credential|bearer|private)",
    re.IGNORECASE,
)
_REDACTED = "__REDACTED__"
_MAX_BACKUPS = 10


class ConfigService:
    """Manage openclaw.json with safety guards.

    Args:
        settings: Application settings (provides config_path).
        file_service: Sandboxed FileService for all I/O.
    """

    def __init__(self, settings: Settings, file_service: FileService) -> None:
        """Initialise ConfigService.

        Args:
            settings: Application settings.
            file_service: Sandboxed FileService.
        """
        self._settings = settings
        self._fs = file_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_config(self) -> ConfigResponse:
        """Read openclaw.json with secrets redacted.

        Returns:
            ConfigResponse containing the redacted config dict and ETag.

        Raises:
            FileNotFoundError: If openclaw.json does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        config_path = self._settings.config_path
        if not config_path.exists():
            raise FileNotFoundError(f"openclaw.json not found at {config_path}")

        content, etag = await self._fs.read_file(config_path)
        parsed: dict = json.loads(content)
        redacted = _redact_secrets(parsed)

        return ConfigResponse(
            config=redacted,
            etag=etag,
            path=str(config_path),
        )

    async def write_config(self, request: ConfigWriteRequest) -> ConfigResponse:
        """Write openclaw.json with ETag concurrency control and backup rotation.

        Steps:
          1. Check If-Match ETag (raises ETagMismatchError on mismatch).
          2. Read current config so __REDACTED__ values can be restored.
          3. Merge incoming config (restore __REDACTED__ → original values).
          4. Validate JSON structure.
          5. Create timestamped backup.
          6. Prune backups to the last 10.
          7. Atomic write (via FileService).

        Args:
            request: ConfigWriteRequest with config dict and optional ETag.

        Returns:
            ConfigResponse containing the newly written config and new ETag.

        Raises:
            ETagMismatchError: If If-Match header does not match current ETag.
            PermissionError: If the file is outside the sandbox.
        """
        config_path = self._settings.config_path

        # Read current file so we can (a) check ETag, (b) restore redacted values
        original_config: dict = {}
        if config_path.exists():
            raw, current_etag = await self._fs.read_file(config_path)
            try:
                original_config = json.loads(raw)
            except json.JSONDecodeError:
                original_config = {}

            # ETag check (only when the file already exists and client sent an ETag)
            if request.etag is not None:
                from app.middleware.error_handler import ETagMismatchError

                if request.etag != current_etag:
                    raise ETagMismatchError(
                        "openclaw.json has changed since last read",
                        current_etag=current_etag,
                    )

        # Restore any __REDACTED__ values from the original
        merged = _restore_redacted(request.config, original_config)

        # Validate: must be serialisable
        serialised = json.dumps(merged, indent=2, ensure_ascii=False)

        # Backup before write
        await self._create_backup(config_path, serialised)

        # Atomic write via FileService (no ETag check inside — we already did it)
        new_etag = await self._fs.write_file(config_path, serialised, if_match=None)

        logger.info("config_written", path=str(config_path), etag=new_etag)

        redacted = _redact_secrets(merged)
        return ConfigResponse(
            config=redacted,
            etag=new_etag,
            path=str(config_path),
        )

    async def validate_config(self, config: dict) -> ConfigValidateResponse:
        """Validate a configuration dict without writing it.

        Args:
            config: Config dict to validate.

        Returns:
            ConfigValidateResponse with valid flag plus any errors/warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Must be a dict at the top level
        if not isinstance(config, dict):
            errors.append("Config must be a JSON object at the top level.")
            return ConfigValidateResponse(valid=False, errors=errors, warnings=warnings)

        # Check default workspace path exists
        workspace_path = (
            config.get("agents", {})
            .get("defaults", {})
            .get("workspace")
        )
        if workspace_path:
            p = Path(workspace_path).expanduser()
            if not p.exists():
                warnings.append(f"Default workspace path does not exist: {workspace_path}")

        # Check gateway port if present
        gw_port = config.get("gateway", {}).get("port")
        if gw_port is not None:
            if not isinstance(gw_port, int) or not (1024 <= gw_port <= 65535):
                errors.append(
                    f"gateway.port must be an integer between 1024 and 65535 (got {gw_port!r})."
                )

        return ConfigValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Backup helpers
    # ------------------------------------------------------------------

    async def _create_backup(self, config_path: Path, content: str) -> None:
        """Write a timestamped backup of the current config file.

        Args:
            config_path: Path to openclaw.json.
            content: Current file content (already read by caller).
        """
        if not config_path.exists():
            return

        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = config_path.with_suffix(f".json.bak.{ts}")

        try:
            # Read actual current bytes from disk (not from `content` param which
            # is what we're about to write — we want the OLD content)
            old_content, _ = await self._fs.read_file(config_path)
            await self._fs.write_file(backup_path, old_content, if_match=None)
            logger.info("config_backup_created", path=str(backup_path))
        except Exception as exc:  # noqa: BLE001
            logger.warning("config_backup_failed", error=str(exc))

        await self._prune_backups(config_path)

    async def _prune_backups(self, config_path: Path) -> None:
        """Delete oldest backups beyond the max allowed count.

        Args:
            config_path: Path to openclaw.json (used to find sibling backups).
        """
        parent = config_path.parent
        stem = config_path.name  # e.g. "openclaw.json"
        backups = sorted(
            parent.glob(f"{stem}.bak.*"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(backups) > _MAX_BACKUPS:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                logger.info("config_backup_pruned", path=str(oldest))
            except OSError as exc:
                logger.warning("config_backup_prune_failed", path=str(oldest), error=str(exc))


# ---------------------------------------------------------------------------
# Pure utility functions
# ---------------------------------------------------------------------------

def _redact_secrets(config: dict) -> dict:
    """Recursively replace secret-looking string values with __REDACTED__.

    A key is considered secret if it matches _SECRET_PATTERN (case-insensitive).
    Only non-empty string values are redacted (booleans, ints, dicts left alone).

    Args:
        config: Configuration dict (may be nested).

    Returns:
        New dict with sensitive string values replaced.
    """
    result: dict = {}
    for k, v in config.items():
        if isinstance(v, dict):
            result[k] = _redact_secrets(v)
        elif isinstance(v, str) and v and _SECRET_PATTERN.search(k):
            result[k] = _REDACTED
        else:
            result[k] = v
    return result


def _restore_redacted(incoming: dict, original: dict) -> dict:
    """For any key whose incoming value is __REDACTED__, restore the original value.

    Works recursively for nested dicts.

    Args:
        incoming: New config dict (may contain __REDACTED__ sentinels).
        original: Original config dict read from disk.

    Returns:
        Merged dict with __REDACTED__ values replaced by originals.
    """
    result: dict = {}
    for k, v in incoming.items():
        if v == _REDACTED and k in original:
            # Keep the original secret value
            result[k] = original[k]
        elif isinstance(v, dict) and isinstance(original.get(k), dict):
            result[k] = _restore_redacted(v, original[k])
        else:
            result[k] = v
    return result
