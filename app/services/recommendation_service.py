from typing import List, Optional, Dict, Any
from app.schemas.fpl import TransferRecommendation, Team, Player
from app.models.prediction import get_model_for_tier
from app.utils import fpl_data, config
import logging

# Configure logger
logger = logging.getLogger(__name__)


async def get_team_players(team_id: int) -> List[Player]:
    """
    Get a team's players from FPL API
    
    Args:
        team_id: FPL team ID
        
    Returns:
        List of Player objects
    """
    try:
        # Get actual team data from FPL API
        team_data = await fpl_data.get_team_players(team_id)
        
        # Convert to Player objects
        players = []
        
        for player_data in team_data:
            player = Player(
                id=player_data.get("id", 0),
                name=player_data.get("name", "Unknown"),
                team=player_data.get("team", "Unknown"),
                position=player_data.get("position", "Unknown"),
                price=player_data.get("price", 0.0),
                form=player_data.get("form", 0.0),
                total_points=player_data.get("total_points", 0),
                minutes=player_data.get("minutes", 0),
                goals_scored=player_data.get("goals_scored", 0),
                assists=player_data.get("assists", 0),
                clean_sheets=player_data.get("clean_sheets", 0),
                goals_conceded=player_data.get("goals_conceded", 0),
                own_goals=player_data.get("own_goals", 0),
                penalties_saved=player_data.get("penalties_saved", 0),
                penalties_missed=player_data.get("penalties_missed", 0),
                yellow_cards=player_data.get("yellow_cards", 0),
                red_cards=player_data.get("red_cards", 0),
                saves=player_data.get("saves", 0),
                bonus=player_data.get("bonus", 0)
            )
            players.append(player)
        
        return players
    
    except Exception as e:
        logger.error(f"Error fetching team players: {str(e)}")
        return []


async def get_transfer_targets(
    current_players: List[Player], 
    budget: float = 0.0,
    limit: int = 20
) -> List[Player]:
    """
    Get potential transfer targets
    
    Args:
        current_players: Current team players
        budget: Available budget
        limit: Maximum number of targets to return
        
    Returns:
        List of potential transfer targets
    """
    try:
        # In a real implementation, you would filter players based on budget, etc.
        # For now, we'll get players with good form who aren't already in the team
        
        all_targets = []
        
        # Get targets for each position
        for position_id, position_name in [(1, "GK"), (2, "DEF"), (3, "MID"), (4, "FWD")]:
            # Get top form players for this position
            position_players = await fpl_data.get_players_by_form(position=position_id, limit=limit)
            
            for player_data in position_players:
                # Skip if player is already in the team
                player_id = player_data.get("id", 0)
                if any(p.id == player_id for p in current_players):
                    continue
                
                # Get team name
                team_id = player_data.get("team", 0)
                team_data = await fpl_data.get_team_by_id(team_id)
                team_name = team_data.get("name", "Unknown") if team_data else "Unknown"
                
                player = Player(
                    id=player_data.get("id", 0),
                    name=f"{player_data.get('first_name', '')} {player_data.get('second_name', '')}",
                    team=team_name,
                    position=position_name,
                    price=player_data.get("now_cost", 0) / 10.0,  # Convert to actual price
                    form=float(player_data.get("form", "0.0")),
                    total_points=player_data.get("total_points", 0),
                    minutes=player_data.get("minutes", 0),
                    goals_scored=player_data.get("goals_scored", 0),
                    assists=player_data.get("assists", 0),
                    clean_sheets=player_data.get("clean_sheets", 0),
                    goals_conceded=player_data.get("goals_conceded", 0),
                    own_goals=player_data.get("own_goals", 0),
                    penalties_saved=player_data.get("penalties_saved", 0),
                    penalties_missed=player_data.get("penalties_missed", 0),
                    yellow_cards=player_data.get("yellow_cards", 0),
                    red_cards=player_data.get("red_cards", 0),
                    saves=player_data.get("saves", 0),
                    bonus=player_data.get("bonus", 0)
                )
                all_targets.append(player)
        
        return all_targets
    
    except Exception as e:
        logger.error(f"Error fetching transfer targets: {str(e)}")
        return []


