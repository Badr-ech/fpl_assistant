"""
Mock service implementations for when ML models are not available
"""
from typing import List, Dict, Any, Optional
from app.schemas.fpl import Team, Player, TransferRecommendation, CaptainPick, TeamScore
import logging
import random

logger = logging.getLogger(__name__)

async def mock_transfer_suggestions(
    team: Team,
    budget: float,
    gameweek: int,
    subscription_tier: str = "basic",
    max_suggestions: int = 2
) -> List[Dict[str, Any]]:
    """
    Mock transfer suggestions when ML models are not available
    """
    try:
        # Get some popular players as mock suggestions
        from app.utils.fpl_data import get_players_by_form
        
        # Get current player IDs to avoid suggesting existing players
        current_ids = {p.id for p in team.players}
        
        suggestions = []
        positions = ["DEF", "MID", "FWD"]
        
        for pos in positions[:max_suggestions]:
            # Get top players by form for this position
            position_id = {"DEF": 2, "MID": 3, "FWD": 4}.get(pos, 3)
            top_players = await get_players_by_form(position=position_id, limit=5)
            
            # Find a player not in current team
            for player_data in top_players:
                if player_data["id"] not in current_ids and player_data["now_cost"] / 10.0 <= budget:
                    # Create mock player out (lowest scoring from same position)
                    players_same_pos = [p for p in team.players if p.position == pos]
                    if players_same_pos:
                        player_out = min(players_same_pos, key=lambda x: x.total_points)
                        
                        # Create player in
                        player_in = {
                            "id": player_data["id"],
                            "name": f"{player_data['first_name']} {player_data['second_name']}",
                            "price": player_data["now_cost"] / 10.0,
                            "form": float(player_data["form"]) if player_data["form"] else 0.0,
                            "total_points": player_data["total_points"]
                        }
                        
                        suggestions.append({
                            "player_out": player_out.dict(),
                            "player_in": player_in,
                            "predicted_impact": random.uniform(1.0, 5.0),
                            "reasoning": f"Better form and fixtures for {player_in['name']}"
                        })
                        break
        
        return suggestions[:max_suggestions]
    
    except Exception as e:
        logger.error(f"Error in mock transfer suggestions: {e}")
        return []

async def mock_captain_pick(
    team: Team,
    gameweek: int,
    subscription_tier: str = "basic"
) -> Optional[Dict[str, Any]]:
    """
    Mock captain pick when ML models are not available
    """
    try:
        if not team.players:
            return None
        
        # Pick the player with highest total points
        best_player = max(team.players, key=lambda x: x.total_points)
        
        return {
            "name": best_player.name,
            "player_id": best_player.id,
            "expected_points": best_player.total_points / 10,  # Mock expected points
            "reasoning": f"Highest total points ({best_player.total_points}) and consistent performer"
        }
    
    except Exception as e:
        logger.error(f"Error in mock captain pick: {e}")
        return None

async def mock_team_rating(
    team: Team,
    gameweek: int
) -> Dict[str, Any]:
    """
    Mock team rating when ML models are not available
    """
    try:
        # Simple scoring based on player stats
        total_points = sum(p.total_points for p in team.players)
        avg_points = total_points / len(team.players) if team.players else 0
        
        # Scale to 0-100
        score = min(100, max(0, avg_points * 2))
        
        suggestions = []
        if score < 70:
            suggestions.append("Consider upgrading your lowest-scoring players")
            suggestions.append("Look for players with better fixtures")
        
        return {
            "score": round(score, 1),
            "suggestions": suggestions,
            "rating": "Good" if score >= 70 else "Needs Improvement"
        }
    
    except Exception as e:
        logger.error(f"Error in mock team rating: {e}")
        return {"score": 50, "suggestions": ["Unable to analyze team"], "rating": "Unknown"}
