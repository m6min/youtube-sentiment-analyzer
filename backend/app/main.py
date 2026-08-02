from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.apiv1.api import router

app = FastAPI(title="Youtube Analyzer API", version="1.0")

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)
