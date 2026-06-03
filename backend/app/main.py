# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_driver, close_driver
from app.routers import courses, graph, users

app = FastAPI(title="Topic-to-Course")

# CORS (important for Vite frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(graph.router)

@app.on_event("startup")
async def startup_event():
    await init_driver()

@app.on_event("shutdown")
async def shutdown_event():
    await close_driver()

@app.get("/")
async def root():
    return {"message": "ReaderPath API is running"}