import re
from typing import List


def clean_resume_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?m)^\s*[-_]{3,}\s*$", "", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def split_sections(text: str) -> List[str]:
    chunks = re.split(r"\n(?=\S)", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]
