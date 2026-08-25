"""In-memory crew generation job store with step progress."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

JobStatus = Literal["pending", "running", "complete", "failed"]
StepStatus = Literal["pending", "active", "done", "failed"]

STEP_DEFS = [
    ("classifying_topic", "Classifying topic"),
    ("searching_books", "Searching Google Books"),
    ("building_modules", "Building course modules"),
    ("validating_readings", "Validating readings"),
]


@dataclass
class JobStep:
    key: str
    label: str
    status: StepStatus = "pending"

    def to_dict(self) -> dict:
        return {"key": self.key, "label": self.label, "status": self.status}


@dataclass
class CrewJob:
    job_id: str
    user_id: str
    topic: str
    status: JobStatus = "pending"
    steps: List[JobStep] = field(default_factory=list)
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "topic": self.topic,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, CrewJob] = {}
        self._lock = threading.Lock()

    def create(self, user_id: str, topic: str) -> CrewJob:
        job = CrewJob(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            steps=[JobStep(key=k, label=l) for k, l in STEP_DEFS],
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[CrewJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def set_status(self, job_id: str, status: JobStatus) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = status

    def activate_step(self, job_id: str, key: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for step in job.steps:
                if step.status == "active":
                    step.status = "done"
                if step.key == key:
                    step.status = "active"

    def complete_step(self, job_id: str, key: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for step in job.steps:
                if step.key == key:
                    step.status = "done"

    def fail(self, job_id: str, error: str, step_key: Optional[str] = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = "failed"
            job.error = error
            for step in job.steps:
                if step_key and step.key == step_key:
                    step.status = "failed"
                elif step.status == "active":
                    step.status = "failed"

    def complete(self, job_id: str, result: dict) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = "complete"
            job.result = result
            for step in job.steps:
                if step.status != "done":
                    step.status = "done"


job_store = JobStore()
