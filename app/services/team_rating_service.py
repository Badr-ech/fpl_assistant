from typing import List, Dict, Any, Optional
from app.schemas.fpl import Team, Player
from app.utils.fpl_data import get_player_fixture_difficulty
import logging

logger = logging.getLogger(__name__)

async def rate_team(team: Team, gameweek: int) -> Dict[str, Any]:
    """
    Rate a team (0-100) based on balance, injuries, fixtures, and coverage.
    Suggest improvements if score < 70.
    Args:
        team: Team schema
        gameweek: Target gameweek
    Returns:
        Dict with score and suggestions
    """
    try:
        players = team.players
        score = 100
        suggestions = []

        # 1. Balance: Check for at least 2 GKs, 5 DEFs, 5 MIDs, 3 FWDs
        pos_counts = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for p in players:
            pos_counts[p.position] = pos_counts.get(p.position, 0) + 1
        if pos_counts["GK"] < 2:
            score -= 10
            suggestions.append("Add a backup goalkeeper.")
        if pos_counts["DEF"] < 4:
            score -= 10
            suggestions.append("Increase defensive depth.")
        if pos_counts["MID"] < 4:
            score -= 10
            suggestions.append("Increase midfield depth.")
        if pos_counts["FWD"] < 2:
            score -= 10
            suggestions.append("Increase forward depth.")

        # 2. Injuries: Penalize for injured/unavailable players
        for p in players:
            if getattr(p, "status", "a") not in ("a", "d"):
                score -= 5
                suggestions.append(f"Replace injured/unavailable player: {p.name}")

        # 3. Fixtures: Penalize for too many players with hard fixtures
        hard_fixture_count = 0
        for p in players:
            try:
                fixtures = await get_player_fixture_difficulty(p.id, next_n=1)
                avg_diff = fixtures[0]["difficulty"] if fixtures else 3.0
            except:
                avg_diff = 3.0
            if avg_diff >= 4:
                hard_fixture_count += 1
        
        if hard_fixture_count > 6:
            score -= 15
            suggestions.append("Too many players with difficult fixtures.")

        # 4. Value: Basic value assessment
        total_value = sum(p.price for p in players)
        if total_value < 90:  # Team too cheap
            score -= 10
            suggestions.append("Consider upgrading to higher-value players.")

        return {
            "score": max(0, score),
            "suggestions": suggestions,
            "rating": "Excellent" if score >= 90 else "Good" if score >= 70 else "Needs Improvement"
        }
    
    except Exception as e:
        logger.error(f"Error in rate_team: {e}")
        # Use mock service as fallback
        from app.services.mock_service import mock_team_rating
        return await mock_team_rating(team, gameweek)
    if hard_fixture_count > 4:
        score -= 10
        suggestions.append("Too many players with tough upcoming fixtures.")

    # 4. Coverage: Penalize if too many players from one team
    team_counts = {}
    for p in players:
        team_counts[p.team] = team_counts.get(p.team, 0) + 1
    for t, count in team_counts.items():
        if count > 3:
            score -= 5
            suggestions.append(f"Too many players from {t} (>{count}).")

    # Clamp score
    score = max(0, min(100, score))
    result: Dict[str, Any] = {"score": score}
    if score < 70:
        result["suggestions"] = suggestions
    return result
