from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.models.course import CoursePreview
from app.services.search_service import CourseGenerationService

router = APIRouter(prefix="/crew", tags=["crew"])


@router.get("/kickoff", response_model=dict)
async def kickoff_crew(
    topic: str,
    current_user=Depends(get_current_user),
):
    """
    Generate a course preview for the given topic.
    Requires authentication so saved courses always have an owner.
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
    except Exception as e:
        print("Error occurred while generating course:", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
