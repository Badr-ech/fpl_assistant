from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.schemas.fpl import CaptainPick, Team
from app.services import captain_service
from app.services.captain_picker_service import pick_best_captain

router = APIRouter(
    prefix="/captain",
    tags=["captain"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[CaptainPick])
async def get_captain_picks(
    team_id: int = Query(..., description="FPL Team ID"),
    gameweek: int = Query(..., description="Gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get captain recommendations for a given FPL team and gameweek
    """
    try:
        captain_picks = await captain_service.get_captain_recommendations(
            team_id, gameweek, subscription_tier
        )
        return captain_picks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=List[CaptainPick])
async def get_custom_captain_picks(
    team: Team,
    gameweek: int = Query(..., description="Gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get captain recommendations for a custom team
    """
    try:
        captain_picks = await captain_service.get_custom_captain_recommendations(
            team, gameweek, subscription_tier
        )
        return captain_picks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/best", response_model=Optional[Dict[str, Any]])
async def get_best_captain(
    team: Team,
    gameweek: int = Query(..., description="Target gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Return the best captain pick for a user's team using the selected AI model.
    """
    try:
        best_pick = await pick_best_captain(team, gameweek, subscription_tier or "basic")
        return best_pick
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
