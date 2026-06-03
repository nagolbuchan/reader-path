# What needs to be created when a book is added to the database? 
        #Book node, Topic relationship, Genre relationship, Author relationship, Module relationship(?)

        #Flow: user enters topic; agent searches for books first (checks neo4j; if none, then searches internet)
            #Agent organizes books into course and modules -- shows the user the course and its modules, allowing the user
            #to review and change the course.  After the user approves the course, then data is saved to the database:
                #In the case when a new book is found, the book node is created; it's relationships to topic and genre are created, assuming those exist.
                    #And if the author node exists, then the relationship to the author is created; if not, the process for identifying the author and creating a node
                    #is triggered.  And the book is added to the appropriate module in the course.  

from app.repositories.book_repo import BookRepository
from app.repositories.course_repo import CourseRepository
from app.repositories.user_repo import UserRepository
from typing import List, Dict, Optional

class CourseService:
    def __init__(self, course_repo: CourseRepository, book_repo: BookRepository, user_repo: UserRepository):
        self.course_repo = course_repo
        self.book_repo = book_repo
        self.user_repo = user_repo

    async def create_course(self, user_id: str, topic: str, title: str) -> Dict:
        # Check if user exists
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Create course
        course = await self.course_repo.create_course(user_id, topic, title)
        return course

    async def get_user_courses(self, user_id: str) -> List[Dict]:
        # Check if user exists
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Get courses for user
        courses = await self.course_repo.get_user_courses(user_id)
        return courses

    async def get_course(self, course_id: str) -> Optional[Dict]:
        course = await self.course_repo.get_course(course_id)
        return course