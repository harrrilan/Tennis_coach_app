from __future__ import annotations

import os
import sys
import tempfile
import threading
import webbrowser
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from tennis_coach_app.models import MediaAsset
from tennis_coach_app.storage import Library, LibraryError
from tennis_coach_app.storage.library import SUPPORTED_VIDEO_EXTENSIONS

STATIC_DIRECTORY = Path(__file__).parent / "static"


def create_app(library_root: str | Path | None = None) -> FastAPI:
    """Create the local-only browser application."""
    root = Path(library_root) if library_root is not None else _default_library_root()
    library = Library.open_or_create(root)
    app = FastAPI(
        title="Tennis Coach",
        description="Private local tennis video review",
        version="0.1.0",
    )
    app.state.library = library

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIRECTORY / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/library")
    def library_info() -> dict[str, object]:
        return {
            "path": str(library.root),
            "video_count": len(library.list_media()),
        }

    @app.get("/api/videos")
    def list_videos() -> list[dict[str, object]]:
        return [_asset_response(asset) for asset in library.list_media()]

    @app.post("/api/videos", status_code=201)
    async def import_video(
        video: Annotated[UploadFile, File(description="An MP4 or MOV tennis video")],
    ) -> dict[str, object]:
        original_filename = _safe_filename(video.filename)
        extension = Path(original_filename).suffix.lower()
        if extension not in SUPPORTED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Choose an MP4 or MOV video.")

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix="tennis-upload-",
                suffix=extension,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while chunk := await video.read(1024 * 1024):
                    temporary_file.write(chunk)

            asset = await run_in_threadpool(
                library.import_video,
                temporary_path,
                original_filename=original_filename,
            )
        except LibraryError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            await video.close()
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return _asset_response(asset)

    @app.get("/api/videos/{asset_id}/stream", name="stream_video")
    def stream_video(asset_id: str) -> FileResponse:
        asset = library.get_media(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Video not found.")
        path = library.resolve_media_path(asset)
        if not path.is_file():
            raise HTTPException(status_code=410, detail="The managed video file is missing.")
        media_type = "video/quicktime" if path.suffix.lower() == ".mov" else "video/mp4"
        return FileResponse(path, media_type=media_type)

    app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")
    return app


def main() -> None:
    """Run the local server and open the interface in a browser when possible."""
    host = os.environ.get("TENNIS_COACH_HOST", "127.0.0.1")
    port = int(os.environ.get("TENNIS_COACH_PORT", "8000"))
    url = f"http://{host}:{port}"
    if sys.platform == "darwin" or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    print(f"Tennis Coach is ready at {url}")
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


def _default_library_root() -> Path:
    configured = os.environ.get("TENNIS_COACH_LIBRARY")
    if configured:
        return Path(configured).expanduser()
    return Path.cwd() / ".data" / "library"


def _safe_filename(filename: str | None) -> str:
    if not filename:
        return "uploaded-video.mp4"
    normalized = filename.replace("\\", "/")
    return normalized.rsplit("/", maxsplit=1)[-1]


def _asset_response(asset: MediaAsset) -> dict[str, object]:
    return {
        "id": asset.id,
        "name": asset.original_filename,
        "size_bytes": asset.file_size_bytes,
        "width": asset.width,
        "height": asset.height,
        "duration_seconds": asset.duration_seconds,
        "orientation_degrees": asset.orientation_degrees,
        "imported_at": asset.imported_at,
        "stream_url": f"/api/videos/{asset.id}/stream",
    }
