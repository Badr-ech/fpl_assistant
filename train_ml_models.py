#!/usr/bin/env python
"""
Fantasy Premier League Assistant - ML Model Training Script

This script prepares training data and trains machine learning models for the FPL Assistant.
Run this script before starting the application to ensure models are available.

Usage:
    python train_ml_models.py [--prepare-data] [--model-types basic,premium,elite] [--num-players 300]

Options:
    --prepare-data      Prepare training data (fetch from FPL API)
    --model-types       Model types to train (comma-separated, default: basic,premium,elite)
    --num-players       Number of players to include in training data (default: all)
"""

import os
import asyncio
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for troubleshooting
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("training_output.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_section_header(title):
    logger.info(f"\n{'=' * 10} {title} {'=' * 10}")


def print_metrics_summary(metrics, model_type, indent=0):
    if not metrics:
        logger.warning(f"No metrics found for {model_type}.")
        return
    indent_str = '  ' * indent
    logger.info(f"\n{model_type.capitalize()} Model Metrics:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            logger.info(f"{indent_str}{key}:")
            print_metrics_summary(value, model_type, indent=indent+1)
        else:
            try:
                logger.info(f"{indent_str}  {key}: {value:.4f}")
            except Exception:
                logger.info(f"{indent_str}  {key}: {value}")
    if indent == 0:
        logger.info("")


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Train FPL ML models")
    parser.add_argument('--prepare-data', action='store_true', help='Prepare training data')
    parser.add_argument('--num-players', type=int, default=None, help='Number of players to include in training data')
    parser.add_argument('--model-types', type=str, default='basic,premium,elite', help='Model types to train (comma-separated)')
    args = parser.parse_args()
    
    # Parse model types
    model_types = args.model_types.split(',')
    
    # Define directories
    base_dir = Path(__file__).parent
    data_dir = base_dir / "app" / "data" / "training"
    model_dir = base_dir / "app" / "models" / "trained"
    
    # Create directories if they don't exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)
    
    # Convert to strings for compatibility with functions expecting string paths
    data_dir_str = str(data_dir)
    model_dir_str = str(model_dir)
    
    # Import here to avoid circular imports
    from app.training.train_models import prepare_training_data, generate_position_specific_datasets
    from app.training.train_models import train_position_specific_models, train_captain_models, train_transfer_models
    
    # Prepare data if requested
    if args.prepare_data:
        logger.info("Preparing training data...")
        # --- Use merged multi-season CSV for maximal training data ---
        from app.data_processing.training_data import load_merged_seasons_training_data
        merged_csv_path = os.path.join(base_dir, "app", "data", "cleaned_merged_seasons.csv")
        if os.path.exists(merged_csv_path):
            logger.info(f"Loading multi-season data from {merged_csv_path}")
            df_merged = load_merged_seasons_training_data(merged_csv_path)
            # Save to main training dir for downstream pipeline compatibility
            main_data_dir = os.path.join(data_dir_str, "main")
            os.makedirs(main_data_dir, exist_ok=True)
            merged_out_path = os.path.join(main_data_dir, "fpl_training_data_multiseason.csv")
            df_merged.to_csv(merged_out_path, index=False)
            logger.info(f"Multi-season training data saved to {merged_out_path}")
        else:
            logger.warning(f"Multi-season CSV not found at {merged_csv_path}. Falling back to API-based data preparation.")
            # Fallback: prepare data as before
            await prepare_training_data(os.path.join(data_dir_str, "main"), num_players=args.num_players)
        logger.info("Generating position-specific datasets...")
        await generate_position_specific_datasets(os.path.join(data_dir_str, "positions"))
        logger.info("Position-specific datasets ready.")
    
    # Train models
    print_section_header("Training Position-Specific Models")
    logger.info("Starting training of position-specific models...")
    position_metrics = await train_position_specific_models(
        base_dir=os.path.join(data_dir_str, "positions"),
        output_dir=model_dir_str,
        model_types=model_types
    )
    logger.info("Position-specific models training complete.")
    
    print_section_header("Training Captain Models")
    logger.info("Starting training of captain models...")
    captain_metrics = await train_captain_models(
        base_dir=data_dir_str,
        output_dir=model_dir_str,
        model_types=model_types
    )
    logger.info("Captain models training complete.")
    
    # --- Inject predicted next_gw_points into main dataset for transfer model training ---
    import pandas as pd
    import joblib
    from app.models.ml_models import PointsPredictor
    import shutil
    import time

    # Find latest main dataset
    main_data_dir = os.path.join(data_dir_str, "main")
    main_files = [f for f in os.listdir(main_data_dir) if f.endswith('.csv')]
    if not main_files:
        logger.error("No main CSV files found in data directory. Aborting transfer model training.")
        return
    main_files.sort(reverse=True)
    main_csv = os.path.join(main_data_dir, main_files[0])
    try:
        df = pd.read_csv(main_csv)
    except Exception as e:
        logger.error(f"Failed to read main CSV: {main_csv}. Error: {e}")
        return
    if df.empty:
        logger.error(f"Main CSV {main_csv} is empty. Aborting transfer model training.")
        return

    # For each player, predict next_gw_points using the correct trained model (by position and tier)
    # We'll use the highest tier available (elite > premium > basic)
    tier_priority = ['stacking', 'elite', 'premium', 'basic']
    positions = ['gk', 'def', 'mid', 'fwd']
    predictors = {}
    logger.info("Loading trained points predictor models for all positions...")
    for pos in positions:
        for tier in tier_priority:
            if tier == 'stacking':
                model_path = os.path.join(model_dir_str, f"points_predictor_{pos}_stacking_stacking.joblib")
                # stacking ensemble uses a special file naming
                if os.path.exists(model_path):
                    predictors[pos] = PointsPredictor(model_type='stacking', position=pos.upper(), model_dir=model_dir_str)
                    if predictors[pos].load():
                        break
            else:
                model_path = os.path.join(model_dir_str, f"points_predictor_{pos}_{tier}.joblib")
                scaler_path = os.path.join(model_dir_str, f"points_predictor_{pos}_{tier}_scaler.joblib")
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    predictors[pos] = PointsPredictor(model_type=tier, position=pos.upper(), model_dir=model_dir_str)
                    if predictors[pos].load():
                        break
        if pos not in predictors:
            logger.warning(f"No points predictor model found for position {pos.upper()}. Will fallback to points_per_game.")
    logger.info("All points predictor models loaded.")

    # Predict next_gw_points for each player
    logger.info("Predicting next_gw_points for all players in main dataset...")
    pred_points = []
    for idx, (row_idx, row) in enumerate(df.iterrows()):
        pos = str(row['position']).lower()
        predictor = predictors.get(pos)
        if idx % 500 == 0:
            logger.info(f"Predicting player {idx+1}/{len(df)}...")
        try:
            if predictor is not None and predictor.feature_names:
                # Always use predictor.feature_names
                features = {fname: 0 for fname in predictor.feature_names}
                row_features = row.drop(['player_id', 'name', 'team', 'position'], errors='ignore').fillna(0)
                row_features = row_features.infer_objects()  # Fix pandas downcasting warning
                row_features = row_features.to_dict()
                for k, v in row_features.items():
                    if k in features:
                        features[k] = v
                pred = predictor.predict(features)
                pred_points.append(pred)
            else:
                pred_points.append(row.get('points_per_game', 0))
        except Exception as e:
            logger.error(f"Prediction failed for player {row.get('name', 'unknown')} (ID: {row.get('player_id', 'N/A')}): {e}")
            pred_points.append(row.get('points_per_game', 0))
    df['next_gw_points'] = pred_points
    logger.info("next_gw_points prediction complete.")

    # Overwrite the latest main CSV with the new one for transfer model training
    unique_id = f"{os.getpid()}_{int(time.time())}"
    backup_csv = main_csv + f'.bak_{unique_id}'
    shutil.copy2(main_csv, backup_csv)
    df.to_csv(main_csv, index=False)

    try:
        print_section_header("Training Transfer Models")
        logger.info("Starting training of transfer models...")
        transfer_metrics = await train_transfer_models(
            base_dir=data_dir_str,
            output_dir=model_dir_str,
            model_types=model_types
        )
        logger.info("Transfer models training complete.")
    finally:
        # Restore the original main CSV
        shutil.move(backup_csv, main_csv)
    
    logger.info("\nModel training complete!")
    print_metrics_summary(position_metrics, "position-specific")
    print_metrics_summary(captain_metrics, "captain")
    print_metrics_summary(transfer_metrics, "transfer")


if __name__ == "__main__":
    asyncio.run(main())
