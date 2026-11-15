from __future__ import annotations

MIGRATION_001 = """
CREATE TABLE media_asset (
    id TEXT PRIMARY KEY,
    library_relative_path TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL UNIQUE,
    original_filename TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes >= 0),
    width INTEGER,
    height INTEGER,
    duration_seconds REAL,
    orientation_degrees INTEGER,
    imported_at TEXT NOT NULL
);

CREATE TABLE attempt (
    id TEXT PRIMARY KEY,
    media_asset_id TEXT NOT NULL REFERENCES media_asset(id) ON DELETE RESTRICT,
    start_timestamp_seconds REAL NOT NULL CHECK (start_timestamp_seconds >= 0),
    end_timestamp_seconds REAL NOT NULL,
    stroke_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (end_timestamp_seconds > start_timestamp_seconds)
);

CREATE TABLE event_marker (
    id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES attempt(id) ON DELETE CASCADE,
    event_name TEXT NOT NULL,
    source_timestamp_seconds REAL NOT NULL CHECK (source_timestamp_seconds >= 0),
    is_approximate INTEGER NOT NULL DEFAULT 0 CHECK (is_approximate IN (0, 1)),
    UNIQUE (attempt_id, event_name)
);

CREATE TABLE review_note (
    attempt_id TEXT PRIMARY KEY REFERENCES attempt(id) ON DELETE CASCADE,
    user_note TEXT NOT NULL DEFAULT '',
    practice_cue TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE pose_run (
    id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES attempt(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL,
    configuration_version TEXT NOT NULL,
    status TEXT NOT NULL,
    artifact_path TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_attempt_media_asset ON attempt(media_asset_id);
CREATE INDEX idx_event_marker_attempt ON event_marker(attempt_id);
CREATE INDEX idx_pose_run_attempt ON pose_run(attempt_id);
"""

MIGRATIONS: tuple[tuple[int, str], ...] = ((1, MIGRATION_001),)

