from fastapi import APIRouter, Depends
from app.core.database import get_driver
from app.repositories.course_repo import CourseRepository

#Defines endpoint with prefix /courses.  
router = APIRouter(prefix="/courses", tags=["courses"])

#Get all courses for a user, including their modules
# @router.post("/get_user_courses")



# @router.post("/create")