import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import init_driver, close_driver
from app.core.stdio_utf8 import configure_utf8_stdio
from app.routers import auth, courses, crew, graph

# Before CrewAI / uvicorn log handlers touch the console.
configure_utf8_stdio()

load_dotenv()

# Ensure CrewAI / tools see keys from Settings
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.GOOGLE_BOOKS_API_KEY:
    os.environ["GOOGLE_BOOKS_API_KEY"] = settings.GOOGLE_BOOKS_API_KEY

app = FastAPI(title="ReaderPath")

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(graph.router)
app.include_router(crew.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_driver()


@app.on_event("shutdown")
async def shutdown_event():
    await close_driver()


@app.get("/")
async def root():
    return {"message": "ReaderPath API is running"}
