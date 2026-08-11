from typing import List, Optional
from pydantic import BaseModel, Field


class BookReading(BaseModel):
    title: str
    authors: str = "Unknown Author"
    link: Optional[str] = None
    summary: Optional[str] = None


class AssignmentItem(BaseModel):
    assignment_title: str
    description: str


class ModuleItem(BaseModel):
    module_title: str
    learning_objectives: List[str] = Field(default_factory=list)
    assigned_readings: List[BookReading] = Field(default_factory=list)
    assignments: List[AssignmentItem] = Field(default_factory=list)


class CoursePreview(BaseModel):
    title: str
    description: str = ""
    topic: Optional[str] = None
    modules: List[ModuleItem] = Field(default_factory=list)


class CourseCreateRequest(BaseModel):
    title: str
    description: str = ""
    topic: str
    modules: List[ModuleItem] = Field(default_factory=list)


class CourseResponse(BaseModel):
    course_id: str
    title: str
    description: str = ""
    topic: str = ""
