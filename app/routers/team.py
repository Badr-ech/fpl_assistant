from fastapi import APIRouter, HTTPException
from app.utils.fpl_data import get_team_players

router = APIRouter()

@router.get("/team/{team_id}")
async def get_team(team_id: int):
    try:
        players = await get_team_players(team_id)
        if not players:
            raise HTTPException(status_code=404, detail="Team not found")
        return players
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
