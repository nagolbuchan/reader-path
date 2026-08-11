from fastapi import APIRouter, Depends, HTTPException
from neo4j import AsyncDriver

from app.core.database import get_driver
from app.core.security import get_current_user
from app.models.course import CourseCreateRequest, CourseResponse
from app.repositories.course_repo import CourseRepository
from app.repositories.user_repo import UserRepository
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


def get_course_service(driver: AsyncDriver = Depends(get_driver)) -> CourseService:
    return CourseService(CourseRepository(driver), UserRepository(driver))


@router.post("", response_model=CourseResponse)
async def create_course(
    payload: CourseCreateRequest,
    current_user=Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    try:
        course = await service.create_course(current_user["user_id"], payload)
        return CourseResponse(**course)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
async def list_my_courses(
    current_user=Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    try:
        return await service.get_user_courses(current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{course_id}")
async def get_course(
    course_id: str,
    current_user=Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
