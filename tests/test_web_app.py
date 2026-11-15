import httpx
import pytest

from tennis_coach_app.web.app import create_app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_browser_home_page_and_health(tmp_path) -> None:
    transport = httpx.ASGITransport(app=create_app(tmp_path / "library"))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        home = await client.get("/")
        health = await client.get("/api/health")
        library = await client.get("/api/library")

        assert home.status_code == 200
        assert "Bring in one forehand video" in home.text
        assert "/static/styles.css" in home.text
        assert health.json() == {"status": "ok"}
        assert library.json() == {
            "path": str((tmp_path / "library").resolve()),
            "video_count": 0,
        }


@pytest.mark.anyio
async def test_browser_upload_lists_and_streams_managed_video(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "Forehand Session.mp4", width=80, height=48)
    source_bytes = source.read_bytes()
    transport = httpx.ASGITransport(app=create_app(tmp_path / "library"))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        uploaded = await client.post(
            "/api/videos",
            files={"video": (source.name, source_bytes, "video/mp4")},
        )

        assert uploaded.status_code == 201
        video = uploaded.json()
        assert video["name"] == source.name
        assert video["width"] == 80
        assert video["height"] == 48
        assert video["duration_seconds"] == 0.2

        listed = await client.get("/api/videos")
        assert listed.status_code == 200
        assert listed.json() == [video]

        streamed = await client.get(video["stream_url"], headers={"Range": "bytes=0-31"})
        assert streamed.status_code == 206
        assert streamed.content == source_bytes[:32]
        assert streamed.headers["accept-ranges"] == "bytes"


@pytest.mark.anyio
async def test_browser_upload_reuses_duplicate_video(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "forehand.mov")
    source_bytes = source.read_bytes()
    transport = httpx.ASGITransport(app=create_app(tmp_path / "library"))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/videos",
            files={"video": (source.name, source_bytes, "video/quicktime")},
        )
        second = await client.post(
            "/api/videos",
            files={"video": (source.name, source_bytes, "video/quicktime")},
        )

        assert first.status_code == 201
        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]
        assert len((await client.get("/api/videos")).json()) == 1


@pytest.mark.anyio
async def test_browser_rejects_unsupported_upload(tmp_path) -> None:
    transport = httpx.ASGITransport(app=create_app(tmp_path / "library"))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/videos",
            files={"video": ("notes.txt", b"not a video", "text/plain")},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Choose an MP4 or MOV video."
        assert (await client.get("/api/videos")).json() == []
