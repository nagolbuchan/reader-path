from typing import Any, Dict, List, Optional
import re
import uuid

from app.models.course import BookReading, CourseCreateRequest
from app.repositories.base_repo import BaseRepository


def _normalize_topic_name(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", (text or "").strip())
    return collapsed.lower() or "topic"


def _book_catalog_key(book: BookReading, book_id: str) -> str:
    if book.isbn13:
        return f"isbn:{book.isbn13}"
    if book.google_books_id:
        return f"gb:{book.google_books_id}"
    if book.open_library_id:
        return f"ol:{book.open_library_id}"
    if book.loc_control_number:
        return f"loc:{book.loc_control_number}"
    return f"book:{book_id}"


def _book_sources(book: BookReading) -> List[str]:
    sources: List[str] = []
    if book.google_books_id:
        sources.append("google_books")
    if book.open_library_id:
        sources.append("open_library")
    if book.loc_control_number:
        sources.append("library_of_congress")
    if book.gutenberg_url:
        sources.append("gutenberg")
    return sources


def _author_names(authors: Optional[str]) -> List[str]:
    names = [
        a.strip()
        for a in (authors or "Unknown Author").split(",")
        if a.strip()
    ]
    return names or ["Unknown Author"]


def _book_payload(book: BookReading) -> Dict[str, Any]:
    book_id = str(uuid.uuid4())
    return {
        "bookId": book_id,
        "catalogKey": _book_catalog_key(book, book_id),
        "title": book.title,
        "description": book.summary or "",
        "isbn13": book.isbn13,
        "googleBooksId": book.google_books_id,
        "openLibraryId": book.open_library_id,
        "locControlNumber": book.loc_control_number,
        "gutenbergUrl": book.gutenberg_url,
        "firstPublicationYear": book.published_year,
        "coverUrl": book.link,
        "sources": _book_sources(book),
        "authors": _author_names(book.authors),
    }


class CourseRepository(BaseRepository):
    async def create_full_course(
        self, user_id: str, course: CourseCreateRequest
    ) -> Optional[Dict[str, Any]]:
        """Persist course, modules, books, authors, assignments, and topic in one write."""
        course_id = str(uuid.uuid4())
        topic_name = course.topic.strip()
        topic_normalized = _normalize_topic_name(topic_name)
        learning_objectives: List[str] = []

        modules_payload: List[Dict[str, Any]] = []
        for idx, mod in enumerate(course.modules):
            learning_objectives.extend(mod.learning_objectives or [])
            readings = [_book_payload(book) for book in mod.assigned_readings]
            assignments = []
            for a_idx, assignment in enumerate(mod.assignments):
                assignments.append(
                    {
                        "assignmentId": str(uuid.uuid4()),
                        "title": assignment.assignment_title,
                        "description": assignment.description,
                        "type": "other",
                        "order": a_idx,
                    }
                )
            modules_payload.append(
                {
                    "moduleId": str(uuid.uuid4()),
                    "title": mod.module_title,
                    "description": " ".join(mod.learning_objectives or []) or None,
                    "order": idx,
                    "isPrimarySourcesOnly": bool(mod.is_primary_sources_only),
                    "isLegacyModule": bool(mod.is_legacy_module),
                    "readings": readings,
                    "assignments": assignments,
                }
            )

        spares = [_book_payload(book) for book in (course.replacement_pool or [])]

        query = """
        MATCH (u:User {userId: $user_id})
        MERGE (t:Topic {name: $topic_normalized})
        ON CREATE SET
            t.topicId = randomUUID(),
            t.createdAt = datetime(),
            t.source = 'user_topic'
        CREATE (c:Course {
            courseId: $course_id,
            title: $title,
            description: $description,
            difficulty: 'intermediate',
            status: 'published',
            createdBy: $user_id,
            createdAt: datetime(),
            learningObjectives: $learning_objectives,
            category: $category
        })
        CREATE (u)-[:CREATED]->(c)
        CREATE (c)-[:ABOUT]->(t)
        WITH c, t
        FOREACH (mod IN $modules |
            CREATE (m:Module {
                moduleId: mod.moduleId,
                title: mod.title,
                description: mod.description,
                order: mod.order,
                estimatedHours: null,
                isPrimarySourcesOnly: mod.isPrimarySourcesOnly,
                isLegacyModule: mod.isLegacyModule,
                createdAt: datetime()
            })
            CREATE (c)-[:HAS_MODULE]->(m)
            FOREACH (reading IN mod.readings |
                MERGE (b:Book {catalogKey: reading.catalogKey})
                ON CREATE SET
                    b.bookId = reading.bookId,
                    b.title = reading.title,
                    b.description = reading.description,
                    b.isbn13 = reading.isbn13,
                    b.googleBooksId = reading.googleBooksId,
                    b.openLibraryId = reading.openLibraryId,
                    b.locControlNumber = reading.locControlNumber,
                    b.gutenbergUrl = reading.gutenbergUrl,
                    b.firstPublicationYear = reading.firstPublicationYear,
                    b.coverUrl = reading.coverUrl,
                    b.sources = reading.sources,
                    b.createdAt = datetime(),
                    b.lastVerifiedAt = datetime()
                ON MATCH SET
                    b.isbn13 = coalesce(b.isbn13, reading.isbn13),
                    b.googleBooksId = coalesce(b.googleBooksId, reading.googleBooksId),
                    b.openLibraryId = coalesce(b.openLibraryId, reading.openLibraryId),
                    b.locControlNumber = coalesce(b.locControlNumber, reading.locControlNumber),
                    b.gutenbergUrl = coalesce(b.gutenbergUrl, reading.gutenbergUrl),
                    b.firstPublicationYear = coalesce(b.firstPublicationYear, reading.firstPublicationYear),
                    b.coverUrl = coalesce(b.coverUrl, reading.coverUrl),
                    b.description = coalesce(nullif(b.description, ''), reading.description),
                    b.sources = reduce(
                        acc = coalesce(b.sources, []),
                        src IN coalesce(reading.sources, []) |
                        CASE WHEN src IN acc THEN acc ELSE acc + src END
                    ),
                    b.lastVerifiedAt = datetime()
                CREATE (m)-[:ASSIGNS_READING]->(b)
                MERGE (b)-[:RELATED_TO]->(t)
                FOREACH (authorName IN reading.authors |
                    MERGE (a:Author {name: authorName})
                    ON CREATE SET
                        a.authorId = randomUUID(),
                        a.sortName = authorName
                    MERGE (b)-[:WRITTEN_BY]->(a)
                )
            )
            FOREACH (asg IN mod.assignments |
                CREATE (asgn:Assignment {
                    assignmentId: asg.assignmentId,
                    title: asg.title,
                    description: asg.description,
                    type: asg.type,
                    order: asg.order,
                    rubric: null,
                    createdAt: datetime()
                })
                CREATE (m)-[:HAS_ASSIGNMENT]->(asgn)
            )
        )
        FOREACH (reading IN $spares |
            MERGE (b:Book {catalogKey: reading.catalogKey})
            ON CREATE SET
                b.bookId = reading.bookId,
                b.title = reading.title,
                b.description = reading.description,
                b.isbn13 = reading.isbn13,
                b.googleBooksId = reading.googleBooksId,
                b.openLibraryId = reading.openLibraryId,
                b.locControlNumber = reading.locControlNumber,
                b.gutenbergUrl = reading.gutenbergUrl,
                b.firstPublicationYear = reading.firstPublicationYear,
                b.coverUrl = reading.coverUrl,
                b.sources = reading.sources,
                b.createdAt = datetime(),
                b.lastVerifiedAt = datetime()
            ON MATCH SET
                b.isbn13 = coalesce(b.isbn13, reading.isbn13),
                b.googleBooksId = coalesce(b.googleBooksId, reading.googleBooksId),
                b.openLibraryId = coalesce(b.openLibraryId, reading.openLibraryId),
                b.locControlNumber = coalesce(b.locControlNumber, reading.locControlNumber),
                b.gutenbergUrl = coalesce(b.gutenbergUrl, reading.gutenbergUrl),
                b.firstPublicationYear = coalesce(b.firstPublicationYear, reading.firstPublicationYear),
                b.coverUrl = coalesce(b.coverUrl, reading.coverUrl),
                b.description = coalesce(nullif(b.description, ''), reading.description),
                b.sources = reduce(
                    acc = coalesce(b.sources, []),
                    src IN coalesce(reading.sources, []) |
                    CASE WHEN src IN acc THEN acc ELSE acc + src END
                ),
                b.lastVerifiedAt = datetime()
            MERGE (c)-[:HAS_SPARE]->(b)
            MERGE (b)-[:RELATED_TO]->(t)
            FOREACH (authorName IN reading.authors |
                MERGE (a:Author {name: authorName})
                ON CREATE SET
                    a.authorId = randomUUID(),
                    a.sortName = authorName
                MERGE (b)-[:WRITTEN_BY]->(a)
            )
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
                "topic_normalized": topic_normalized,
                "learning_objectives": learning_objectives,
                "category": course.category,
                "modules": modules_payload,
                "spares": spares,
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
        ORDER BY c.createdAt DESC
        """
        result = await self.execute_query(query, {"user_id": user_id})
        return [record["c"] for record in result]

    async def get_course(self, course_id: str) -> Optional[Dict]:
        query = """
        MATCH (c:Course {courseId: $course_id})
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
        MATCH (u:User {userId: $user_id})-[:CREATED]->(c:Course {courseId: $course_id})
        RETURN c
        """
        result = await self.execute_query(
            query, {"course_id": course_id, "user_id": user_id}
        )
        return result[0]["c"] if result else None

    async def delete_course_and_modules(self, course_id: str) -> bool:
        query = """
        MATCH (c:Course {courseId: $course_id})
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        OPTIONAL MATCH (m)-[:HAS_ASSIGNMENT]->(a:Assignment)
        DETACH DELETE a, m, c
        RETURN true AS ok
        """
        result = await self.execute_query(query, {"course_id": course_id})
        return bool(result)
