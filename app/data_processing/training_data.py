"""
FPL Training Data Processor

This module handles processing and preparing FPL data for training machine learning models.
It converts raw FPL API data into feature vectors suitable for training.
"""

import asyncio
import logging
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from app.utils.fpl_data import (
    get_bootstrap_data,
    get_players,
    get_player_with_history,
    get_team_by_id,
    get_fixture_difficulty,
    get_player_fixture_difficulty,
    get_teams
)

# Configure logger
logger = logging.getLogger(__name__)


async def get_player_extended_data(player_id: int, next_n_fixtures: int = 5) -> Dict[str, Any]:
    """
    Get extended player data including history and fixture difficulty
    
    Args:
        player_id: Player ID from FPL API
        next_n_fixtures: Number of upcoming fixtures to include
        
    Returns:
        Dictionary containing player data with extended information
    """
    # Get player data with history
    player_data = await get_player_with_history(player_id)
    
    # Get fixture difficulty for upcoming games
    fixture_difficulty = await get_player_fixture_difficulty(player_id, next_n=next_n_fixtures)
    
    # Calculate average fixture difficulty
    if fixture_difficulty:
        avg_difficulty = sum(fix["difficulty"] for fix in fixture_difficulty) / len(fixture_difficulty)
    else:
        avg_difficulty = 3.0  # Default medium difficulty
    
    # Get team data
    team_data = await get_team_by_id(player_data["team"])
    
    # Add extended data
    extended_data = {
        **player_data,
        "upcoming_fixtures": fixture_difficulty,
        "avg_fixture_difficulty": avg_difficulty,
        "team_name": team_data["name"] if team_data else "Unknown",
        "team_strength": team_data["strength"] if team_data else 0,
        "team_strength_overall_home": team_data["strength_overall_home"] if team_data else 0,
        "team_strength_overall_away": team_data["strength_overall_away"] if team_data else 0,
        "team_strength_attack_home": team_data["strength_attack_home"] if team_data else 0,
        "team_strength_attack_away": team_data["strength_attack_away"] if team_data else 0,
        "team_strength_defence_home": team_data["strength_defence_home"] if team_data else 0,
        "team_strength_defence_away": team_data["strength_defence_away"] if team_data else 0,
    }
    
    return extended_data


