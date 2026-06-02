import re

from app.services.ai_client import AIClient


def extract_job_title(job_description: str) -> str:
    ai_title = _extract_with_ai(job_description)
    if ai_title:
        return ai_title[:80]
    return _extract_with_rules(job_description)


def _extract_with_ai(job_description: str):
    client = AIClient()
    if not client.enabled:
        return None
    result = client._json_completion(
        "请从下面岗位 JD 中提取岗位名称，返回严格 JSON："
        '{"job_title":"岗位名称"}。如果没有明确岗位名称，请概括成最贴近的岗位名。\n\n'
        f"JD:\n{job_description[:4000]}"
    )
    title = result.get("job_title") if result else None
    return str(title).strip() if title else None


def _extract_with_rules(job_description: str) -> str:
    patterns = [
        r"(?:招聘|岗位|职位|诚聘)[:：\s]*([^\n，。；;]{2,40})",
        r"([A-Za-z0-9+\-#\s]{2,30}(?:工程师|开发|专家|经理|实习生))",
        r"([\u4e00-\u9fa5A-Za-z0-9+\-#\s]{2,30}(?:工程师|开发|专家|经理|实习生))",
    ]
    for pattern in patterns:
        match = re.search(pattern, job_description)
        if match:
            return match.group(1).strip()
    return "未命名岗位"
