from fastapi import HTTPException

from app.schemas.resume import JobSource


def resolve_job_description(job_source: JobSource) -> str:
    if job_source.source_type == "text":
        return job_source.content.strip()

    if job_source.source_type == "url":
        raise HTTPException(
            status_code=501,
            detail="URL job description parsing is reserved for future implementation.",
        )

    raise HTTPException(status_code=400, detail="Unsupported job source type.")
