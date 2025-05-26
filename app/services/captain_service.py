from typing import List, Optional, Dict, Any
from app.schemas.fpl import CaptainPick, Team, Player
from app.models.prediction import get_model_for_tier
from app.utils import fpl_data, config
import logging

# Configure logger
logger = logging.getLogger(__name__)


async def get_captain_recommendations(
    team_id: int, 
    gameweek: int, 
    subscription_tier: Optional[str] = "basic"
) -> List[CaptainPick]:
    """
    Get captain recommendations for a given FPL team and gameweek
    
    Args:
        team_id: FPL team ID
        gameweek: Gameweek number
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        List of captain picks in order of recommendation
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek if not specified
    if gameweek <= 0:
        current_gw = await fpl_data.get_current_gameweek()
        gameweek = current_gw["id"]
    
    # Get tier configuration
    tier_config = config.settings.SUBSCRIPTION_TIERS.get(
        subscription_tier or "basic", 
        config.settings.SUBSCRIPTION_TIERS["basic"]
    )
    captain_picks_limit = tier_config.get("captain_picks_limit", 2)
    
    try:
        # Get team players - in a real implementation, you would get actual team data
        # For now, using the helper function from recommendation service
        from app.services.recommendation_service import get_team_players
        team_players = await get_team_players(team_id)
        
        # Use the model to recommend captains
        captain_picks_data = await model.recommend_captain(team_players, gameweek)
        
        # Format results according to schema
        recommendations = []
        for pick_data in captain_picks_data[:captain_picks_limit]:
            # Find player by name
            player_name = pick_data.get("player", "")
            player = next((p for p in team_players if p.name == player_name), None)
            
            if player:
                recommendations.append(
                    CaptainPick(
                        player=player,
                        reasoning=pick_data.get("reasoning", "Strong candidate for returns."),
                        expected_points=pick_data.get("expected_points", 0.0)
                    )
                )
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating captain recommendations: {str(e)}")
        # Return empty list in case of error
        return []


async def get_custom_captain_recommendations(
    team: Team, 
    gameweek: int, 
    subscription_tier: Optional[str] = "basic"
) -> List[CaptainPick]:
    """
    Get captain recommendations for a custom team
    
    Args:
        team: Custom team data
        gameweek: Gameweek number
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        List of captain picks in order of recommendation
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek if not specified
    if gameweek <= 0:
        current_gw = await fpl_data.get_current_gameweek()
        gameweek = current_gw["id"]
    
    # Get tier configuration
    tier_config = config.settings.SUBSCRIPTION_TIERS.get(
        subscription_tier or "basic", 
        config.settings.SUBSCRIPTION_TIERS["basic"]
    )
    captain_picks_limit = tier_config.get("captain_picks_limit", 2)
    
    try:
        # Use the model to recommend captains
        captain_picks_data = await model.recommend_captain(team.players, gameweek)
        
        # Format results according to schema
        recommendations = []
        for pick_data in captain_picks_data[:captain_picks_limit]:
            # Find player by name
            player_name = pick_data.get("player", "")
            player = next((p for p in team.players if p.name == player_name), None)
            
            if player:
                recommendations.append(
                    CaptainPick(
                        player=player,
                        reasoning=pick_data.get("reasoning", "Strong candidate for returns."),
                        expected_points=pick_data.get("expected_points", 0.0)
                    )
                )
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating custom captain recommendations: {str(e)}")
        # Return empty list in case of error
        return []
