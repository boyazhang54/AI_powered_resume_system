from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MatchHistoryItem(BaseModel):
    id: int
    resume_id: str
    candidate_name: str
    contact: str
    job_title: str
    score: int
    analysis_mode: str
    created_at: datetime


class MatchHistoryCreate(BaseModel):
    resume_id: str
    candidate_name: str
    contact: str
    job_title: str
    score: int
    analysis_mode: str
    job_description: Optional[str] = None
