"""
FPL Data Ingestion Module

This module handles fetching and parsing data from the FPL API.
"""

import httpx
import logging
from typing import Dict, List, Any, Optional, Union
from functools import lru_cache
import asyncio
from datetime import datetime, timedelta
import os
import glob
import json

# Configure logger
logger = logging.getLogger(__name__)

# FPL API URLs
BASE_URL = "https://fantasy.premierleague.com/api"
BOOTSTRAP_URL = f"{BASE_URL}/bootstrap-static/"
FIXTURES_URL = f"{BASE_URL}/fixtures/"
PLAYER_DETAIL_URL = f"{BASE_URL}/element-summary"
TEAM_URL = f"{BASE_URL}/entry"

# Cache expiration time (in seconds)
CACHE_EXPIRY = 3600  # 1 hour


class FPLDataCache:
    """Class to handle caching of FPL data with expiration"""
    
    def __init__(self):
        # Use explicit types with Optional to allow None values
        self.bootstrap_data = None  # type: Optional[Dict[str, Any]]
        self.bootstrap_timestamp = None  # type: Optional[datetime]
        self.fixtures_data = None  # type: Optional[List[Dict[str, Any]]]
        self.fixtures_timestamp = None  # type: Optional[datetime]
        self.player_details_cache = {}  # type: Dict[int, Dict[str, Any]]
        self.player_details_timestamp = {}  # type: Dict[int, datetime]
    
    def is_bootstrap_expired(self) -> bool:
        """Check if bootstrap cache has expired"""
        if not self.bootstrap_timestamp:
            return True
        return (datetime.now() - self.bootstrap_timestamp).total_seconds() > CACHE_EXPIRY
    
    def is_fixtures_expired(self) -> bool:
        """Check if fixtures cache has expired"""
        if not self.fixtures_timestamp:
            return True
        return (datetime.now() - self.fixtures_timestamp).total_seconds() > CACHE_EXPIRY
    
    def is_player_details_expired(self, player_id: int) -> bool:
        """Check if player details cache has expired for a specific player"""
        if player_id not in self.player_details_timestamp:
            return True
        return (datetime.now() - self.player_details_timestamp[player_id]).total_seconds() > CACHE_EXPIRY


# Initialize cache
data_cache = FPLDataCache()


async def get_bootstrap_data() -> Dict[str, Any]:
    """
    Get general FPL data including teams, players, and gameweeks
    
    Returns:
        Dictionary containing FPL bootstrap static data
    """
    global data_cache
    
    # Return cached data if available and not expired
    if data_cache.bootstrap_data and not data_cache.is_bootstrap_expired():
        logger.debug("Using cached bootstrap data")
        assert data_cache.bootstrap_data is not None
        return data_cache.bootstrap_data
    
    try:
        logger.info("Fetching bootstrap data from FPL API")
        async with httpx.AsyncClient() as client:
            response = await client.get(BOOTSTRAP_URL, timeout=30.0)
            response.raise_for_status()
              # Update cache
            data_cache.bootstrap_data = response.json()
            data_cache.bootstrap_timestamp = datetime.now()
            
            assert data_cache.bootstrap_data is not None
            return data_cache.bootstrap_data
    except httpx.RequestError as e:
        logger.error(f"Error fetching FPL bootstrap data: {str(e)}")
        raise Exception(f"Failed to fetch FPL bootstrap data: {str(e)}")


async def get_fixtures_data() -> List[Dict[str, Any]]:
    """
    Get fixture data for all teams
    
    Returns:
        List of dictionaries containing fixture data
    """
    global data_cache
    
    # Return cached data if available and not expired
    if data_cache.fixtures_data and not data_cache.is_fixtures_expired():
        logger.debug("Using cached fixtures data")
        assert data_cache.fixtures_data is not None
        return data_cache.fixtures_data
    
    try:
        logger.info("Fetching fixtures data from FPL API")
        async with httpx.AsyncClient() as client:
            response = await client.get(FIXTURES_URL, timeout=30.0)
            response.raise_for_status()
              # Update cache
            data_cache.fixtures_data = response.json()
            data_cache.fixtures_timestamp = datetime.now()
            
            assert data_cache.fixtures_data is not None
            return data_cache.fixtures_data
    except httpx.RequestError as e:
        logger.error(f"Error fetching FPL fixtures data: {str(e)}")
        raise Exception(f"Failed to fetch FPL fixtures data: {str(e)}")


