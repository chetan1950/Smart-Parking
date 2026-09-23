"""Safe file-upload helpers."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def extension_of(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return bool(filename and "." in filename and extension_of(filename) in allowed_extensions)


def save_upload(upload: FileStorage, destination: Path) -> tuple[Path, str]:
    """Save an upload with a collision-resistant, path-safe filename."""
    original_name = secure_filename(upload.filename or "")
    if not original_name:
        raise ValueError("Please choose a valid file.")
    suffix = Path(original_name).suffix.lower()
    stored_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:10]}{suffix}"
    destination.mkdir(parents=True, exist_ok=True)
    file_path = destination / stored_name
    upload.save(file_path)
    return file_path, original_name


def relative_media_path(path: Path, base_dir: Path) -> str:
    """Return a URL-safe application-relative path using forward slashes."""
    return path.resolve().relative_to(base_dir.resolve()).as_posix()
