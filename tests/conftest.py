import os
from fractions import Fraction

import av
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def make_video():
    """Create a small, real encoded MP4 fixture with controlled frame timestamps."""

    def _make_video(
        path,
        *,
        width: int = 64,
        height: int = 48,
        rate: int = 30,
        frame_pts: tuple[int, ...] = (0, 1, 2, 3, 4, 5),
    ):
        with av.open(str(path), mode="w") as container:
            stream = container.add_stream("mpeg4", rate=rate)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"
            for index, pts in enumerate(frame_pts):
                image = np.zeros((height, width, 3), dtype=np.uint8)
                image[:, :, 0] = (index * 20) % 256
                image[:, :, 1] = 80
                frame = av.VideoFrame.from_ndarray(image, format="rgb24")
                frame.pts = pts
                frame.time_base = Fraction(1, rate)
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        return path

    return _make_video
