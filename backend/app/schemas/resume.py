from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    period: Optional[str] = None


class ProjectItem(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    job_intention: Optional[str] = None
    expected_salary: Optional[str] = None
    years_of_experience: Optional[str] = None
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    resume_id: str
    cached: bool = False
    raw_text: str
    cleaned_text: str
    profile: ResumeProfile


class JobSource(BaseModel):
    source_type: Literal["text", "url"] = "text"
    content: str = Field(min_length=1)


class ResumeMatchRequest(BaseModel):
    job_source: JobSource


class RadarScore(BaseModel):
    label: str
    value: int


class RequirementMatch(BaseModel):
    requirement: str
    normalized_skill: Optional[str] = None
    matched: bool
    match_level: Literal["strong", "partial", "weak", "none"] = "none"
    score: int = Field(ge=0, le=100)
    importance: Literal["high", "medium", "low"] = "medium"
    evidence: Optional[str] = None
    reason: Optional[str] = None


class MissingSkill(BaseModel):
    skill: str
    normalized_skill: Optional[str] = None
    importance: Literal["high", "medium", "low"] = "medium"
    reason: Optional[str] = None


class ResumeMatchResponse(BaseModel):
    resume_id: str
    cached: bool = False
    analysis_mode: Literal["rule_based", "ai_enhanced"] = "rule_based"
    score: int
    keyword_match_rate: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    semantic_matches: List[RequirementMatch] = Field(default_factory=list)
    missing_skill_details: List[MissingSkill] = Field(default_factory=list)
    radar_scores: List[RadarScore]
    dimension_scores: Dict[str, int]
    experience_relevance: str
    ai_summary: str
