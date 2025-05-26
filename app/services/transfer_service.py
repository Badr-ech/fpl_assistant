from typing import List, Dict, Any, Optional
from app.schemas.fpl import Team, Player
from app.models.model_selector import predict_transfer_for_subscription
from app.utils.fpl_data import get_player_fixture_difficulty
import logging

logger = logging.getLogger(__name__)

async def suggest_transfers(
    team: Team,
    budget: float,
    gameweek: int,
    subscription_tier: str = "basic",
    max_suggestions: int = 2
) -> List[Dict[str, Any]]:
    """
    Suggest top transfer options for a user's team using the selected AI model.
    Considers price limits, upcoming fixtures, and player form.
    Args:
        team: User's current team (Team schema)
        budget: Remaining budget for transfers
        gameweek: Target gameweek
        subscription_tier: User's subscription tier
        max_suggestions: Number of transfer suggestions to return
    Returns:
        List of top transfer suggestions
    """
    try:
        current_players = [player.dict() for player in team.players]
        # Build a pool of potential transfers (all players not in team, within budget)
        from app.utils.fpl_data import get_all_players
        all_players = await get_all_players()
        current_ids = {p['id'] for p in current_players}
        
        # Only consider players not already in team and affordable
        potential_transfers = []
        for player in all_players:
            if player['id'] in current_ids:
                continue
            if player['now_cost'] / 10.0 > budget:
                continue
            # Add fixture difficulty for next GW
            try:
                fixtures = await get_player_fixture_difficulty(player['id'], next_n=1)
                player['avg_fixture_difficulty'] = fixtures[0]['difficulty'] if fixtures else 3.0
            except:
                player['avg_fixture_difficulty'] = 3.0
            potential_transfers.append(player)
        
        # Try to use AI model to evaluate transfers
        try:
            suggestions = predict_transfer_for_subscription(current_players, potential_transfers, subscription_tier)
            # Filter and sort by predicted impact, form, and fixture
            suggestions = sorted(suggestions, key=lambda x: (
                -x.get('predicted_impact', 0),
                -x['player_in'].get('form', 0),
                x['player_in'].get('avg_fixture_difficulty', 3.0)
            ))
            return suggestions[:max_suggestions]
        except Exception as model_error:
            logger.warning(f"ML model not available, using fallback: {model_error}")
            # Use mock service as fallback
            from app.services.mock_service import mock_transfer_suggestions
            return await mock_transfer_suggestions(team, budget, gameweek, subscription_tier, max_suggestions)
    
    except Exception as e:
        logger.error(f"Error in suggest_transfers: {e}")
        # Return empty list as final fallback
        return []
