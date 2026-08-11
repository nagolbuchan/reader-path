from typing import Dict, List, Optional

from app.models.course import CourseCreateRequest
from app.repositories.course_repo import CourseRepository
from app.repositories.user_repo import UserRepository


class CourseService:
    def __init__(self, course_repo: CourseRepository, user_repo: UserRepository):
        self.course_repo = course_repo
        self.user_repo = user_repo

    async def create_course(
        self, user_id: str, payload: CourseCreateRequest
    ) -> Dict:
        user = await self.user_repo.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        course = await self.course_repo.create_full_course(user_id, payload)
        if not course:
            raise ValueError("Failed to create course")
        return course

    async def get_user_courses(self, user_id: str) -> List[Dict]:
        user = await self.user_repo.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        return await self.course_repo.get_user_courses(user_id)

    async def get_course(self, course_id: str) -> Optional[Dict]:
        return await self.course_repo.get_course(course_id)
