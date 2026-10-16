"""Sandboxed file reader tool.

Reads text files only inside a designated sandbox directory.
Rejects .., absolute paths, and symlinks escaping the sandbox.
"""

from pathlib import Path

from pydantic import BaseModel, Field

# Define sandbox root directory (e.g., ./sandbox relative to project root or absolute)
SANDBOX_DIR = Path(__file__).resolve().parent.parent / "sandbox"


class FileReaderArgs(BaseModel):
    filepath: str = Field(..., description="Relative file path inside the sandbox directory.")


def read_file(filepath: str) -> dict[str, str]:
    """Read a text file strictly inside the sandbox directory."""
    # Ensure sandbox dir exists
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Resolve path
        target_path = (SANDBOX_DIR / filepath).resolve()

        # Check path traversal
        if not target_path.is_relative_to(SANDBOX_DIR.resolve()):
            return {"error": "Path traversal rejected: file is outside sandbox."}

        # Check symlinks escaping sandbox
        if target_path.is_symlink():
            real_target = target_path.readlink()
            if not (SANDBOX_DIR / real_target).resolve().is_relative_to(SANDBOX_DIR.resolve()):
                return {"error": "Symlink escape rejected."}

        if not target_path.exists() or not target_path.is_file():
            return {"error": "File not found or is not a file."}

        content = target_path.read_text(encoding="utf-8")
        return {"content": content}
    except Exception as exc:
        return {"error": f"Failed to read file: {str(exc)}"}
