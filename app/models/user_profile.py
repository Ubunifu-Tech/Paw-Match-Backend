from pydantic import BaseModel
from typing import Optional, List

class UserProfile(BaseModel):
    # Living Situation
    living_space: Optional[str] = None  # "apartment", "house_small", "house_large", "farm"
    has_yard: Optional[bool] = None
    
    # Family & Lifestyle
    family_members: Optional[int] = None
    has_children: Optional[bool] = None
    children_age: Optional[str] = None  # "toddler", "school_age", "teen"
    has_other_pets: Optional[bool] = None
    
    # Activity Level
    activity_level: Optional[str] = None  # "sedentary", "moderate", "active", "very_active"
    exercise_time: Optional[str] = None  # "minimal", "30min", "1hour", "2plus_hours"
    
    # Experience & Preferences
    dog_experience: Optional[str] = None  # "first_time", "some", "experienced"
    training_commitment: Optional[str] = None  # "low", "moderate", "high"
    
    # Practical Considerations
    allergies: Optional[bool] = None
    grooming_tolerance: Optional[str] = None  # "low", "moderate", "high"
    noise_tolerance: Optional[str] = None  # "quiet", "moderate", "any"
    
    # Personality Preferences
    desired_traits: List[str] = []  # ["affectionate", "playful", "protective", etc.]
    deal_breakers: List[str] = []
    
    # Additional Context
    work_schedule: Optional[str] = None  # "home", "part_time", "full_time"
    budget: Optional[str] = None  # "low", "moderate", "high"