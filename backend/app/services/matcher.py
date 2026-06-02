import re
from typing import Any, Dict, List, Tuple

from app.schemas.resume import (
    MissingSkill,
    RadarScore,
    RequirementMatch,
    ResumeMatchResponse,
    ResumeParseResponse,
)
from app.services.ai_client import AIClient
from app.services.resume_extractor import SKILL_KEYWORDS


DIMENSION_WEIGHTS = {
    "skill_match": 0.35,
    "experience_relevance": 0.25,
    "project_relevance": 0.20,
    "education_fit": 0.10,
    "keyword_coverage": 0.10,
}


def match_resume_to_job(resume: ResumeParseResponse, job_description: str) -> ResumeMatchResponse:
    rule_result = _rule_based_match(resume, job_description)
    ai_result = AIClient().score_match(resume.cleaned_text, job_description)

    if ai_result:
        return _build_ai_enhanced_response(resume.resume_id, rule_result, ai_result)
    return _build_rule_response(resume.resume_id, rule_result)


def extract_job_keywords(job_description: str) -> List[str]:
    lowered = job_description.lower()
    hits = [skill for skill in SKILL_KEYWORDS if skill.lower() in lowered]
    words = re.findall(r"[A-Za-z][A-Za-z0-9.+#-]{1,30}", job_description)
    technical_words = [
        word
        for word in words
        if len(word) >= 3 and word.lower() not in {"and", "the", "with", "for", "our", "you"}
    ]
    return _dedupe([*hits, *technical_words])[:30]


def _rule_based_match(resume: ResumeParseResponse, job_description: str) -> Dict[str, Any]:
    job_keywords = extract_job_keywords(job_description)
    resume_keywords = set(skill.lower() for skill in resume.profile.skills)
    matched, missing = _split_keywords(job_keywords, resume_keywords)

    keyword_rate = len(matched) / len(job_keywords) if job_keywords else 0.0
    skill_score = round(keyword_rate * 100)
    experience_score = _score_experience(resume.cleaned_text, job_description)
    education_score = _score_education(resume.cleaned_text, job_description)
    project_score = _score_project(resume.cleaned_text, job_description)
    keyword_score = skill_score
    dimensions = {
        "skill_match": skill_score,
        "experience_relevance": experience_score,
        "education_fit": education_score,
        "project_relevance": project_score,
        "keyword_coverage": keyword_score,
    }

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "keyword_match_rate": round(keyword_rate, 2),
        "dimension_scores": dimensions,
        "summary": _rule_summary(_weighted_score(dimensions), matched, missing),
    }


def _build_ai_enhanced_response(
    resume_id: str,
    rule_result: Dict[str, Any],
    ai_result: Dict[str, Any],
) -> ResumeMatchResponse:
    ai_dimensions = _safe_dimensions(ai_result.get("dimension_scores") or ai_result)
    rule_dimensions = rule_result["dimension_scores"]

    # Hybrid score: rules keep the result repeatable, AI supplies semantic judgment.
    dimensions = {
        key: round(rule_dimensions[key] * 0.4 + ai_dimensions.get(key, rule_dimensions[key]) * 0.6)
        for key in DIMENSION_WEIGHTS
    }

    semantic_matches = _parse_requirement_matches(ai_result.get("requirement_matches", []))
    missing_details = _parse_missing_skills(ai_result.get("missing_skills", []))

    ai_matched = [str(item) for item in ai_result.get("matched_keywords", []) if item]
    matched_keywords = _dedupe([*rule_result["matched_keywords"], *ai_matched])
    missing_keywords = _missing_names(missing_details) or rule_result["missing_keywords"]
    keyword_rate = _semantic_coverage(semantic_matches, rule_result["keyword_match_rate"])
    score = _weighted_score(dimensions)

    return ResumeMatchResponse(
        resume_id=resume_id,
        analysis_mode="ai_enhanced",
        score=score,
        keyword_match_rate=keyword_rate,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        semantic_matches=semantic_matches,
        missing_skill_details=missing_details,
        radar_scores=_radar_scores(dimensions),
        dimension_scores=dimensions,
        experience_relevance=_label_score(dimensions["experience_relevance"]),
        ai_summary=ai_result.get("summary") or rule_result["summary"],
    )


def _build_rule_response(resume_id: str, rule_result: Dict[str, Any]) -> ResumeMatchResponse:
    dimensions = rule_result["dimension_scores"]
    score = _weighted_score(dimensions)
    missing_details = [
        MissingSkill(skill=item, normalized_skill=item, importance="medium", reason="规则匹配未在简历技能中发现该关键词")
        for item in rule_result["missing_keywords"]
    ]
    return ResumeMatchResponse(
        resume_id=resume_id,
        analysis_mode="rule_based",
        score=score,
        keyword_match_rate=rule_result["keyword_match_rate"],
        matched_keywords=rule_result["matched_keywords"],
        missing_keywords=rule_result["missing_keywords"],
        semantic_matches=[],
        missing_skill_details=missing_details,
        radar_scores=_radar_scores(dimensions),
        dimension_scores=dimensions,
        experience_relevance=_label_score(dimensions["experience_relevance"]),
        ai_summary=rule_result["summary"],
    )