async def process_player_features(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process player data to extract features for machine learning
    
    Args:
        player_data: Extended player data from get_player_extended_data
        
    Returns:
        Dictionary of player features
    """
    # Calculate points per game (ppg)
    minutes = player_data["minutes"]
    total_points = player_data["total_points"]
    games_played = len([game for game in player_data.get("history", []) if game.get("minutes", 0) > 0])
    
    # Avoid division by zero
    ppg = total_points / max(1, games_played) if games_played > 0 else 0
    
    # Calculate points per 90 minutes
    points_per_90 = (total_points / max(1, minutes)) * 90 if minutes > 0 else 0
    
    # Extract raw form and convert to float, with default if missing
    raw_form = player_data.get("form", "0.0")
    form = float(raw_form) if raw_form and raw_form != "" else 0.0
    
    # Calculate recent form (last 3 games)
    history = player_data.get("history", [])
    recent_history = history[-3:] if len(history) >= 3 else history
    recent_points = sum(game.get("total_points", 0) for game in recent_history)
    recent_form = recent_points / len(recent_history) if recent_history else 0.0
    
    # Get xG and xA (expected goals and assists) if available, or approximate
    # Note: FPL API doesn't directly provide xG/xA, so we'll approximate from recent performance
    # In a real implementation, you might want to scrape these from another source
    goals = player_data.get("goals_scored", 0)
    assists = player_data.get("assists", 0)
    
    # Simple approximation of xG and xA based on past performance and minutes
    # In a real model, you'd want to use actual xG/xA data from a proper source
    xG_approx = (goals / max(1, games_played)) if games_played > 0 else 0
    xA_approx = (assists / max(1, games_played)) if games_played > 0 else 0
    
    # Extract ownership percentage
    selected_by_percent = float(player_data.get("selected_by_percent", "0.0").replace(',', '.'))
    
    # Process team strength relative to league average
    avg_strength = 1000  # Assumed average team strength in FPL
    relative_team_strength = (player_data.get("team_strength", avg_strength) / avg_strength) * 100
    
    features = {
        "player_id": player_data["id"],
        "name": f"{player_data.get('first_name', '')} {player_data.get('second_name', '')}",
        "team": player_data.get("team_name", "Unknown"),
        "position": get_position_name(player_data.get("element_type", 0)),
        "price": player_data.get("now_cost", 0) / 10.0,
        "form": form,
        "recent_form": recent_form,
        "points_per_game": ppg,
        "points_per_90": points_per_90,
        "minutes": player_data.get("minutes", 0),
        "goals_scored": player_data.get("goals_scored", 0),
        "assists": player_data.get("assists", 0),
        "clean_sheets": player_data.get("clean_sheets", 0),
        "goals_conceded": player_data.get("goals_conceded", 0),
        "own_goals": player_data.get("own_goals", 0),
        "penalties_saved": player_data.get("penalties_saved", 0),
        "penalties_missed": player_data.get("penalties_missed", 0),
        "yellow_cards": player_data.get("yellow_cards", 0),
        "red_cards": player_data.get("red_cards", 0),
        "saves": player_data.get("saves", 0),
        "bonus": player_data.get("bonus", 0),
        "bps": player_data.get("bps", 0),
        "influence": float(player_data.get("influence", 0)),
        "creativity": float(player_data.get("creativity", 0)),
        "threat": float(player_data.get("threat", 0)),
        "ict_index": float(player_data.get("ict_index", 0)),
        "xG": xG_approx,
        "xA": xA_approx,
        "ownership_percentage": selected_by_percent,
        "avg_fixture_difficulty": player_data.get("avg_fixture_difficulty", 3.0),
        "team_strength": relative_team_strength,
        "team_strength_attack_home": player_data.get("team_strength_attack_home", 0),
        "team_strength_attack_away": player_data.get("team_strength_attack_away", 0),
        "team_strength_defence_home": player_data.get("team_strength_defence_home", 0),
        "team_strength_defence_away": player_data.get("team_strength_defence_away", 0),
    }
    
    return features


def get_position_name(position_id: int) -> str:
    """
    Get position name from position ID
    
    Args:
        position_id: Position ID from FPL API
        
    Returns:
        Position name as string
    """
    positions = {
        1: "GK",   # Goalkeeper
        2: "DEF",  # Defender
        3: "MID",  # Midfielder
        4: "FWD"   # Forward
    }
    return positions.get(position_id, "Unknown")


async def prepare_training_data(output_dir: str, num_players: Optional[int] = None) -> str:
    """
    Prepare training data by fetching data for all players and processing features
    
    Args:
        output_dir: Directory to save the training data
        num_players: Optional limit on number of players to process (for testing)
        
    Returns:
        Path to the saved training data CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all players
    players = await get_players()
    
    # Limit number of players if specified
    if num_players:
        players = players[:num_players]
    
    logger.info(f"Processing data for {len(players)} players...")
    
    # Process each player
    player_features = []
    for i, player in enumerate(players):
        try:
            logger.info(f"Processing player {i+1}/{len(players)}: {player['first_name']} {player['second_name']}")
            # Use all available history (multi-season if possible)
            from app.utils.fpl_data import get_player_with_history_all_seasons
            extended_data = await get_player_with_history_all_seasons(player["id"])
            features = await process_player_features(extended_data)
            player_features.append(features)
        except Exception as e:
            logger.error(f"Error processing player {player['id']}: {str(e)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(player_features)
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"fpl_training_data_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    
    # Also save as JSON for raw data access
    json_path = os.path.join(output_dir, f"fpl_training_data_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(player_features, f, indent=2)
    
    logger.info(f"Training data saved to {csv_path}")
    return csv_path


async def generate_weekly_datasets(base_dir: str, weeks_of_history: int = 10) -> Dict[str, str]:
    """
    Generate weekly datasets for time-series prediction
    
    Args:
        base_dir: Base directory to save datasets
        weeks_of_history: Number of past gameweeks to include
        
    Returns:
        Dictionary mapping gameweek numbers to dataset paths
    """
    # Create output directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Get bootstrap data to find current gameweek
    bootstrap_data = await get_bootstrap_data()
    events = bootstrap_data.get("events", [])
    
    # Find current gameweek
    current_gw = None
    for event in events:
        if event.get("is_current", False):
            current_gw = event
            break
    
    if not current_gw:
        for event in events:
            if event.get("is_next", False):
                current_gw = event
                break
    
    if not current_gw:
        logger.warning("Could not determine current gameweek, using first gameweek")
        current_gw = events[0] if events else {"id": 1}
    
    current_gw_id = current_gw["id"]
    
    # Generate datasets for each of the past N gameweeks
    dataset_paths = {}
    start_gw = max(1, current_gw_id - weeks_of_history)
    
    for gw in range(start_gw, current_gw_id + 1):
        logger.info(f"Generating dataset for gameweek {gw}")
        
        # Create gameweek directory
        gw_dir = os.path.join(base_dir, f"gameweek_{gw}")
        os.makedirs(gw_dir, exist_ok=True)
        
        # Prepare dataset for this gameweek
        # In a real implementation, you'd filter player data to only include data available at that gameweek
        # For this example, we'll use current data but note this is a simplification
        dataset_path = await prepare_training_data(gw_dir, num_players=50)  # Limit to 50 players for example
        
        dataset_paths[str(gw)] = dataset_path
    
    return dataset_paths


async def generate_position_specific_datasets(base_dir: str) -> Dict[str, str]:
    """
    Generate position-specific datasets for specialized models
    
    Args:
        base_dir: Base directory to save datasets
        
    Returns:
        Dictionary mapping position names to dataset paths
    """
    # Create output directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Get all players
    players = await get_players()
    
    # Group players by position
    positions = {
        1: [],  # GK
        2: [],  # DEF
        3: [],  # MID
        4: []   # FWD
    }
    
    for player in players:
        pos = player.get("element_type", 0)
        if pos in positions:
            positions[pos].append(player)
    
    # Generate dataset for each position
    dataset_paths = {}
    for pos_id, pos_players in positions.items():
        pos_name = get_position_name(pos_id)
        logger.info(f"Generating dataset for position {pos_name} with {len(pos_players)} players")
        
        # Create position directory
        pos_dir = os.path.join(base_dir, pos_name.lower())
        os.makedirs(pos_dir, exist_ok=True)
        
        # Process players for this position
        player_features = []
        for i, player in enumerate(pos_players):
            try:
                logger.info(f"Processing {pos_name} {i+1}/{len(pos_players)}: {player['first_name']} {player['second_name']}")
                extended_data = await get_player_extended_data(player["id"])
                features = await process_player_features(extended_data)
                player_features.append(features)
            except Exception as e:
                logger.error(f"Error processing player {player['id']}: {str(e)}")
        
        # Convert to DataFrame
        df = pd.DataFrame(player_features)
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(pos_dir, f"{pos_name.lower()}_training_data_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        
        dataset_paths[pos_name] = csv_path
    
    return dataset_paths


async def normalize_features(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize features for better model performance
    
    Args:
        features_df: DataFrame of player features
        
    Returns:
        DataFrame with normalized features
    """
    # Create a copy to avoid modifying the original
    normalized_df = features_df.copy()
    
    # Define numeric columns to normalize
    numeric_cols = [
        'price', 'form', 'recent_form', 'points_per_game', 'points_per_90', 
        'minutes', 'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
        'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards',
        'red_cards', 'saves', 'bonus', 'bps', 'influence', 'creativity',
        'threat', 'ict_index', 'xG', 'xA', 'ownership_percentage',
        'avg_fixture_difficulty', 'team_strength', 'team_strength_attack_home',
        'team_strength_attack_away', 'team_strength_defence_home',
        'team_strength_defence_away'
    ]
    
    # Ensure all columns exist
    numeric_cols = [col for col in numeric_cols if col in normalized_df.columns]
    
    # Apply min-max normalization to numerical features
    for col in numeric_cols:
        min_val = normalized_df[col].min()
        max_val = normalized_df[col].max()
        
        if max_val > min_val:
            normalized_df[col] = (normalized_df[col] - min_val) / (max_val - min_val)
    
    return normalized_df


def load_merged_seasons_training_data(csv_path: str) -> pd.DataFrame:
    """
    Load and preprocess the unified multi-season FPL training dataset from CSV.
    Args:
        csv_path: Path to cleaned_merged_seasons.csv
    Returns:
        Preprocessed DataFrame ready for model training
    """
    logger.info(f"Loading multi-season training data from {csv_path}")
    df = pd.read_csv(csv_path)
    # Basic cleaning: drop rows with missing essential values
    essential_cols = ["name", "position", "minutes", "total_points", "season_x", "GW"]
    df = df.dropna(subset=essential_cols)
    # Convert types if needed
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce").fillna(0)
    df["total_points"] = pd.to_numeric(df["total_points"], errors="coerce").fillna(0)
    df["GW"] = pd.to_numeric(df["GW"], errors="coerce").fillna(0)
    # Add points per 90 and points per game
    df["points_per_90"] = df["total_points"] / df["minutes"].replace(0, np.nan) * 90
    df["points_per_game"] = df["total_points"] / df.groupby(["season_x", "name"])['GW'].transform('count')
    df["points_per_90"] = df["points_per_90"].replace([np.inf, -np.inf], 0).fillna(0)
    df["points_per_game"] = df["points_per_game"].replace([np.inf, -np.inf], 0).fillna(0)
    # Standardize column names if needed (e.g., 'position' to uppercase)
    df["position"] = df["position"].str.upper()
    return df


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Define async main function
    async def main():
        # Define output directory relative to current script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "..", "..", "data", "training")
        
        # Generate main training dataset
        logger.info("Generating main training dataset")
        await prepare_training_data(os.path.join(base_dir, "main"))
        
        # Generate position-specific datasets
        logger.info("Generating position-specific datasets")
        await generate_position_specific_datasets(os.path.join(base_dir, "positions"))
        
        # Generate weekly datasets
        logger.info("Generating weekly datasets")
        await generate_weekly_datasets(os.path.join(base_dir, "weekly"), weeks_of_history=3)
        
        logger.info("Data preparation complete!")
    
    # Run main function
    asyncio.run(main())
