"""File models for workspace file listings."""

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    """A single file entry from recursive workspace listing."""

    name: str = Field(..., description="Filename")
    path: str = Field(..., description="Relative path from workspace root")
    size: int = Field(..., description="File size in bytes")
    mtime: float = Field(..., description="Last modified Unix timestamp")
    is_binary: bool = Field(..., description="Detected as binary by extension")
    is_directory: bool = Field(False, description="Whether this is a directory entry")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "SOUL.md",
                "path": "SOUL.md",
                "size": 3800,
                "mtime": 1772031239.308,
                "is_binary": False,
                "is_directory": False,
            }
        }
    }


class FileListResponse(BaseModel):
    """Response for recursive file listing."""

    files: list[FileEntry] = Field(..., description="List of file entries")
    total: int = Field(..., description="Number of files returned")
    truncated: bool = Field(False, description="True if max_files limit was reached")

    model_config = {
        "json_schema_extra": {
            "example": {
                "files": [
                    {
                        "name": "SOUL.md",
                        "path": "SOUL.md",
                        "size": 3800,
                        "mtime": 1772031239.308,
                        "is_binary": False,
                        "is_directory": False,
                    },
                ],
                "total": 1,
                "truncated": False,
            }
        }
    }
