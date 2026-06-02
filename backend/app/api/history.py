from fastapi import APIRouter, Depends

from app.schemas.history import MatchHistoryItem
from app.services.auth import get_current_user
from app.services.history import list_match_history


router = APIRouter()


@router.get("/history", response_model=list[MatchHistoryItem])
def get_history(user=Depends(get_current_user)):
    return list_match_history(user["id"])