async def get_transfer_recommendations(
    team_id: int, 
    budget: float, 
    free_transfers: int, 
    subscription_tier: Optional[str] = "basic"
) -> List[TransferRecommendation]:
    """
    Get recommended transfers for a given FPL team
    
    Args:
        team_id: FPL team ID
        budget: Available budget for transfers
        free_transfers: Number of free transfers available
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        List of recommended transfers
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek
    gameweek_info = await fpl_data.get_current_gameweek()
    gameweek_id = gameweek_info["id"]
    
    # Get tier configuration
    tier_config = config.settings.SUBSCRIPTION_TIERS.get(
        subscription_tier or "basic", 
        config.settings.SUBSCRIPTION_TIERS["basic"]
    )
    recommendations_limit = tier_config.get("recommendations_limit", 3)
    
    try:
        # Get team players data
        team_players = await get_team_players(team_id)
        
        # Get potential transfer targets
        potential_transfers = await get_transfer_targets(
            team_players, 
            budget=budget,
            limit=recommendations_limit*5  # Get more candidates than needed for filtering
        )
        
        # Use the model to rank transfers
        recommendations_data = await model.rank_transfers(
            current_team=team_players,
            potential_transfers=potential_transfers, 
            gameweek=gameweek_id
        )
        
        # Format results according to schema
        recommendations = []
        for rec_data in recommendations_data[:recommendations_limit]:
            # Find player objects by name
            player_out_name = rec_data.get("player_out", "")
            player_in_name = rec_data.get("player_in", "")
            
            player_out = next((p for p in team_players if p.name == player_out_name), None)
            player_in = next((p for p in potential_transfers if p.name == player_in_name), None)
            
            if player_out and player_in:
                recommendations.append(
                    TransferRecommendation(
                        player_out=player_out,
                        player_in=player_in,
                        reasoning=rec_data.get("reasoning", "Better overall performance expected."),
                        expected_point_impact=rec_data.get("expected_point_impact", 0.0)
                    )
                )
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating transfer recommendations: {str(e)}")
        # Return empty list in case of error
        return []


async def get_custom_recommendations(
    team: Team, 
    free_transfers: int, 
    subscription_tier: Optional[str] = "basic"
) -> List[TransferRecommendation]:
    """
    Get recommended transfers for a custom team
    
    Args:
        team: Custom team data
        free_transfers: Number of free transfers available
        subscription_tier: User subscription tier (basic, premium, elite)
        
    Returns:
        List of recommended transfers
    """
    # Get AI model for the subscription tier
    model = get_model_for_tier(subscription_tier or "basic")
    
    # Get current gameweek
    gameweek_info = await fpl_data.get_current_gameweek()
    gameweek_id = gameweek_info["id"]
    
    # Get tier configuration
    tier_config = config.settings.SUBSCRIPTION_TIERS.get(
        subscription_tier or "basic", 
        config.settings.SUBSCRIPTION_TIERS["basic"]
    )
    recommendations_limit = tier_config.get("recommendations_limit", 3)
    
    try:
        # Get potential transfer targets
        potential_transfers = await get_transfer_targets(
            team.players, 
            budget=team.remaining_budget,
            limit=recommendations_limit*5  # Get more candidates than needed for filtering
        )
        
        # Use the model to rank transfers
        recommendations_data = await model.rank_transfers(
            current_team=team.players,
            potential_transfers=potential_transfers, 
            gameweek=gameweek_id
        )
        
        # Format results according to schema
        recommendations = []
        for rec_data in recommendations_data[:recommendations_limit]:
            # Find player objects by name
            player_out_name = rec_data.get("player_out", "")
            player_in_name = rec_data.get("player_in", "")
            
            player_out = next((p for p in team.players if p.name == player_out_name), None)
            player_in = next((p for p in potential_transfers if p.name == player_in_name), None)
            
            if player_out and player_in:
                recommendations.append(
                    TransferRecommendation(
                        player_out=player_out,
                        player_in=player_in,
                        reasoning=rec_data.get("reasoning", "Better overall performance expected."),
                        expected_point_impact=rec_data.get("expected_point_impact", 0.0)
                    )
                )
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error generating custom recommendations: {str(e)}")
        # Return empty list in case of error
        return []
