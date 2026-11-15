import hashlib

import pytest

from tennis_coach_app.storage import Library, LibraryError


def test_create_library_builds_portable_folder_structure(tmp_path) -> None:
    root = tmp_path / "tennis-library"

    library = Library.open_or_create(root)

    assert library.root == root.resolve()
    assert (root / "library.sqlite3").is_file()
    assert (root / "media").is_dir()
    assert (root / "analysis").is_dir()
    assert (root / "thumbnails").is_dir()


def test_new_library_rejects_nonempty_unmanaged_folder(tmp_path) -> None:
    root = tmp_path / "not-a-library"
    root.mkdir()
    (root / "personal-file.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(LibraryError, match="empty folder"):
        Library.open_or_create(root)

    assert (root / "personal-file.txt").read_text(encoding="utf-8") == "keep me"


def test_import_video_preserves_source_and_registers_managed_copy(tmp_path, make_video) -> None:
    source = tmp_path / "Forehand.MP4"
    make_video(source, width=80, height=48)
    source_bytes = source.read_bytes()
    source_stat = source.stat()
    library = Library.open_or_create(tmp_path / "library")

    asset = library.import_video(source)

    expected_hash = hashlib.sha256(source_bytes).hexdigest()
    managed_path = library.resolve_media_path(asset)
    assert source.read_bytes() == source_bytes
    assert source.stat().st_mtime_ns == source_stat.st_mtime_ns
    assert managed_path.read_bytes() == source_bytes
    assert asset.content_hash == expected_hash
    assert asset.library_relative_path.as_posix() == f"media/{expected_hash}.mp4"
    assert asset.original_filename == "Forehand.MP4"
    assert asset.file_size_bytes == len(source_bytes)
    assert asset.width == 80
    assert asset.height == 48
    assert asset.duration_seconds == pytest.approx(6 / 30)
    assert asset.orientation_degrees == 0
    assert library.list_media() == [asset]


def test_importing_same_content_reuses_existing_asset(tmp_path, make_video) -> None:
    source = tmp_path / "forehand.mov"
    make_video(source)
    library = Library.open_or_create(tmp_path / "library")

    first = library.import_video(source)
    second = library.import_video(source)

    assert second == first
    assert library.list_media() == [first]
    assert len(list(library.media_directory.iterdir())) == 1


def test_import_rejects_unsupported_file_without_copying_it(tmp_path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not a video", encoding="utf-8")
    library = Library.open_or_create(tmp_path / "library")

    with pytest.raises(LibraryError, match="MP4 or MOV"):
        library.import_video(source)

    assert source.read_text(encoding="utf-8") == "not a video"
    assert list(library.media_directory.iterdir()) == []


def test_import_rejects_corrupt_video_and_removes_partial_copy(tmp_path) -> None:
    source = tmp_path / "corrupt.mp4"
    source.write_bytes(b"not an encoded video")
    library = Library.open_or_create(tmp_path / "library")

    with pytest.raises(LibraryError, match="not a usable video"):
        library.import_video(source)

    assert source.read_bytes() == b"not an encoded video"
    assert library.list_media() == []
    assert list(library.media_directory.iterdir()) == []
