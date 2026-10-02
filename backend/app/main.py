import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import joblib
from app.apiv1.api import router
from app.core.config import settings
from app.limiter import limiter
from app.render.ping import self_ping
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads classifier model to memory"""
    PATH =Path(__file__).parent
    MODEL_PATH = PATH / "services" / "local_model" / "v1" / "model_v1.joblib"
    app.state.title_analyze_model = joblib.load(MODEL_PATH)
    ping_task = asyncio.create_task(self_ping())

    try:
        yield
    finally:
        ping_task.cancel()
        with suppress(asyncio.CancelledError):
            await ping_task

        app.state.title_analyze_model = None

app = FastAPI(lifespan=lifespan, title="Clickbait Analyzer API", version="1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore
app.include_router(router)
