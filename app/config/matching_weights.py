"""
Matching Engine Weight Configuration

Centralized configuration for breed matching algorithm weights.
Allows easy tuning of the matching algorithm without code changes.

Author: PawMatch Team
Version: 1.0.0
"""

from typing import Dict


class MatchingWeights:
    """
    Configuration class for matching algorithm weights.
    
    All weights should sum to 100 for proper percentage calculations.
    Adjust these values to fine-tune the matching algorithm.
    """
    
    # Core compatibility weights (sum = 100)
    FAMILY_COMPATIBILITY = 20      # Weight for children/family factors
    ACTIVITY_LEVEL = 25            # Weight for energy/exercise match
    LIVING_SPACE = 15              # Weight for home size compatibility
    GROOMING_TOLERANCE = 15        # Weight for grooming needs match
    TRAINING_DIFFICULTY = 15       # Weight for trainability vs experience
    OTHER_PETS = 10                # Weight for compatibility with other pets
    
    # Penalty multipliers
    ALLERGY_PENALTY = 0.3          # Multiply score by this if allergies + high shedding
    
    # Activity level mappings (1-5 scale)
    ACTIVITY_LEVEL_MAP: Dict[str, int] = {
        "sedentary": 1,
        "moderate": 3,
        "active": 4,
        "very_active": 5
    }
    
    # Grooming tolerance mappings (1-5 scale)
    GROOMING_MAP: Dict[str, int] = {
        "low": 1,
        "moderate": 3,
        "high": 5
    }
    
    # Experience level to required trainability mapping
    EXPERIENCE_TRAINABILITY_MAP: Dict[str, int] = {
        "first_time": 4,      # Need highly trainable breeds
        "some": 3,            # Moderate trainability ok
        "experienced": 1      # Can handle any trainability level
    }
    
    # First-time owner penalty for low trainability
    FIRST_TIME_LOW_TRAIN_PENALTY = 0.7
    
    @classmethod
    def get_total_weight(cls) -> int:
        """
        Calculate total weight to verify it equals 100.
        
        Returns:
            int: Sum of all weights
        """
        return (
            cls.FAMILY_COMPATIBILITY +
            cls.ACTIVITY_LEVEL +
            cls.LIVING_SPACE +
            cls.GROOMING_TOLERANCE +
            cls.TRAINING_DIFFICULTY +
            cls.OTHER_PETS
        )
    
    @classmethod
    def validate_weights(cls) -> bool:
        """
        Validate that weights are properly configured.
        
        Returns:
            bool: True if weights sum to 100
            
        Raises:
            ValueError: If weights don't sum to 100
        """
        total = cls.get_total_weight()
        if total != 100:
            raise ValueError(
                f"Matching weights must sum to 100, currently sum to {total}. "
                f"Please adjust weights in matching_weights.py"
            )
        return True


# Validate weights on module load
MatchingWeights.validate_weights()
