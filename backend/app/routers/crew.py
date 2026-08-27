from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.models.course import CoursePreview
from app.services.crew_run_log import read_run_log
from app.services.google_books import GoogleBooksError
from app.services.job_store import job_store
from app.services.search_service import CourseGenerationService

router = APIRouter(prefix="/crew", tags=["crew"])


class CrewJobCreate(BaseModel):
    topic: str = Field(min_length=1)


async def _run_generation_job(job_id: str, topic: str) -> None:
    job_store.set_status(job_id, "running")

    def on_progress(key: str, _label: str = "") -> None:
        job_store.activate_step(job_id, key)

    try:
        course_service = CourseGenerationService()
        course: CoursePreview = await course_service.generate_course_from_topic(
            topic, on_progress=on_progress, run_id=job_id
        )
        job_store.complete(job_id, course.model_dump())
    except (GoogleBooksError, ValueError) as exc:
        job_store.fail(job_id, str(exc))
    except Exception as exc:
        print("Error occurred while generating course:", str(exc))
        job_store.fail(job_id, str(exc) or "Course generation failed")


@router.post("/jobs")
async def create_crew_job(
    body: CrewJobCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")

    job = job_store.create(user_id=current_user["user_id"], topic=topic)
    background_tasks.add_task(_run_generation_job, job.job_id, topic)
    return {"job_id": job.job_id, "status": job.status}


@router.get("/jobs/{job_id}")
async def get_crew_job(job_id: str, current_user=Depends(get_current_user)):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    return job.to_dict()


@router.get("/jobs/{job_id}/log")
async def get_crew_job_log(job_id: str, current_user=Depends(get_current_user)):
    """Return the full agent run log (verbose trace + course JSON)."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    log = read_run_log(job_id)
    if not log:
        raise HTTPException(status_code=404, detail="Run log not found yet")

    return JSONResponse(content=log)


@router.get("/kickoff", response_model=dict)
async def kickoff_crew(
    topic: str,
    current_user=Depends(get_current_user),
):
    """
    Synchronous course generation (legacy). Prefer POST /crew/jobs for progress UI.
    """
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    try:
        course_service = CourseGenerationService()
        course: CoursePreview = await course_service.generate_course_from_topic(
            topic.strip()
        )
        return {
            "status": "success",
            "data": course.model_dump(),
            "user_id": current_user["user_id"],
        }
    except (GoogleBooksError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        print("Error occurred while generating course:", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
