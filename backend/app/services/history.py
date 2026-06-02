from typing import List

from app.schemas.history import MatchHistoryCreate, MatchHistoryItem
from app.services.database import get_connection


def save_match_history(user_id: int, item: MatchHistoryCreate) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO match_history (
                user_id, resume_id, candidate_name, contact, job_title,
                score, analysis_mode, job_description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                item.resume_id,
                item.candidate_name,
                item.contact,
                item.job_title,
                item.score,
                item.analysis_mode,
                item.job_description,
            ),
        )


def list_match_history(user_id: int, limit: int = 50) -> List[MatchHistoryItem]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, resume_id, candidate_name, contact, job_title,
                   score, analysis_mode, created_at
            FROM match_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [MatchHistoryItem(**dict(row)) for row in rows]
