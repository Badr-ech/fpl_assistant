"""
FPL ML Model Training Script

This script prepares training data and trains ML models for FPL predictions.
It uses historical player data to train models for:
1. Player point prediction
2. Captain selection
3. Transfer recommendations
4. Team evaluation

Train models by running:
python -m app.training.train_models
"""

import os
import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import argparse

from app.models.ml_models import (
    PointsPredictor,
    CaptainRanker,
    TransferAdvisor,
    TeamEvaluator
)

from app.data_processing.training_data import (
    prepare_training_data,
    generate_position_specific_datasets,
    normalize_features
)

# Configure logger
logger = logging.getLogger(__name__)


async def prepare_prediction_dataset(base_dataset_path: str, weeks_to_predict: int = 5) -> pd.DataFrame:
    """
    Prepare dataset for training prediction models
    
    Args:
        base_dataset_path: Path to base FPL training dataset
        weeks_to_predict: Number of future gameweeks to include
        
    Returns:
        DataFrame ready for model training
    """
    # Load base dataset
    logger.info(f"Loading base dataset from {base_dataset_path}")
    df = pd.read_csv(base_dataset_path)
    
    # Create columns to predict next gameweek points
    logger.info(f"Preparing prediction targets for {weeks_to_predict} future gameweeks")
    
    # Since this is a new dataset creation, we'll simulate future points using
    # a combination of form, fixture difficulty, and historical performance
    # In a real implementation, you would use actual historical data across gameweeks
    
    # Calculate baseline expected points using current points_per_game
    df['next_gw_points'] = df['points_per_game']
    
    # Adjust based on form (positive form increases expected points)
    form_factor = 0.2  # Weight for form adjustment
    df['next_gw_points'] = df['next_gw_points'] + (df['form'] - df['points_per_game']) * form_factor
    
    # Adjust based on fixture difficulty (higher difficulty decreases expected points)
    fixture_factor = 0.15  # Weight for fixture adjustment
    df['next_gw_points'] = df['next_gw_points'] - (df['avg_fixture_difficulty'] - 2.5) * fixture_factor
    
    # Ensure points are non-negative
    df['next_gw_points'] = df['next_gw_points'].apply(lambda x: max(0, x))
    
    # For captain points, we'll simulate higher variance and higher ceiling
    df['captain_points'] = df['next_gw_points'] * 2  # Double points for captain
    
    # Add random variance to make the model less deterministic
    np.random.seed(42)  # For reproducibility
    variance = np.random.normal(0, 1, size=len(df)) * (df['next_gw_points'] * 0.3)
    df['captain_points'] = df['captain_points'] + variance
    df['captain_points'] = df['captain_points'].apply(lambda x: max(0, x))
    
    logger.info(f"Dataset prepared with {len(df)} player records")
    return df


