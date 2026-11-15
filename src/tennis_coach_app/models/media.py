from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class MediaMetadata:
    """Display-oriented metadata for the primary video stream."""

    width: int
    height: int
    duration_seconds: float
    orientation_degrees: int


@dataclass(frozen=True, slots=True)
class DecodedFrame:
    """One orientation-corrected RGB frame at its source presentation timestamp."""

    timestamp_seconds: float
    presentation_timestamp: int
    time_base_numerator: int
    time_base_denominator: int
    rgb: NDArray[np.uint8]


@dataclass(frozen=True, slots=True)
class MediaAsset:
    """An immutable source video managed by a library."""

    id: str
    library_relative_path: Path
    content_hash: str
    original_filename: str
    file_size_bytes: int
    imported_at: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    orientation_degrees: int | None = None
