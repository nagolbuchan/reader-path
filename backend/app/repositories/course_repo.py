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
    
    async def get_user_courses(self, user_id: str) -> List[Dict]:
        query = """
        MATCH (u:User {user_id: $user_id})-[:CREATED]->(c:Course)
        RETURN c
        """
        result = await self.execute_query(query, {"user_id": user_id})
        return [record['c'] for record in result]

    async def get_course(self, course_id: str) -> Optional[Dict]:
        query = """
        MATCH (c:Course {course_id: $course_id})
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        RETURN c, collect(m) AS modules
        """
        result = await self.execute_query(query, {"course_id": course_id})

        if not result:
            return None
        
        course_data = result[0]['c']
        course_data['modules'] = result[0]['modules']
        return course_data
    
    async def get_module(self, module_id: str) -> Optional[Dict]:
        query = """
        MATCH (m:Module {module_id: $module_id})
        RETURN m
        """
        result = await self.execute_query(query, {"module_id": module_id})
        return result[0]['m'] if result else None

    async def delete_course_and_modules(self, course_id: str) -> bool:
        query = """
        MATCH (c:Course {course_id: $course_id})
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        DELETE m
        DELETE c
        RETURN true
        """
        result = await self.execute_query(query, {"course_id": course_id})
        return bool(result)