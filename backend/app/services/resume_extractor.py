import re
from typing import Dict, List

from app.schemas.resume import EducationItem, ProjectItem, ResumeProfile
from app.services.ai_client import AIClient


SKILL_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "FastAPI",
    "Flask", "Django", "Spring", "Node.js", "MySQL", "PostgreSQL", "Redis",
    "MongoDB", "Docker", "Kubernetes", "Linux", "Git", "Serverless", "AWS",
    "阿里云", "腾讯云", "机器学习", "深度学习", "NLP", "LLM", "数据分析",
]


def extract_resume_profile(text: str) -> ResumeProfile:
    ai_data = AIClient().extract_resume_profile(text)
    if ai_data:
        return _profile_from_ai(ai_data, text)
    return _profile_from_rules(text)


def _profile_from_ai(data: Dict, text: str) -> ResumeProfile:
    fallback = _profile_from_rules(text)
    education = [
        EducationItem(**item) for item in data.get("education", []) if isinstance(item, dict)
    ]
    projects = [
        ProjectItem(**item) for item in data.get("projects", []) if isinstance(item, dict)
    ]
    return ResumeProfile(
        name=data.get("name") or fallback.name,
        phone=data.get("phone") or fallback.phone,
        email=data.get("email") or fallback.email,
        address=data.get("address") or fallback.address,
        job_intention=data.get("job_intention") or fallback.job_intention,
        expected_salary=data.get("expected_salary") or fallback.expected_salary,
        years_of_experience=data.get("years_of_experience") or fallback.years_of_experience,
        education=education or fallback.education,
        projects=projects or fallback.projects,
        skills=_dedupe([*data.get("skills", []), *fallback.skills]),
    )


def _profile_from_rules(text: str) -> ResumeProfile:
    phone = _first_match(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)", text)
    email = _first_match(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    name = _guess_name(text)
    address = _guess_address(text)
    years = _first_match(r"(\d{1,2}\s*年(?:以上)?(?:工作)?经验)", text)
    expected_salary = _first_match(r"(\d{1,3}\s*[kK万]\s*[-~至]\s*\d{1,3}\s*[kK万]|\d{1,3}\s*[kK万]/?月)", text)
    job_intention = _first_match(r"(?:求职意向|应聘岗位|目标岗位)[:：\s]*([^\n]{2,40})", text)

    return ResumeProfile(
        name=name,
        phone=phone,
        email=email,
        address=address,
        job_intention=job_intention,
        expected_salary=expected_salary,
        years_of_experience=years,
        education=_extract_education(text),
        projects=_extract_projects(text),
        skills=_extract_skills(text),
    )


def _first_match(pattern: str, text: str):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return (match.group(1) if match.lastindex else match.group(0)).strip()


def _guess_name(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:8]:
        clean = re.sub(r"[\s:：]", "", line)
        if 2 <= len(clean) <= 6 and re.fullmatch(r"[\u4e00-\u9fa5A-Za-z]+", clean):
            if clean not in {"个人简历", "简历", "Resume"}:
                return clean
    return None


def _guess_address(text: str):
    match = re.search(r"(?:地址|现居|所在地|城市)[:：\s]*([^\n]{2,40})", text)
    return match.group(1).strip() if match else None


def _extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    result = []
    for skill in SKILL_KEYWORDS:
        if skill.lower() in lowered:
            result.append(skill)
    return _dedupe(result)


def _extract_education(text: str) -> List[EducationItem]:
    degrees = ["博士", "硕士", "研究生", "本科", "大专", "学士"]
    items = []
    for line in text.splitlines():
        if any(degree in line for degree in degrees):
            items.append(EducationItem(degree=next((d for d in degrees if d in line), None), school=line[:80]))
            if len(items) >= 3:
                break
    return items


def _extract_projects(text: str) -> List[ProjectItem]:
    projects = []
    capture = False
    for line in text.splitlines():
        if any(key in line for key in ["项目经历", "项目经验", "Project"]):
            capture = True
            continue
        if capture and line:
            projects.append(ProjectItem(name=line[:50], description=line[:160], technologies=_extract_skills(line)))
            if len(projects) >= 5:
                break
    return projects


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if not item:
            continue
        key = str(item).lower()
        if key not in seen:
            seen.add(key)
            output.append(str(item))
    return output