async def prepare_transfer_dataset(base_dataset_path: str, num_pairs: int = 1000) -> pd.DataFrame:
    """
    Prepare dataset for transfer recommendation models
    
    Args:
        base_dataset_path: Path to base FPL training dataset
        num_pairs: Number of player pairs to generate
        
    Returns:
        DataFrame with transfer features and impact
    """
    # Load base dataset
    logger.info(f"Loading base dataset from {base_dataset_path}")
    df = pd.read_csv(base_dataset_path)
    
    # Generate player pairs for transfers (within same position)
    logger.info(f"Generating {num_pairs} player transfer pairs")
    
    # Group players by position
    grouped = df.groupby('position')
    
    transfer_rows = []
    for position, group in grouped:
        # Calculate how many pairs to generate for this position
        # Weight by squad composition: DEF/MID more than GK/FWD
        position_weights = {
            'GK': 0.1,
            'DEF': 0.35,
            'MID': 0.35,
            'FWD': 0.2
        }
        
        position_pairs = int(num_pairs * position_weights.get(str(position), 0.25))
        
        # Generate random pairs
        players = group.sample(n=min(len(group), position_pairs * 2), replace=True)
        
        # Create pairs
        for i in range(0, min(len(players) - 1, position_pairs)):
            player_out = players.iloc[i].copy()
            player_in = players.iloc[i + 1].copy()
            
            # Skip if same player
            if player_out['player_id'] == player_in['player_id']:
                continue
                
            # Calculate point impact (simulate with adjusted next_gw_points difference)
            # Add randomness to make the model less deterministic
            raw_point_diff = player_in['next_gw_points'] - player_out['next_gw_points']
            variance = np.random.normal(0, 1) * 2  # Random variance
            point_impact = raw_point_diff + variance
            
            # Create transfer features
            transfer_data = {
                # IDs and names
                'player_in_id': player_in['player_id'],
                'player_out_id': player_out['player_id'],
                'player_in_name': player_in['name'],
                'player_out_name': player_out['name'],
                'position': position,
                
                # Player in features
                'player_in_form': player_in['form'],
                'player_in_points_per_game': player_in['points_per_game'],
                'player_in_minutes': player_in['minutes'],
                'player_in_goals': player_in.get('goals_scored', 0),
                'player_in_assists': player_in.get('assists', 0),
                'player_in_clean_sheets': player_in.get('clean_sheets', 0),
                'player_in_fixture_difficulty': player_in['avg_fixture_difficulty'],
                'player_in_ict': player_in.get('ict_index', 0),
                'player_in_bonus': player_in.get('bonus', 0),
                'player_in_price': player_in['price'],
                
                # Player out features
                'player_out_form': player_out['form'],
                'player_out_points_per_game': player_out['points_per_game'],
                'player_out_minutes': player_out['minutes'],
                'player_out_goals': player_out.get('goals_scored', 0),
                'player_out_assists': player_out.get('assists', 0),
                'player_out_clean_sheets': player_out.get('clean_sheets', 0),
                'player_out_fixture_difficulty': player_out['avg_fixture_difficulty'],
                'player_out_ict': player_out.get('ict_index', 0),
                'player_out_bonus': player_out.get('bonus', 0),
                'player_out_price': player_out['price'],
                
                # Difference features
                'form_diff': player_in['form'] - player_out['form'],
                'price_diff': player_in['price'] - player_out['price'],
                'fixture_diff': player_out['avg_fixture_difficulty'] - player_in['avg_fixture_difficulty'],
                'team_strength_diff': player_in.get('team_strength', 0) - player_out.get('team_strength', 0),
                
                # Target
                'points_delta': point_impact
            }
            
            transfer_rows.append(transfer_data)
    
    # Create DataFrame
    transfer_df = pd.DataFrame(transfer_rows)
    logger.info(f"Transfer dataset prepared with {len(transfer_df)} transfer records")
    return transfer_df


async def train_position_specific_models(base_dir: str, output_dir: str, model_types: List[str]) -> Dict[str, Any]:
    """
    Train position-specific prediction models
    
    Args:
        base_dir: Directory with position datasets
        output_dir: Directory to save trained models
        model_types: List of model types to train (basic, premium, elite)
        
    Returns:
        Dictionary with model performance metrics by position
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Position to train for
    positions = ["GK", "DEF", "MID", "FWD"]
    
    # Store metrics
    metrics = {}
    
    gbm_types = ["lgbm", "xgboost", "catboost", "tabnet"]
    all_types = list(model_types) + gbm_types
    
    for position in positions:
        position_dir = os.path.join(base_dir, position.lower())
        
        # Check if position directory exists
        if not os.path.isdir(position_dir):
            logger.warning(f"Position directory {position_dir} not found, skipping")
            continue
        
        # Get the latest dataset in the position directory
        datasets = [f for f in os.listdir(position_dir) if f.endswith('.csv')]
        if not datasets:
            logger.warning(f"No datasets found in {position_dir}, skipping")
            continue
            
        datasets.sort(reverse=True)  # Sort by filename (with timestamp) descending
        dataset_path = os.path.join(position_dir, datasets[0])
        
        logger.info(f"Preparing prediction dataset for {position} from {dataset_path}")
        prediction_df = await prepare_prediction_dataset(dataset_path)
        
        # Train models for each type
        position_metrics = {}
        
        for model_type in all_types:
            logger.info(f"Training {model_type} model for {position}")
            
            # Create and train points predictor
            predictor = PointsPredictor(
                model_type=model_type,
                position=position,
                model_dir=output_dir
            )
            
            metrics_dict = predictor.train(prediction_df)
            predictor.save()
            
            position_metrics[model_type] = metrics_dict
            logger.info(f"{model_type} model for {position} - MAE: {metrics_dict['mae']:.4f}")
        
        metrics[position] = position_metrics
    
    return metrics


async def train_captain_models(base_dir: str, output_dir: str, model_types: List[str]) -> Dict[str, Any]:
    """
    Train captain recommendation models
    
    Args:
        base_dir: Directory with main dataset
        output_dir: Directory to save trained models
        model_types: List of model types to train
        
    Returns:
        Dictionary with model performance metrics
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find latest dataset in the main directory
    main_dir = os.path.join(base_dir, "main")
    datasets = [f for f in os.listdir(main_dir) if f.endswith('.csv')]
    
    if not datasets:
        logger.warning(f"No datasets found in {main_dir}, skipping")
        return {}
    
    datasets.sort(reverse=True)
    dataset_path = os.path.join(main_dir, datasets[0])
    
    logger.info(f"Preparing captain dataset from {dataset_path}")
    prediction_df = await prepare_prediction_dataset(dataset_path)
    
    # Train models for each type
    metrics = {}
    
    gbm_types = ["lgbm", "xgboost", "catboost", "tabnet"]
    all_types = list(model_types) + gbm_types
    
    for model_type in all_types:
        logger.info(f"Training {model_type} captain model")
        
        # Create and train captain ranker
        ranker = CaptainRanker(
            model_type=model_type,
            model_dir=output_dir
        )
        
        metrics_dict = ranker.train(prediction_df, target_col="captain_points")
        ranker.save()
        
        metrics[model_type] = metrics_dict
        logger.info(f"{model_type} captain model - MAE: {metrics_dict['mae']:.4f}")
    
    return metrics


