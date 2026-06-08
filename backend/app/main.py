# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_driver, close_driver
from app.routers import courses, graph, users

app = FastAPI(title="Topic-to-Course")

# Include routers
# app.include_router(users.router)
# app.include_router(courses.router)
app.include_router(graph.router)

# CORS (important for Vite frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default ports
    allow_credentials=True, #change to True if you need to send cookies or auth headers
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