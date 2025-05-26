from typing import Optional, List, Dict, Any
from app.schemas.fpl import TeamScore, Team, Player
from app.models.prediction import get_model_for_tier
from app.utils import fpl_data, config
import logging

# Configure logger
logger = logging.getLogger(__name__)


async def get_team_score(
    team_id: int, 
    gameweek: int, 
    subscription_tier: Optional[str] = "basic"
) -> TeamScore:
    """
    Get evaluation score and optimization suggestions for a given FPL team
    
    Args:
        team_id: FPL team ID
        gameweek: Gameweek number
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        Team score and evaluation
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek if not specified
    if gameweek <= 0:
        current_gw = await fpl_data.get_current_gameweek()
        gameweek = current_gw["id"]
    
    try:
        # Get team players - in a real implementation, you would get actual team data
        # For now, using the helper function from recommendation service
        from app.services.recommendation_service import get_team_players
        team_players = await get_team_players(team_id)
        
        # Use the model to evaluate the team
        evaluation = await model.evaluate_team(team_players, gameweek)
        
        # Format results according to schema
        return TeamScore(
            total_score=evaluation.get("total_score", 0.0),
            areas_of_strength=evaluation.get("areas_of_strength", []),
            areas_for_improvement=evaluation.get("areas_for_improvement", []),
            optimization_tips=evaluation.get("optimization_tips", [])
        )
    
    except Exception as e:
        logger.error(f"Error evaluating team: {str(e)}")
        # Return default values in case of error
        return TeamScore(
            total_score=0.0,
            areas_of_strength=[],
            areas_for_improvement=["Unable to evaluate team due to an error."],
            optimization_tips=["Try again later."]
        )


async def get_custom_team_score(
    team: Team, 
    gameweek: int, 
    subscription_tier: Optional[str] = "basic"
) -> TeamScore:
    """
    Get evaluation score and optimization suggestions for a custom team
    
    Args:
        team: Custom team data
        gameweek: Gameweek number
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        Team score and evaluation
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek if not specified
    if gameweek <= 0:
        current_gw = await fpl_data.get_current_gameweek()
        gameweek = current_gw["id"]
    
    try:
        # Use the model to evaluate the team
        evaluation = await model.evaluate_team(team.players, gameweek)
        
        # Format results according to schema
        return TeamScore(
            total_score=evaluation.get("total_score", 0.0),
            areas_of_strength=evaluation.get("areas_of_strength", []),
            areas_for_improvement=evaluation.get("areas_for_improvement", []),
            optimization_tips=evaluation.get("optimization_tips", [])
        )
    
    except Exception as e:
        logger.error(f"Error evaluating custom team: {str(e)}")
        # Return default values in case of error
        return TeamScore(
            total_score=0.0,
            areas_of_strength=[],
            areas_for_improvement=["Unable to evaluate team due to an error."],
            optimization_tips=["Try again later."]
        )