async def get_player_detail_data(player_id: int) -> Dict[str, Any]:
    """
    Get detailed data for a specific player
    
    Args:
        player_id: Player ID in the FPL API
    
    Returns:
        Dictionary containing detailed player data
    """
    global data_cache
    
    # Return cached data if available and not expired
    if (player_id in data_cache.player_details_cache and 
            not data_cache.is_player_details_expired(player_id)):
        logger.debug(f"Using cached player detail data for player ID {player_id}")
        return data_cache.player_details_cache[player_id]
    
    try:
        logger.info(f"Fetching player detail data for player ID {player_id}")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PLAYER_DETAIL_URL}/{player_id}/", timeout=30.0)
            response.raise_for_status()
            
            # Update cache
            data_cache.player_details_cache[player_id] = response.json()
            data_cache.player_details_timestamp[player_id] = datetime.now()
            
            return data_cache.player_details_cache[player_id]
    except httpx.RequestError as e:
        logger.error(f"Error fetching player detail data for player ID {player_id}: {str(e)}")
        raise Exception(f"Failed to fetch player detail data: {str(e)}")


async def get_players() -> List[Dict[str, Any]]:
    """
    Get data for all players
    
    Returns:
        List of dictionaries containing player data
    """
    bootstrap_data = await get_bootstrap_data()
    return bootstrap_data.get("elements", [])


async def get_all_players() -> List[Dict[str, Any]]:
    """
    Get all player dicts (public alias for get_players)
    """
    return await get_players()


async def get_player_by_id(player_id: int) -> Optional[Dict[str, Any]]:
    """
    Get player data by player ID
    
    Args:
        player_id: Player ID in the FPL API
    
    Returns:
        Dictionary containing player data or None if not found
    """
    players = await get_players()
    
    for player in players:
        if player["id"] == player_id:
            return player
    
    logger.warning(f"Player with ID {player_id} not found")
    return None


async def get_player_with_history(player_id: int) -> Dict[str, Any]:
    """
    Get player data including history and fixtures
    
    Args:
        player_id: Player ID in the FPL API
    
    Returns:
        Dictionary containing player data, history, and fixtures
    """
    # Get basic player data
    player = await get_player_by_id(player_id)
    if not player:
        raise Exception(f"Player with ID {player_id} not found")
    
    # Get detailed data including history and fixtures
    player_details = await get_player_detail_data(player_id)
    
    # Combine data
    result = {**player, "history": player_details.get("history", []), "fixtures": player_details.get("fixtures", [])}
    return result


async def get_player_with_history_all_seasons(player_id: int) -> Dict[str, Any]:
    """
    Get player data including history and fixtures for all available seasons.
    Aggregates from local files in app/data/ (e.g., 2018-19.json, 2019-20.json, etc.) if available.
    Falls back to current season if no files found.
    """
    player = await get_player_by_id(player_id)
    if not player:
        raise Exception(f"Player with ID {player_id} not found")

    # Directory where multi-season files are stored
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    data_dir = os.path.abspath(data_dir)
    season_files = glob.glob(os.path.join(data_dir, '*.json'))
    all_history = []
    found = False
    for season_file in season_files:
        try:
            with open(season_file, 'r', encoding='utf-8') as f:
                season_data = json.load(f)
                # Each file should be a list of player dicts with 'id' and 'history'
                for p in season_data:
                    if p.get('id') == player_id and 'history' in p:
                        all_history.extend(p['history'])
                        found = True
        except Exception as e:
            logger.warning(f"Could not read {season_file}: {e}")
    if not found:
        # Fallback to current season only
        player_details = await get_player_detail_data(player_id)
        all_history = player_details.get('history', [])
        fixtures = player_details.get('fixtures', [])
    else:
        # Use current season's fixtures (API only provides current)
        player_details = await get_player_detail_data(player_id)
        fixtures = player_details.get('fixtures', [])
    result = {**player, "history": all_history, "fixtures": fixtures}
    return result


async def get_teams() -> List[Dict[str, Any]]:
    """
    Get data for all teams
    
    Returns:
        List of dictionaries containing team data
    """
    bootstrap_data = await get_bootstrap_data()
    return bootstrap_data.get("teams", [])


async def get_team_by_id(team_id: int) -> Optional[Dict[str, Any]]:
    """
    Get team data by team ID
    
    Args:
        team_id: Team ID in the FPL API
    
    Returns:
        Dictionary containing team data or None if not found
    """
    teams = await get_teams()
    
    for team in teams:
        if team["id"] == team_id:
            return team
    
    logger.warning(f"Team with ID {team_id} not found")
    return None


