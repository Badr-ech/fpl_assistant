from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from app.schemas.fpl import TeamScore, Team
from app.services import team_service
from app.services.team_rating_service import rate_team

router = APIRouter(
    prefix="/team-score",
    tags=["team-score"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=TeamScore)
async def get_team_score(
    team_id: int = Query(..., description="FPL Team ID"),
    gameweek: int = Query(..., description="Gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get evaluation score and optimization suggestions for a given FPL team
    """
    try:
        team_score = await team_service.get_team_score(
            team_id, gameweek, subscription_tier
        )
        return team_score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=TeamScore)
async def get_custom_team_score(
    team: Team,
    gameweek: int = Query(..., description="Gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get evaluation score and optimization suggestions for a custom team
    """
    try:
        team_score = await team_service.get_custom_team_score(
            team, gameweek, subscription_tier
        )
        return team_score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate", response_model=Dict[str, Any])
async def get_team_rating(
    team: Team,
    gameweek: int = Query(..., description="Target gameweek number")
):
    """
    Rate a team (0-100) and provide improvement suggestions if needed.
    """
    try:
        result = await rate_team(team, gameweek)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
