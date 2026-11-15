import sqlite3

from tennis_coach_app.storage import Library


def test_initial_migration_creates_expected_tables(tmp_path) -> None:
    library = Library.open_or_create(tmp_path / "library")

    with sqlite3.connect(library.database.path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migration ORDER BY version"
        ).fetchall()

    assert {
        "attempt",
        "event_marker",
        "media_asset",
        "pose_run",
        "review_note",
        "schema_migration",
    }.issubset(tables)
    assert versions == [(1,)]


def test_reopening_library_does_not_reapply_migration(tmp_path) -> None:
    root = tmp_path / "library"
    Library.open_or_create(root)
    reopened = Library.open_or_create(root)

    with sqlite3.connect(reopened.database.path) as connection:
        applied_count = connection.execute("SELECT COUNT(*) FROM schema_migration").fetchone()[0]

    assert applied_count == 1