async def get_team_players(team_id: int) -> list:
    """
    Fetch the actual FPL team for the given team_id from the FPL API.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get current gameweek
            bootstrap = await client.get("https://fantasy.premierleague.com/api/bootstrap-static/")
            bootstrap.raise_for_status()
            bootstrap_data = bootstrap.json()
            events = bootstrap_data["events"]
            current_gw = next((e["id"] for e in events if e["is_current"]), None)
            if not current_gw:
                current_gw = max(e["id"] for e in events if e["is_next"])
            
            # Get team picks for the current gameweek
            picks_resp = await client.get(f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{current_gw}/picks/")
            picks_resp.raise_for_status()
            picks = picks_resp.json()["picks"]
            
            # Get all player data and teams
            all_players = bootstrap_data["elements"]
            all_teams = bootstrap_data["teams"]
            player_map = {p["id"]: p for p in all_players}
            team_map = {t["id"]: t for t in all_teams}
            
            # Position mapping
            position_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
            
            # Build the team with transformed data structure
            team_players = []
            for pick in picks:
                player_data = player_map.get(pick["element"])
                if player_data:
                    # Transform FPL API format to our internal format
                    team_name = team_map.get(player_data["team"], {}).get("name", "Unknown")
                    position = position_map.get(player_data["element_type"], "Unknown")
                    
                    transformed_player = {
                        "id": player_data["id"],
                        "name": f"{player_data['first_name']} {player_data['second_name']}".strip(),
                        "team": team_name,
                        "position": position,
                        "price": player_data["now_cost"] / 10.0,  # Convert from pence to pounds
                        "total_points": player_data["total_points"],
                        "form": float(player_data["form"]) if player_data["form"] else 0.0,
                        "minutes": player_data["minutes"],
                        "goals_scored": player_data["goals_scored"],
                        "assists": player_data["assists"],
                        "clean_sheets": player_data["clean_sheets"],
                        "goals_conceded": player_data["goals_conceded"],
                        "own_goals": player_data["own_goals"],
                        "penalties_saved": player_data["penalties_saved"],
                        "penalties_missed": player_data["penalties_missed"],
                        "yellow_cards": player_data["yellow_cards"],
                        "red_cards": player_data["red_cards"],
                        "saves": player_data["saves"],
                        "bonus": player_data["bonus"]
                    }
                    team_players.append(transformed_player)
            
            return team_players
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error fetching real FPL team: {e}")
        return []


async def get_current_gameweek() -> Dict[str, Any]:
    """
    Get the current gameweek data
    
    Returns:
        Dictionary containing current gameweek data
    """
    bootstrap_data = await get_bootstrap_data()
    events = bootstrap_data.get("events", [])
    
    for event in events:
        if event["is_current"]:
            return event
    
    # If no current gameweek found, return the next one
    for event in events:
        if event["is_next"]:
            return event
            
    # If no current or next gameweek, return the first one
    return events[0] if events else {}


async def get_team_fixtures(team_id: int, include_finished: bool = False) -> List[Dict[str, Any]]:
    """
    Get upcoming fixtures for a specific team
    
    Args:
        team_id: Team ID in the FPL API
        include_finished: Whether to include finished fixtures
    
    Returns:
        List of fixture data for the specified team
    """
    all_fixtures = await get_fixtures_data()
    
    # Filter fixtures for the specified team
    team_fixtures = [
        fixture for fixture in all_fixtures 
        if fixture["team_a"] == team_id or fixture["team_h"] == team_id
    ]
    
    # Filter out finished fixtures if not needed
    if not include_finished:
        team_fixtures = [
            fixture for fixture in team_fixtures
            if fixture["finished"] == False
        ]
    
    # Add is_home flag and opponent ID
    for fixture in team_fixtures:
        fixture["is_home"] = fixture["team_h"] == team_id
        fixture["opponent"] = fixture["team_a"] if fixture["is_home"] else fixture["team_h"]
    
    return team_fixtures


async def get_fixture_difficulty() -> Dict[int, Dict[int, int]]:
    """
    Get fixture difficulty ratings for all teams
    
    Returns:
        Dictionary mapping team IDs to a dictionary of opponent team IDs and their difficulty rating
        Example: {1: {2: 4, 3: 2, ...}, 2: {1: 3, ...}}
    """
    teams = await get_teams()
    team_count = len(teams)
    fixtures = await get_fixtures_data()
    
    # Initialize difficulty matrix
    difficulty = {team["id"]: {} for team in teams}
    
    # Fill difficulty matrix from fixtures
    for fixture in fixtures:
        home_team = fixture["team_h"]
        away_team = fixture["team_a"]
        
        # Use FDR values from the API
        home_difficulty = fixture["team_h_difficulty"]
        away_difficulty = fixture["team_a_difficulty"]
        
        # Update difficulty matrix
        difficulty[home_team][away_team] = away_difficulty
        difficulty[away_team][home_team] = home_difficulty
    
    return difficulty


async def get_player_fixture_difficulty(player_id: int, next_n: int = 5) -> List[Dict[str, Any]]:
    """
    Get fixture difficulty for a player's upcoming fixtures
    
    Args:
        player_id: Player ID in the FPL API
        next_n: Number of upcoming fixtures to include
    
    Returns:
        List of fixture difficulties for the player
    """
    # Get player data to find their team
    player = await get_player_by_id(player_id)
    if not player:
        raise Exception(f"Player with ID {player_id} not found")
    
    team_id = player["team"]
    
    # Get upcoming fixtures for the team
    fixtures = await get_team_fixtures(team_id)
    
    # Get difficulty ratings
    difficulty_matrix = await get_fixture_difficulty()
    
    # Create result
    result = []
    for i, fixture in enumerate(fixtures[:next_n]):
        opponent_id = fixture["opponent"]
        opponent_team = await get_team_by_id(opponent_id)
        
        difficulty = difficulty_matrix[team_id].get(opponent_id, 3)  # Default to medium difficulty
        
        result.append({
            "gameweek": fixture["event"],
            "opponent": opponent_team["name"] if opponent_team else "Unknown",
            "is_home": fixture["is_home"],
            "difficulty": difficulty
        })
    
    return result


async def get_players_by_form(position: Optional[int] = None, 
                           limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get players sorted by form
    
    Args:
        position: Optional position filter (1=GK, 2=DEF, 3=MID, 4=FWD)
        limit: Maximum number of players to return
    
    Returns:
        List of players sorted by form
    """
    players = await get_players()
    
    # Apply position filter if specified
    if position is not None:
        players = [p for p in players if p["element_type"] == position]
    
    # Sort by form (descending)
    sorted_players = sorted(players, key=lambda p: float(p["form"]), reverse=True)
    
    return sorted_players[:limit]