async def train_transfer_models(base_dir: str, output_dir: str, model_types: List[str]) -> Dict[str, Any]:
    """
    Train transfer recommendation models
    
    Args:
        base_dir: Directory with main dataset
        output_dir: Directory to save trained models
        model_types: List of model types to train
        
    Returns:
        Dictionary with model performance metrics
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find latest dataset in the main directory
    main_dir = os.path.join(base_dir, "main")
    datasets = [f for f in os.listdir(main_dir) if f.endswith('.csv')]
    
    if not datasets:
        logger.warning(f"No datasets found in {main_dir}, skipping")
        return {}
    
    datasets.sort(reverse=True)
    dataset_path = os.path.join(main_dir, datasets[0])
    
    logger.info(f"Preparing transfer dataset from {dataset_path}")
    transfer_df = await prepare_transfer_dataset(dataset_path)
    
    # Train general transfer model
    metrics = {}
    
    gbm_types = ["lgbm", "xgboost", "catboost", "tabnet"]
    all_types = list(model_types) + gbm_types
    
    for model_type in all_types:
        logger.info(f"Training {model_type} transfer model")
        
        # Create and train transfer advisor
        advisor = TransferAdvisor(
            model_type=model_type,
            model_dir=output_dir
        )
        
        metrics_dict = advisor.train(transfer_df)
        advisor.save()
        
        metrics[model_type] = metrics_dict
        logger.info(f"{model_type} transfer model - MAE: {metrics_dict['mae']:.4f}")
    
    return metrics


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Train FPL ML models')
    parser.add_argument('--prepare-data', action='store_true', help='Prepare training data')
    parser.add_argument('--num-players', type=int, default=None, help='Number of players to include in training data')
    parser.add_argument('--model-types', type=str, default='basic,premium,elite', help='Model types to train (comma-separated)')
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Parse model types
    model_types = args.model_types.split(',')
    
    async def main():
        # Define directories
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "..", "..", "data", "training")
        model_dir = os.path.join(script_dir, "..", "..", "models")
        
        # Prepare data if requested
        if args.prepare_data:
            logger.info("Preparing training data")
            # Generate main training dataset
            await prepare_training_data(os.path.join(base_dir, "main"), num_players=args.num_players)
            # Generate position-specific datasets
            await generate_position_specific_datasets(os.path.join(base_dir, "positions"))
        
        # Train position-specific prediction models
        logger.info("Training position-specific models")
        position_metrics = await train_position_specific_models(
            base_dir=os.path.join(base_dir, "positions"),
            output_dir=model_dir,
            model_types=model_types
        )
        
        # Train captain models
        logger.info("Training captain models")
        captain_metrics = await train_captain_models(
            base_dir=base_dir,
            output_dir=model_dir,
            model_types=model_types
        )
        
        # Train transfer models
        logger.info("Training transfer models")
        transfer_metrics = await train_transfer_models(
            base_dir=base_dir,
            output_dir=model_dir,
            model_types=model_types
        )
        
        logger.info("Model training complete!")
        logger.info(f"Position-specific model metrics: {position_metrics}")
        logger.info(f"Captain model metrics: {captain_metrics}")
        logger.info(f"Transfer model metrics: {transfer_metrics}")
    
    # Run main function
    asyncio.run(main())
