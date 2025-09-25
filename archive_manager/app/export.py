from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, Tuple
from zipfile import ZIP_DEFLATED, ZipFile


BASE_DIR = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = BASE_DIR / "archive_manager"
DEFAULT_FILES = [
    BASE_DIR / "README.md",
    BASE_DIR / "requirements.txt",
]
EXCLUDED_DIR_NAMES = {"__pycache__", ".git"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pyd"}


def _iter_package_files(package_root: Path) -> Iterable[Tuple[Path, Path]]:
    """Yield files from the package alongside their archive relative paths."""

    for path in package_root.rglob("*"):
        if path.is_dir():
            if path.name in EXCLUDED_DIR_NAMES:
                continue
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        relative = path.relative_to(BASE_DIR)
        yield path, relative


def build_application_bundle(*, include_db: bool = False) -> io.BytesIO:
    """Return an in-memory ZIP archive containing the application files."""

    buffer = io.BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as bundle:
        for file_path, archive_path in _iter_package_files(PACKAGE_ROOT):
            bundle.write(file_path, archive_path.as_posix())

        for file_path in DEFAULT_FILES:
            if file_path.exists():
                bundle.write(file_path, file_path.relative_to(BASE_DIR).as_posix())

        db_path = BASE_DIR / "archive_manager.db"
        if include_db and db_path.exists():
            bundle.write(db_path, db_path.name)

    buffer.seek(0)
    return buffer