async def get_players_by_points(position: Optional[int] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get players sorted by total points
    
    Args:
        position: Optional position filter (1=GK, 2=DEF, 3=MID, 4=FWD)
        limit: Maximum number of players to return
    
    Returns:
        List of players sorted by total points
    """
    players = await get_players()
    
    # Apply position filter if specified
    if position is not None:
        players = [p for p in players if p["element_type"] == position]
    
    # Sort by total points (descending)
    sorted_players = sorted(players, key=lambda p: p["total_points"], reverse=True)
    
    return sorted_players[:limit]


async def get_players_by_value(position: Optional[int] = None, 
                            limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get players sorted by value (points per cost)
    
    Args:
        position: Optional position filter (1=GK, 2=DEF, 3=MID, 4=FWD)
        limit: Maximum number of players to return
    
    Returns:
        List of players sorted by value
    """
    players = await get_players()
    
    # Apply position filter if specified
    if position is not None:
        players = [p for p in players if p["element_type"] == position]
    
    # Calculate value (points per cost) and filter out players with no cost
    players_with_value = []
    for player in players:
        if player["now_cost"] > 0:
            value = player["total_points"] / player["now_cost"]
            players_with_value.append({**player, "value": value})
    
    # Sort by value (descending)
    sorted_players = sorted(players_with_value, key=lambda p: p["value"], reverse=True)
    
    return sorted_players[:limit]


# Simple function for synchronous access to common data
def sync_get_data():
    """
    Get basic FPL data synchronously (for use in sync contexts)
    
    Returns:
        Dictionary containing basic FPL data
    """
    return asyncio.run(get_bootstrap_data())


if __name__ == "__main__":
    # Example usage
    async def main():
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        
        # Get all players
        players = await get_players()
        print(f"Total players: {len(players)}")
        
        # Get player by ID
        player = await get_player_by_id(1)
        if player:
            print(f"Player: {player['first_name']} {player['second_name']}")
        
        # Get team by ID
        team = await get_team_by_id(1)
        if team:
            print(f"Team: {team['name']}")
        
        # Get fixture difficulty
        difficulty = await get_fixture_difficulty()
        print(f"Fixture difficulty for team 1: {difficulty.get(1)}")
        
        # Get best players by form
        form_players = await get_players_by_form(limit=5)
        print("Top players by form:")
        for p in form_players:
            print(f"  {p['first_name']} {p['second_name']} - Form: {p['form']}")
    
    asyncio.run(main())
