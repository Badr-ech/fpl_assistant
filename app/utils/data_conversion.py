from typing import Dict, List, Any
from app.schemas.fpl import Player, Team


def convert_api_player_to_schema(player_data: Dict[str, Any]) -> Player:
    """
    Convert FPL API player data to our Player schema
    
    Args:
        player_data: Player data from the FPL API
        
    Returns:
        Player object
    """
    return Player(
        id=player_data["id"],
        name=f"{player_data['first_name']} {player_data['second_name']}",
        team=player_data["team"],  # In a real implementation, we'd map this to the team name
        position=get_position_name(player_data["element_type"]),
        price=player_data["now_cost"] / 10.0,
        total_points=player_data["total_points"],
        form=float(player_data["form"]),
        minutes=player_data["minutes"],
        goals_scored=player_data["goals_scored"],
        assists=player_data["assists"],
        clean_sheets=player_data["clean_sheets"],
        goals_conceded=player_data["goals_conceded"],
        own_goals=player_data["own_goals"],
        penalties_saved=player_data["penalties_saved"],
        penalties_missed=player_data["penalties_missed"],
        yellow_cards=player_data["yellow_cards"],
        red_cards=player_data["red_cards"],
        saves=player_data["saves"],
        bonus=player_data["bonus"]
    )


def get_position_name(position_id: int) -> str:
    """
    Convert position ID to name
    
    Args:
        position_id: Position ID from FPL API
        
    Returns:
        Position name
    """
    positions = {
        1: "GK",  # Goalkeeper
        2: "DEF",  # Defender
        3: "MID",  # Midfielder
        4: "FWD"   # Forward
    }
    return positions.get(position_id, "Unknown")


def convert_api_team_to_schema(team_data: Dict[str, Any], 
                              player_details: Dict[int, Dict[str, Any]]) -> Team:
    """
    Convert FPL API team data to our Team schema
    
    Args:
        team_data: Team data from the FPL API
        player_details: Dictionary mapping player IDs to their details
        
    Returns:
        Team object
    """
    players = []
    total_value = 0.0
    
    for pick in team_data["picks"]:
        player_id = pick["element"]
        if player_id in player_details:
            player = convert_api_player_to_schema(player_details[player_id])
            players.append(player)
            total_value += player.price
    
    return Team(
        players=players,
        total_value=total_value,
        remaining_budget=team_data.get("budget", 0) / 10.0
    )
