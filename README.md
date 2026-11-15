# Tennis Coach

A private, local-first browser application for reviewing tennis technique from phone video.

The first implementation milestone is intentionally small: import one video, select one forehand attempt, review it with a body-pose overlay, add manual markers and notes, and reopen the saved review.

## Development setup

The application targets Python 3.12. With [`uv`](https://docs.astral.sh/uv/) installed:

```bash
uv sync --group dev
uv run tennis-coach
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) if the browser does not open
automatically. The app creates its private managed library inside the project at
`.data/library`. The entire `.data/` folder is ignored by Git. Set `TENNIS_COACH_LIBRARY` to
use a different folder.

Run the tests with:

```bash
uv run pytest
```

Pose dependencies are isolated in an optional group until pose work begins:

```bash
uv sync --extra pose --group dev
```

The pose group intentionally installs only `opencv-contrib-python`, which is required by the
current MediaPipe package. Do not add a second OpenCV wheel because multiple packages providing
`cv2` conflict with one another.

## Current status

The browser interface can import MP4/MOV videos into a managed local library without altering
the uploaded source. Imported videos are content-hashed, validated with PyAV, and recorded in
SQLite with their display dimensions, duration, and orientation. Reimporting the same bytes
reuses the existing asset.

From the browser:

1. Select **Import a video** or drag an MP4/MOV onto the upload card.
2. Choose a recording from the private library list.
3. Review it with the timeline, slow-motion speeds, and frame controls.

The previous PySide desktop prototype remains available temporarily with
`uv run tennis-coach-desktop`, but the browser interface is now the primary application.
Attempt ranges, markers, saved observations, and pose analysis are the next implementation
packets.

See [the foundation and vertical-slice plan](project_plans/03_PHASE_1_FOUNDATION_AND_VERTICAL_SLICE.md) for the scoped build sequence.
