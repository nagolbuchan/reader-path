from typing import Any, Dict, List, Optional
import re
import uuid

from app.models.course import CourseCreateRequest, CoursePreview
from app.repositories.base_repo import BaseRepository


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "topic"


class CourseRepository(BaseRepository):
    async def create_full_course(
        self, user_id: str, course: CourseCreateRequest
    ) -> Optional[Dict[str, Any]]:
        """Persist course, modules, books, authors, assignments, and topic in one write."""
        course_id = str(uuid.uuid4())
        topic_name = course.topic.strip()
        topic_slug = _slugify(topic_name)

        modules_payload: List[Dict[str, Any]] = []
        for idx, mod in enumerate(course.modules):
            module_id = str(uuid.uuid4())
            readings = []
            for book in mod.assigned_readings:
                authors = [
                    a.strip()
                    for a in (book.authors or "Unknown Author").split(",")
                    if a.strip()
                ] or ["Unknown Author"]
                readings.append(
                    {
                        "book_id": str(uuid.uuid4()),
                        "title": book.title,
                        "link": book.link or "",
                        "summary": book.summary or "",
                        "authors": authors,
                    }
                )
            assignments = []
            for a_idx, assignment in enumerate(mod.assignments):
                assignments.append(
                    {
                        "assignment_id": str(uuid.uuid4()),
                        "title": assignment.assignment_title,
                        "description": assignment.description,
                        "order": a_idx,
                    }
                )
            modules_payload.append(
                {
                    "module_id": module_id,
                    "title": mod.module_title,
                    "order": idx,
                    "learning_objectives": mod.learning_objectives,
                    "readings": readings,
                    "assignments": assignments,
                }
            )

        query = """
        MATCH (u:User {userId: $user_id})
        MERGE (t:Topic {slug: $topic_slug})
        ON CREATE SET t.name = $topic_name
        ON MATCH SET t.name = coalesce(t.name, $topic_name)
        CREATE (c:Course {
            course_id: $course_id,
            title: $title,
            description: $description,
            topic: $topic_name,
            created_at: datetime()
        })
        CREATE (u)-[:CREATED]->(c)
        CREATE (c)-[:ABOUT]->(t)
        WITH c, t
        UNWIND $modules AS mod
        CREATE (m:Module {
            module_id: mod.module_id,
            title: mod.title,
            order: mod.order,
            learning_objectives: mod.learning_objectives,
            created_at: datetime()
        })
        CREATE (c)-[:HAS_MODULE]->(m)
        WITH m, t, mod
        FOREACH (reading IN mod.readings |
            MERGE (b:Book {title: reading.title, link: reading.link})
            ON CREATE SET
                b.book_id = reading.book_id,
                b.summary = reading.summary,
                b.created_at = datetime()
            ON MATCH SET
                b.summary = coalesce(nullif(reading.summary, ''), b.summary)
            CREATE (m)-[:ASSIGNS_READING]->(b)
            MERGE (b)-[:RELATED_TO]->(t)
            FOREACH (author_name IN reading.authors |
                MERGE (a:Author {name: author_name})
                MERGE (b)-[:WRITTEN_BY]->(a)
            )
        )
        FOREACH (asg IN mod.assignments |
            CREATE (asgn:Assignment {
                assignment_id: asg.assignment_id,
                title: asg.title,
                description: asg.description,
                order: asg.order,
                created_at: datetime()
            })
            CREATE (m)-[:HAS_ASSIGNMENT]->(asgn)
        )
        RETURN $course_id AS course_id, $title AS title, $description AS description, $topic_name AS topic
        """

        result = await self.execute_query(
            query,
            {
                "user_id": user_id,
                "course_id": course_id,
                "title": course.title,
                "description": course.description,
                "topic_name": topic_name,
                "topic_slug": topic_slug,
                "modules": modules_payload,
            },
        )
        if not result:
            return None
        row = result[0]
        return {
            "course_id": row["course_id"],
            "title": row["title"],
            "description": row["description"],
            "topic": row["topic"],
        }

    async def get_user_courses(self, user_id: str) -> List[Dict]:
        query = """
        MATCH (u:User {userId: $user_id})-[:CREATED]->(c:Course)
        RETURN c
        ORDER BY c.created_at DESC
        """
        result = await self.execute_query(query, {"user_id": user_id})
        return [record["c"] for record in result]

    async def get_course(self, course_id: str) -> Optional[Dict]:
        query = """
        MATCH (c:Course {course_id: $course_id})
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        RETURN c, collect(m) AS modules
        """
        result = await self.execute_query(query, {"course_id": course_id})
        if not result:
            return None
        course_data = dict(result[0]["c"])
        course_data["modules"] = result[0]["modules"]
        return course_data

    async def get_course_owned_by(
        self, course_id: str, user_id: str
    ) -> Optional[Dict]:
        query = """
        MATCH (u:User {userId: $user_id})-[:CREATED]->(c:Course {course_id: $course_id})
        RETURN c
        """
        result = await self.execute_query(
            query, {"course_id": course_id, "user_id": user_id}
        )
        return result[0]["c"] if result else None

    async def delete_course_and_modules(self, course_id: str) -> bool:
        query = """
        MATCH (c:Course {course_id: $course_id})
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        OPTIONAL MATCH (m)-[:HAS_ASSIGNMENT]->(a:Assignment)
        DETACH DELETE a, m, c
        RETURN true AS ok
        """
        result = await self.execute_query(query, {"course_id": course_id})
        return bool(result)