def _safe_dimensions(data: Dict[str, Any]) -> Dict[str, int]:
    return {
        key: _bounded_int(data.get(key), 0)
        for key in DIMENSION_WEIGHTS
        if data.get(key) is not None
    }


def _parse_requirement_matches(items: Any) -> List[RequirementMatch]:
    if not isinstance(items, list):
        return []
    output = []
    for item in items[:20]:
        if not isinstance(item, dict) or not item.get("requirement"):
            continue
        level = item.get("match_level") if item.get("match_level") in {"strong", "partial", "weak", "none"} else "none"
        importance = item.get("importance") if item.get("importance") in {"high", "medium", "low"} else "medium"
        output.append(
            RequirementMatch(
                requirement=str(item.get("requirement")),
                normalized_skill=_optional_str(item.get("normalized_skill")),
                matched=bool(item.get("matched")),
                match_level=level,
                score=_bounded_int(item.get("score"), 0),
                importance=importance,
                evidence=_optional_str(item.get("evidence")),
                reason=_optional_str(item.get("reason")),
            )
        )
    return output


def _parse_missing_skills(items: Any) -> List[MissingSkill]:
    if not isinstance(items, list):
        return []
    output = []
    for item in items[:20]:
        if isinstance(item, str):
            output.append(MissingSkill(skill=item, normalized_skill=item, importance="medium"))
            continue
        if not isinstance(item, dict) or not item.get("skill"):
            continue
        importance = item.get("importance") if item.get("importance") in {"high", "medium", "low"} else "medium"
        output.append(
            MissingSkill(
                skill=str(item.get("skill")),
                normalized_skill=_optional_str(item.get("normalized_skill")),
                importance=importance,
                reason=_optional_str(item.get("reason")),
            )
        )
    return output


def _split_keywords(job_keywords: List[str], resume_keywords: set) -> Tuple[List[str], List[str]]:
    matched = []
    missing = []
    for keyword in job_keywords:
        if keyword.lower() in resume_keywords:
            matched.append(keyword)
        else:
            missing.append(keyword)
    return matched, missing


def _score_experience(resume_text: str, job_description: str) -> int:
    resume_year = _extract_year(resume_text)
    required_year = _extract_year(job_description)
    if required_year == 0:
        return 70 if resume_year else 55
    if resume_year >= required_year:
        return 90
    if resume_year and resume_year >= max(required_year - 2, 1):
        return 70
    return 45


def _score_education(resume_text: str, job_description: str) -> int:
    levels = ["博士", "硕士", "研究生", "本科", "大专"]
    if not any(level in job_description for level in levels):
        return 70
    for level in levels:
        if level in job_description and level in resume_text:
            return 88
    return 50


def _score_project(resume_text: str, job_description: str) -> int:
    shared = 0
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    for skill in SKILL_KEYWORDS:
        if skill.lower() in resume_lower and skill.lower() in jd_lower:
            shared += 1
    if "项目" in resume_text and shared >= 3:
        return 88
    if "项目" in resume_text:
        return 70
    return 50


def _extract_year(text: str) -> int:
    matches = re.findall(r"(\d{1,2})\s*年", text)
    return max([int(item) for item in matches], default=0)


def _weighted_score(dimensions: Dict[str, int]) -> int:
    return round(sum(dimensions[key] * weight for key, weight in DIMENSION_WEIGHTS.items()))


def _radar_scores(dimensions: Dict[str, int]) -> List[RadarScore]:
    return [
        RadarScore(label="技能匹配", value=dimensions["skill_match"]),
        RadarScore(label="经验相关", value=dimensions["experience_relevance"]),
        RadarScore(label="学历匹配", value=dimensions["education_fit"]),
        RadarScore(label="项目相关", value=dimensions["project_relevance"]),
        RadarScore(label="关键词覆盖", value=dimensions["keyword_coverage"]),
    ]


def _semantic_coverage(matches: List[RequirementMatch], fallback: float) -> float:
    if not matches:
        return fallback
    covered = sum(1 for item in matches if item.match_level in {"strong", "partial"})
    return round(covered / len(matches), 2)


def _missing_names(missing_details: List[MissingSkill]) -> List[str]:
    return _dedupe([item.normalized_skill or item.skill for item in missing_details])


def _bounded_int(value: Any, fallback: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except Exception:
        return fallback


def _optional_str(value: Any):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _label_score(score: int) -> str:
    if score >= 80:
        return "高"
    if score >= 60:
        return "中"
    return "低"


def _rule_summary(score: int, matched: List[str], missing: List[str]) -> str:
    if score >= 80:
        tone = "候选人与岗位要求整体匹配度较高"
    elif score >= 60:
        tone = "候选人与岗位要求存在一定匹配，但仍有补充验证空间"
    else:
        tone = "候选人与岗位要求匹配度偏低，建议重点核验核心技能"
    return f"{tone}。已匹配关键词：{', '.join(matched[:8]) or '暂无'}；缺失技能：{', '.join(missing[:8]) or '暂无'}。"


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output
