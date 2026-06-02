import hashlib


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def short_id(content: bytes) -> str:
    return sha256_bytes(content)[:16]


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
