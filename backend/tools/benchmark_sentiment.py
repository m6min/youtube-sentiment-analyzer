"""Exercise the real application lifespan and inference without external API/DB calls.

Run from backend: python tools/benchmark_sentiment.py
Linux reports peak process RSS and, in Docker, peak container memory.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("YOUTUBE_API_KEY", "benchmark")
os.environ.setdefault("POSTGRES_USER", "benchmark")
os.environ.setdefault("POSTGRES_PASSWORD", "benchmark")
os.environ.setdefault("POSTGRES_DB", "benchmark")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from app.db.session import get_db
from app.main import app, lifespan
from app.services.model import analyze_comments, analyze_title


def memory():
    result = {}
    try:
        import resource
        result["peak_process_mib"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except ImportError:
        import psutil
        result["peak_process_mib"] = round(psutil.Process().memory_info().peak_wset / 1024**2, 1)
    for name in ("memory.current", "memory.peak"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            result[name + "_mib"] = round(int(path.read_text()) / 1024**2, 1)
    return result


async def main():
    started = time.perf_counter()
    async def quiet_ping():
        await asyncio.Event().wait()

    with patch("app.main.self_ping", quiet_ping):
        async with lifespan(app):
            await measure(started)


async def measure(started):
    print(json.dumps({"stage": "loaded", "seconds": round(time.perf_counter() - started, 2), **memory()}), flush=True)
    title_score = analyze_title("Bu videoyu mutlaka izleyin!", app.state.title_analyze_model)
    for count in (1, 30, 100, 500):
        comments = [{"text": "Harika bir anlatım, çok beğendim." if i % 2 == 0
                    else "Berbat bir video, hiç beğenmedim."} for i in range(count)]
        started = time.perf_counter()
        score = await analyze_comments(comments, app.state.sentiment_model)
        print(json.dumps({"comments": count, "negative_percentage": score,
                        "title_score": title_score,
                          "seconds": round(time.perf_counter() - started, 2), **memory()}), flush=True)
    # Stress the configured token cap and simultaneous callers as well.
    long_comments = [{"text": "Bu videodaki açıklamaları beğenmedim. " * 100} for _ in range(30)]
    scores = await asyncio.gather(*(analyze_comments(long_comments, app.state.sentiment_model) for _ in range(2)))
    print(json.dumps({"stage": "concurrent_long_comments", "scores": scores, **memory()}), flush=True)
    await check_http()


async def check_http():
    """Run the actual HTTP route and models, replacing only external I/O."""
    async def fake_db():
        yield None

    comments = [{"text": "Bu video çok güzel olmuş."} for _ in range(40)]
    app.dependency_overrides[get_db] = fake_db
    try:
        with (
            patch("app.apiv1.api.get_video", new=AsyncMock(return_value=None)),
            patch("app.apiv1.api.get_video_details", new=AsyncMock(return_value={
                "video_id": "dQw4w9WgXcQ", "title": "Bir test videosu", "channel_id": "test",
            })),
            patch("app.apiv1.api.get_video_comments", new=AsyncMock(return_value=comments)),
            patch("app.apiv1.api.create_video", new=AsyncMock()),
            patch("app.apiv1.api.create_comments", new=AsyncMock()),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/analyze", json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
                assert response.status_code == 200, response.text
                assert response.json()["comments_count_retrieved"] == 40
                assert (await client.get("/health")).status_code == 200
                print(json.dumps({"stage": "http_analyze_40_comments", "status": response.status_code,
                                  "external_io": "mocked", **memory()}), flush=True)
    finally:
        app.dependency_overrides.pop(get_db, None)


if __name__ == "__main__":
    asyncio.run(main())
