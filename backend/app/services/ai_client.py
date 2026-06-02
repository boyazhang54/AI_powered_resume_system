import json
import logging
import re
from typing import Any, Dict, Optional

from app.config import get_settings


logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.ai_api_key)

    def extract_resume_profile(self, resume_text: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        prompt = (
            "Extract resume information as strict JSON. Keys: name, phone, email, "
            "address, job_intention, expected_salary, years_of_experience, education, "
            "projects, skills. Return JSON only.\n\nResume:\n"
            f"{resume_text[:12000]}"
        )
        return self._json_completion(prompt)

    def score_match(self, resume_text: str, job_description: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        prompt = (
            "你是严谨的招聘简历评估专家。请基于岗位 JD 和简历文本做语义匹配，"
            "不要只做字面关键词匹配。需要识别同义表达，例如“接入大模型接口”"
            "和“AI API/LLM API integration”应视为同一类能力；但不要把能力层级不同"
            "的内容混为一谈，例如“使用 ChatGPT”和“部署/微调大模型”不能直接等价。\n\n"
            "请按固定 Rubric 输出严格 JSON，禁止输出 Markdown。JSON schema 如下：\n"
            "{\n"
            '  "dimension_scores": {\n'
            '    "skill_match": 0-100,\n'
            '    "experience_relevance": 0-100,\n'
            '    "education_fit": 0-100,\n'
            '    "project_relevance": 0-100,\n'
            '    "keyword_coverage": 0-100\n'
            "  },\n"
            '  "requirement_matches": [\n'
            "    {\n"
            '      "requirement": "JD 中的一条具体要求",\n'
            '      "normalized_skill": "标准化能力项，例如 AI API integration",\n'
            '      "matched": true,\n'
            '      "match_level": "strong|partial|weak|none",\n'
            '      "score": 0-100,\n'
            '      "importance": "high|medium|low",\n'
            '      "evidence": "简历中的原文证据，找不到则为 null",\n'
            '      "reason": "为什么这样判断"\n'
            "    }\n"
            "  ],\n"
            '  "matched_keywords": ["标准化后的已满足能力项"],\n'
            '  "missing_skills": [\n'
            "    {\n"
            '      "skill": "缺失技能或能力项",\n'
            '      "normalized_skill": "标准化能力项",\n'
            '      "importance": "high|medium|low",\n'
            '      "reason": "为什么认为缺失"\n'
            "    }\n"
            "  ],\n"
            '  "summary": "简洁中文总结，说明匹配亮点、主要风险和建议追问方向"\n'
            "}\n\n"
            "评分标准：\n"
            "- skill_match：核心技能满足程度，优先看 JD 高重要性要求是否有证据支持。\n"
            "- experience_relevance：年限、行业/岗位经历、职责深度是否相关。\n"
            "- education_fit：学历、专业、证书是否满足硬性要求；无硬性学历要求时不要过低。\n"
            "- project_relevance：项目是否能证明岗位所需能力，重点看结果、职责和技术栈。\n"
            "- keyword_coverage：JD 关键能力项覆盖程度，允许语义同义匹配。\n\n"
            f"岗位 JD：\n{job_description[:7000]}\n\n简历文本：\n{resume_text[:14000]}"
        )
        return self._json_completion(prompt)

    def _json_completion(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.settings.ai_api_key,
                base_url=self.settings.ai_base_url,
            )
            messages = [
                {"role": "system", "content": "You are a precise HR resume analysis assistant. Return JSON only."},
                {"role": "user", "content": prompt},
            ]
            try:
                response = client.chat.completions.create(
                    model=self.settings.ai_model,
                    messages=messages,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
            except Exception:
                response = client.chat.completions.create(
                    model=self.settings.ai_model,
                    messages=messages,
                    temperature=0.1,
                )
            content = response.choices[0].message.content or "{}"
            parsed = _parse_json_object(content)
            if not parsed:
                logger.warning("AI response did not contain a valid JSON object. Preview: %s", content[:500])
            return parsed
        except Exception as exc:
            logger.warning("AI completion failed: %s", exc)
            return None


def _parse_json_object(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])

    return {}
