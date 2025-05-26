from typing import List, Optional
from pydantic import BaseModel


class Player(BaseModel):
    id: int
    name: str
    team: str
    position: str
    price: float
    total_points: int
    form: float
    minutes: int
    goals_scored: Optional[int] = 0
    assists: Optional[int] = 0
    clean_sheets: Optional[int] = 0
    goals_conceded: Optional[int] = 0
    own_goals: Optional[int] = 0
    penalties_saved: Optional[int] = 0
    penalties_missed: Optional[int] = 0
    yellow_cards: Optional[int] = 0
    red_cards: Optional[int] = 0
    saves: Optional[int] = 0
    bonus: Optional[int] = 0
    
    
class Team(BaseModel):
    players: List[Player]
    total_value: float
    remaining_budget: float


class TransferRecommendation(BaseModel):
    player_out: Player
    player_in: Player
    reasoning: str
    expected_point_impact: float
    

class CaptainPick(BaseModel):
    player: Player
    reasoning: str
    expected_points: float


class TeamScore(BaseModel):
    total_score: float
    areas_of_strength: List[str]
    areas_for_improvement: List[str]
    optimization_tips: List[str]
