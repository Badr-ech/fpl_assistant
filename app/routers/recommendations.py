from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.fpl import TransferRecommendation, Team
from app.services import recommendation_service
from app.services.transfer_service import suggest_transfers

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[TransferRecommendation])
async def get_recommendations(
    team_id: int = Query(..., description="FPL Team ID"),
    budget: float = Query(..., description="Available budget for transfers"),
    free_transfers: int = Query(..., description="Number of free transfers available"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get recommended transfers for a given FPL team
    """
    try:
        recommendations = await recommendation_service.get_transfer_recommendations(
            team_id, budget, free_transfers, subscription_tier
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=List[TransferRecommendation])
async def get_custom_recommendations(
    team: Team,
    free_transfers: int = Query(..., description="Number of free transfers available"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Get recommended transfers for a custom team
    """
    try:
        recommendations = await recommendation_service.get_custom_recommendations(
            team, free_transfers, subscription_tier
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfers", response_model=List[dict])
async def get_transfer_suggestions(
    team: Team,
    budget: float = Query(..., description="Remaining budget for transfers"),
    gameweek: int = Query(..., description="Target gameweek number"),
    subscription_tier: Optional[str] = Query("basic", description="User subscription tier (basic, premium, elite)")
):
    """
    Suggest top transfer options for a user's team using the selected AI model.
    """
    try:
        suggestions = await suggest_transfers(team, budget, gameweek, subscription_tier or "basic")
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
