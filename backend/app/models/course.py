from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.topic_classifier import TopicCategory


class BookReading(BaseModel):
    title: str
    authors: str = "Unknown Author"
    link: Optional[str] = None
    summary: Optional[str] = None
    google_books_id: Optional[str] = None
    open_library_id: Optional[str] = None
    isbn13: Optional[str] = None
    gutenberg_url: Optional[str] = None


class AssignmentItem(BaseModel):
    assignment_title: str
    description: str


class ModuleItem(BaseModel):
    module_title: str
    learning_objectives: List[str] = Field(default_factory=list)
    assigned_readings: List[BookReading] = Field(min_length=4)
    assignments: List[AssignmentItem] = Field(default_factory=list)
    is_primary_sources_only: bool = False
    is_legacy_module: bool = False


class CoursePreview(BaseModel):
    title: str
    description: str = ""
    topic: Optional[str] = None
    category: Optional[TopicCategory] = None
    modules: List[ModuleItem] = Field(default_factory=list)


class CourseCreateRequest(BaseModel):
    title: str
    description: str = ""
    topic: str
    category: Optional[TopicCategory] = None
    modules: List[ModuleItem] = Field(default_factory=list)


class CourseResponse(BaseModel):
    course_id: str
    title: str
    description: str = ""
    topic: str = ""
