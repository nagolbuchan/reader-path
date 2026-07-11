from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from app.services.search_service import CourseGenerationService
# from app.dependencies import get_current_user  # We'll create this soon

router = APIRouter(prefix="/crew", tags=["crew"])

@router.get("/kickoff")
async def kickoff_crew(topic: str):
    """
    Endpoint to initiate the CrewAI agents' search for books related to the topic and generate a course structure.
    """
    print('kickoff_crew called with topic:', topic)
    try:
        course_service = CourseGenerationService()
        result = course_service.generate_course_from_topic(topic)
        print('Generated course data:', result)
        return {"status": "success", "data": result}
    except Exception as e:
        print('Error occurred while generating course:', str(e))
        raise HTTPException(status_code=500, detail=str(e))