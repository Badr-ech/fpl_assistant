"""
Feature Standardization Module

This module provides standardized feature extraction for ML models to ensure
consistency between training and prediction phases.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Training feature names from process_player_features function
TRAINING_FEATURE_NAMES = [
    "price", "form", "recent_form", "points_per_game", "points_per_90", 
    "minutes", "goals_scored", "assists", "clean_sheets", "goals_conceded",
    "own_goals", "penalties_saved", "penalties_missed", "yellow_cards",
    "red_cards", "saves", "bonus", "bps", "influence", "creativity",
    "threat", "ict_index", "xG", "xA", "ownership_percentage",
    "avg_fixture_difficulty", "team_strength", "team_strength_attack_home",
    "team_strength_attack_away", "team_strength_defence_home",
    "team_strength_defence_away"
]


def convert_player_to_features(player_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Convert player data (from schema or API) to standardized training features
    
    Args:
        player_data: Player data dictionary (can be from schema or API)
        
    Returns:
        Dictionary with standardized feature names and values
    """
    features = {}
    
    # Basic stats
    total_points = player_data.get("total_points", 0)
    minutes = player_data.get("minutes", 0)
    
    # Calculate derived features
    # Approximate games played (assuming 90 mins per game)
    games_played = max(1, minutes // 60)  # Conservative estimate
    
    # Points per game
    ppg = total_points / max(1, games_played) if games_played > 0 else 0
    
    # Points per 90 minutes
    points_per_90 = (total_points / max(1, minutes)) * 90 if minutes > 0 else 0
    
    # Form - handle both string and float
    form_raw = player_data.get("form", 0)
    if isinstance(form_raw, str):
        try:
            form = float(form_raw) if form_raw else 0.0
        except ValueError:
            form = 0.0
    else:
        form = float(form_raw) if form_raw is not None else 0.0
    
    # Recent form (approximate from current form for prediction)
    recent_form = form
    
    # Price conversion
    price = player_data.get("price", 0)
    if price is None:
        price = 0
    # If price is in FPL format (e.g., 120 for £12.0M), convert
    if "now_cost" in player_data:
        price = player_data["now_cost"] / 10.0
    
    # Ownership percentage
    ownership_raw = player_data.get("selected_by_percent", "0.0")
    if isinstance(ownership_raw, str):
        try:
            ownership_percentage = float(ownership_raw.replace(',', '.'))
        except ValueError:
            ownership_percentage = 0.0
    else:
        ownership_percentage = float(ownership_raw) if ownership_raw is not None else 0.0
    
    # Team strength (default values if not available)
    team_strength = player_data.get("team_strength", 100.0)
    
    # Fixture difficulty (use provided or default)
    avg_fixture_difficulty = player_data.get("avg_fixture_difficulty", 3.0)
    
    # xG and xA approximations
    goals = player_data.get("goals_scored", 0)
    assists = player_data.get("assists", 0)
    xG = (goals / max(1, games_played)) if games_played > 0 else 0
    xA = (assists / max(1, games_played)) if games_played > 0 else 0
    
    # Build feature dictionary
    features = {
        "price": float(price),
        "form": float(form),
        "recent_form": float(recent_form),
        "points_per_game": float(ppg),
        "points_per_90": float(points_per_90),
        "minutes": float(player_data.get("minutes", 0)),
        "goals_scored": float(player_data.get("goals_scored", 0)),
        "assists": float(player_data.get("assists", 0)),
        "clean_sheets": float(player_data.get("clean_sheets", 0)),
        "goals_conceded": float(player_data.get("goals_conceded", 0)),
        "own_goals": float(player_data.get("own_goals", 0)),
        "penalties_saved": float(player_data.get("penalties_saved", 0)),
        "penalties_missed": float(player_data.get("penalties_missed", 0)),
        "yellow_cards": float(player_data.get("yellow_cards", 0)),
        "red_cards": float(player_data.get("red_cards", 0)),
        "saves": float(player_data.get("saves", 0)),
        "bonus": float(player_data.get("bonus", 0)),
        "bps": float(player_data.get("bps", 0)),
        "influence": float(player_data.get("influence", 0)),
        "creativity": float(player_data.get("creativity", 0)),
        "threat": float(player_data.get("threat", 0)),
        "ict_index": float(player_data.get("ict_index", 0)),
        "xG": float(xG),
        "xA": float(xA),
        "ownership_percentage": float(ownership_percentage),
        "avg_fixture_difficulty": float(avg_fixture_difficulty),
        "team_strength": float(team_strength),
        "team_strength_attack_home": float(player_data.get("team_strength_attack_home", 0)),
        "team_strength_attack_away": float(player_data.get("team_strength_attack_away", 0)),
        "team_strength_defence_home": float(player_data.get("team_strength_defence_home", 0)),
        "team_strength_defence_away": float(player_data.get("team_strength_defence_away", 0)),
    }
    
    return features


def prepare_features_for_model(
    player_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
    model_feature_names: Optional[List[str]] = None
) -> Union[Dict[str, float], pd.DataFrame]:
    """
    Prepare player data for ML model prediction
    
    Args:
        player_data: Single player dict or list of player dicts
        model_feature_names: List of feature names expected by the model
        
    Returns:
        Feature dictionary (single player) or DataFrame (multiple players)
    """
    if isinstance(player_data, list):
        # Multiple players
        features_list = []
        for player in player_data:
            features = convert_player_to_features(player)
            features_list.append(features)
        
        df = pd.DataFrame(features_list)
        
        # Reindex to match model's expected features
        if model_feature_names:
            df = df.reindex(columns=model_feature_names, fill_value=0.0)
        
        return df
    else:
        # Single player
        features = convert_player_to_features(player_data)
        
        # Filter to match model's expected features
        if model_feature_names:
            filtered_features = {}
            for feature_name in model_feature_names:
                filtered_features[feature_name] = features.get(feature_name, 0.0)
            return filtered_features
        
        return features


def standardize_player_features_for_prediction(
    players: List[Dict[str, Any]], 
    model_feature_names: List[str]
) -> pd.DataFrame:
    """
    Standardize multiple players' features for model prediction
    
    Args:
        players: List of player dictionaries
        model_feature_names: Feature names expected by the model
        
    Returns:
        DataFrame with standardized features
    """
    features_list = []
    
    for player in players:
        try:
            features = convert_player_to_features(player)
            features_list.append(features)
        except Exception as e:
            logger.warning(f"Error processing player {player.get('id', 'unknown')}: {e}")
            # Add default features for this player
            default_features = {name: 0.0 for name in TRAINING_FEATURE_NAMES}
            features_list.append(default_features)
    
    df = pd.DataFrame(features_list)
    
    # Ensure all required features are present and in correct order
    df = df.reindex(columns=model_feature_names, fill_value=0.0)
    
    return df


def get_training_feature_names() -> List[str]:
    """
    Get the list of feature names used in training
    
    Returns:
        List of training feature names
    """
    return TRAINING_FEATURE_NAMES.copy()


def validate_features(features: Dict[str, float]) -> Dict[str, float]:
    """
    Validate and clean feature values
    
    Args:
        features: Feature dictionary
        
    Returns:
        Cleaned feature dictionary
    """
    cleaned = {}
    
    for key, value in features.items():
        try:
            # Convert to float and handle NaN/inf
            float_val = float(value) if value is not None else 0.0
            
            # Replace NaN and inf with 0
            if np.isnan(float_val) or np.isinf(float_val):
                float_val = 0.0
            
            cleaned[key] = float_val
        except (ValueError, TypeError):
            logger.warning(f"Invalid value for feature {key}: {value}, using 0.0")
            cleaned[key] = 0.0
    
    return cleaned
