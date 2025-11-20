from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.models.breed import BreedDetails

class MatchExplanation(BaseModel):
    category: str
    score: float
    reasoning: str

class BreedRecommendation(BaseModel):
    breed: BreedDetails
    match_score: float  # 0-100
    explanations: List[str]  # Simplified from MatchExplanation for easier frontend rendering
    pros: List[str]
    cons: List[str]
    
class RecommendationResponse(BaseModel):
    session_id: str
    top_three: List[BreedRecommendation]
    user_profile: Dict[str, Any]
    day_in_life_content: Optional[Dict[str, Any]] = None