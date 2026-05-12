from app.repositories.base_repo import BaseRepository
from typing import List, Dict, Optional

#Handles course creation, retrieval, deletion, and updates in the Neo4j database
class CourseRepository(BaseRepository):
    
    async def create_course(self, user_id: str, topic: str, title: str) -> Dict:
        query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (c:Course {
                    course_id: randomUUID(),
                    topic: $topic,
                    title: $title,
                    created_at: datetime()})
        CREATE (u)-[:CREATED]->(c)
        RETURN c
        """
        result = await self.execute_query(query, {
            "user_id": user_id,
            "topic": topic,
            "title": title
        })

        return result[0]['c'] if result else None
    
    async def create_module(self, course_id: str, title: str) -> Dict:
        query = """
        MATCH (c:Course {course_id: $course_id})
        CREATE (m:Module {
                    module_id: randomUUID(),
                    title: $title,
                    created_at: datetime()})
        CREATE (c)-[:HAS_MODULE]->(m)
        RETURN m
        """
        result = await self.execute_query(query, {
            "course_id": course_id,
            "title": title
        })

        return result[0]['m'] if result else None