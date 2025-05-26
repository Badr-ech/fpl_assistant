from typing import List, Dict, Any, Optional
from app.schemas.fpl import Team, Player
from app.models.model_selector import predict_captain_for_subscription
from app.utils.fpl_data import get_player_fixture_difficulty
import logging

logger = logging.getLogger(__name__)

async def pick_best_captain(
    team: Team,
    gameweek: int,
    subscription_tier: str = "basic"
) -> Optional[Dict[str, Any]]:
    """
    Return the best captain choice for a user's team based on model prediction of expected points.
    Args:
        team: User's current team (Team schema)
        gameweek: Target gameweek
        subscription_tier: User's subscription tier
    Returns:
        Dict with best captain pick info, or None if not found
    """
    try:
        players_features = []
        for player in team.players:
            features = player.dict()
            try:
                fixtures = await get_player_fixture_difficulty(player.id, next_n=1)
                features["avg_fixture_difficulty"] = fixtures[0]["difficulty"] if fixtures else 3.0
            except:
                features["avg_fixture_difficulty"] = 3.0
            players_features.append(features)
        
        # Try to use ML model
        try:
            ranked = predict_captain_for_subscription(players_features, subscription_tier)
            if ranked and len(ranked) > 0:
                return ranked[0]
        except Exception as model_error:
            logger.warning(f"ML model not available, using fallback: {model_error}")
            # Use mock service as fallback
            from app.services.mock_service import mock_captain_pick
            return await mock_captain_pick(team, gameweek, subscription_tier)
    
    except Exception as e:
        logger.error(f"Error in pick_best_captain: {e}")
        return None
