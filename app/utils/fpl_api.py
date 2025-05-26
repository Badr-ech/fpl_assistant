import httpx
from typing import Dict, List, Any, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

# FPL API URLs
BASE_URL = "https://fantasy.premierleague.com/api"
BOOTSTRAP_URL = f"{BASE_URL}/bootstrap-static/"
PLAYER_URL = f"{BASE_URL}/element-summary"
TEAM_URL = f"{BASE_URL}/entry"


async def get_fpl_data() -> Dict[str, Any]:
    """
    Get general FPL data including teams, players, and gameweeks
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BOOTSTRAP_URL, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching FPL data: {str(e)}")
        raise Exception(f"Failed to fetch FPL data: {str(e)}")


async def get_player_data(player_id: int) -> Dict[str, Any]:
    """
    Get detailed data for a specific player
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PLAYER_URL}/{player_id}/", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching player data for ID {player_id}: {str(e)}")
        raise Exception(f"Failed to fetch player data: {str(e)}")


async def get_team_data(team_id: int) -> Dict[str, Any]:
    """
    Get data for a specific FPL team
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TEAM_URL}/{team_id}/", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching team data for ID {team_id}: {str(e)}")
        raise Exception(f"Failed to fetch team data: {str(e)}")


async def get_team_players(team_id: int, gameweek: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get the players in a specific FPL team for a given gameweek
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get current gameweek if not specified
            if gameweek is None:
                bootstrap_data = await get_fpl_data()
                for gw in bootstrap_data["events"]:
                    if gw["is_current"]:
                        gameweek = gw["id"]
                        break
                
                if gameweek is None:
                    raise Exception("Could not determine current gameweek")
            
            response = await client.get(f"{TEAM_URL}/{team_id}/event/{gameweek}/picks/", timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching team players for team ID {team_id}: {str(e)}")
        raise Exception(f"Failed to fetch team players: {str(e)}")
