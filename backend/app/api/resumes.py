from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.schemas.resume import ResumeMatchRequest, ResumeMatchResponse, ResumeParseResponse
from app.schemas.history import MatchHistoryCreate
from app.services.auth import get_current_user
from app.services.cache import Cache
from app.services.history import save_match_history
from app.services.job_title import extract_job_title
from app.services.job_source import resolve_job_description
from app.services.matcher import match_resume_to_job
from app.services.pdf_parser import extract_pdf_text
from app.services.resume_extractor import extract_resume_profile
from app.services.text_cleaner import clean_resume_text
from app.utils.hashing import sha256_text, short_id


router = APIRouter()
cache = Cache()


@router.post("/resumes/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    resume_id = short_id(file_bytes)
    cache_key = f"resume:parse:{resume_id}"
    cached = cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    raw_text = extract_pdf_text(file_bytes)
    if not raw_text:
        raise HTTPException(status_code=400, detail="No text content was extracted from the PDF.")

    cleaned_text = clean_resume_text(raw_text)
    profile = extract_resume_profile(cleaned_text)
    response = ResumeParseResponse(
        resume_id=resume_id,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        profile=profile,
    )
    payload = response.model_dump()
    cache.set(cache_key, payload)
    return response


@router.get("/resumes/{resume_id}", response_model=ResumeParseResponse)
def get_resume(resume_id: str, user=Depends(get_current_user)):
    cached = cache.get(f"resume:parse:{resume_id}")
    if not cached:
        raise HTTPException(status_code=404, detail="Resume not found in cache.")
    cached["cached"] = True
    return cached


@router.post("/resumes/{resume_id}/match", response_model=ResumeMatchResponse)
def match_resume(resume_id: str, request: ResumeMatchRequest, user=Depends(get_current_user)):
    resume_payload = cache.get(f"resume:parse:{resume_id}")
    if not resume_payload:
        raise HTTPException(status_code=404, detail="Resume not found. Please upload and parse it first.")

    job_description = resolve_job_description(request.job_source)
    match_key = f"resume:match:v3:{resume_id}:{sha256_text(job_description)[:16]}"
    cached = cache.get(match_key)
    if cached:
        cached["cached"] = True
        resume = ResumeParseResponse(**resume_payload)
        save_match_history(
            user["id"],
            MatchHistoryCreate(
                resume_id=resume_id,
                candidate_name=resume.profile.name or "未识别",
                contact=_contact(resume),
                job_title=extract_job_title(job_description),
                score=cached["score"],
                analysis_mode=cached.get("analysis_mode", "rule_based"),
                job_description=job_description,
            ),
        )
        return cached

    resume = ResumeParseResponse(**resume_payload)
    response = match_resume_to_job(resume, job_description)
    cache.set(match_key, response.model_dump())
    save_match_history(
        user["id"],
        MatchHistoryCreate(
            resume_id=resume_id,
            candidate_name=resume.profile.name or "未识别",
            contact=_contact(resume),
            job_title=extract_job_title(job_description),
            score=response.score,
            analysis_mode=response.analysis_mode,
            job_description=job_description,
        ),
    )
    return response


def _contact(resume: ResumeParseResponse) -> str:
    contact = " / ".join([item for item in [resume.profile.phone, resume.profile.email] if item])
    return contact or "未识别"
