from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from tennis_coach_app.media import MediaDecodeError, inspect_video
from tennis_coach_app.models import MediaAsset
from tennis_coach_app.storage.database import Database

SUPPORTED_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov"})
DATABASE_FILENAME = "library.sqlite3"
MANAGED_DIRECTORIES = ("media", "analysis", "thumbnails")


class LibraryError(Exception):
    """Raised when a local library operation cannot be completed safely."""


class Library:
    """A portable folder containing source media, records, and derived artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.database = Database(root / DATABASE_FILENAME)

    @property
    def media_directory(self) -> Path:
        return self.root / "media"

    @classmethod
    def open_or_create(cls, root: str | Path) -> Library:
        library_root = Path(root).expanduser().resolve()
        if library_root.exists() and not library_root.is_dir():
            raise LibraryError(f"Library path is not a folder: {library_root}")

        library_root.mkdir(parents=True, exist_ok=True)
        database_path = library_root / DATABASE_FILENAME
        if not database_path.exists():
            unexpected_entries = [
                entry
                for entry in library_root.iterdir()
                if entry.name not in {".DS_Store", *MANAGED_DIRECTORIES}
            ]
            if unexpected_entries:
                raise LibraryError(
                    "Choose an empty folder for a new library, or select an existing Tennis "
                    "Coach library."
                )

        for directory_name in MANAGED_DIRECTORIES:
            (library_root / directory_name).mkdir(exist_ok=True)

        library = cls(library_root)
        library.database.initialize()
        return library

    def import_video(
        self,
        source: str | Path,
        *,
        original_filename: str | None = None,
    ) -> MediaAsset:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise LibraryError(f"Video file does not exist: {source_path}")

        extension = source_path.suffix.lower()
        if extension not in SUPPORTED_VIDEO_EXTENSIONS:
            raise LibraryError("Choose an MP4 or MOV video.")

        initial_stat = source_path.stat()
        temporary_path: Path | None = None
        try:
            with source_path.open("rb") as source_file:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix=".import-",
                    suffix=extension,
                    dir=self.media_directory,
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    digest = hashlib.sha256()
                    while chunk := source_file.read(1024 * 1024):
                        digest.update(chunk)
                        temporary_file.write(chunk)
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())

            final_stat = source_path.stat()
            copied_size = temporary_path.stat().st_size
            if (
                initial_stat.st_size != final_stat.st_size
                or initial_stat.st_mtime_ns != final_stat.st_mtime_ns
                or copied_size != initial_stat.st_size
            ):
                raise LibraryError(
                    "The source video changed while it was being imported. Try again."
                )

            content_hash = digest.hexdigest()
            existing = self._find_media_by_hash(content_hash)
            if existing is not None:
                temporary_path.unlink()
                return existing

            relative_path = Path("media") / f"{content_hash}{extension}"
            destination = self.root / relative_path
            os.replace(temporary_path, destination)
            temporary_path = None

            try:
                metadata = inspect_video(destination)
            except MediaDecodeError as error:
                destination.unlink(missing_ok=True)
                raise LibraryError(f"The selected file is not a usable video: {error}") from error

            asset = MediaAsset(
                id=str(uuid4()),
                library_relative_path=relative_path,
                content_hash=content_hash,
                original_filename=original_filename or source_path.name,
                file_size_bytes=copied_size,
                imported_at=datetime.now(UTC).isoformat(),
                width=metadata.width,
                height=metadata.height,
                duration_seconds=metadata.duration_seconds,
                orientation_degrees=metadata.orientation_degrees,
            )
            self._insert_media(asset)
            return asset
        except OSError as error:
            raise LibraryError(f"Could not import the video: {error}") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def resolve_media_path(self, asset: MediaAsset) -> Path:
        return self.root / asset.library_relative_path

    def list_media(self) -> list[MediaAsset]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM media_asset ORDER BY imported_at, id"
            ).fetchall()
        return [self._media_from_row(row) for row in rows]

    def get_media(self, asset_id: str) -> MediaAsset | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM media_asset WHERE id = ?",
                (asset_id,),
            ).fetchone()
        return None if row is None else self._media_from_row(row)

    def _find_media_by_hash(self, content_hash: str) -> MediaAsset | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM media_asset WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
        return None if row is None else self._media_from_row(row)

    def _insert_media(self, asset: MediaAsset) -> None:
        try:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO media_asset (
                        id,
                        library_relative_path,
                        content_hash,
                        original_filename,
                        file_size_bytes,
                        width,
                        height,
                        duration_seconds,
                        orientation_degrees,
                        imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        asset.library_relative_path.as_posix(),
                        asset.content_hash,
                        asset.original_filename,
                        asset.file_size_bytes,
                        asset.width,
                        asset.height,
                        asset.duration_seconds,
                        asset.orientation_degrees,
                        asset.imported_at,
                    ),
                )
        except sqlite3.Error as error:
            self.resolve_media_path(asset).unlink(missing_ok=True)
            raise LibraryError(f"Could not save the imported video record: {error}") from error

    @staticmethod
    def _media_from_row(row: sqlite3.Row) -> MediaAsset:
        return MediaAsset(
            id=row["id"],
            library_relative_path=Path(row["library_relative_path"]),
            content_hash=row["content_hash"],
            original_filename=row["original_filename"],
            file_size_bytes=row["file_size_bytes"],
            imported_at=row["imported_at"],
            width=row["width"],
            height=row["height"],
            duration_seconds=row["duration_seconds"],
            orientation_degrees=row["orientation_degrees"],
        )
