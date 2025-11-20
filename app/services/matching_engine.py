"""
Matching Engine Module

This module implements the core breed matching algorithm that calculates
compatibility scores between user preferences and dog breed characteristics.
Uses a sophisticated weighted scoring system across multiple dimensions.

Classes:
    MatchingEngine: Main engine for breed-user compatibility matching

Author: PawMatch Team
Version: 1.0.0
"""

import numpy as np
from typing import List, Tuple, Dict
from app.models.user_profile import UserProfile
from app.models.breed import BreedTraits
from app.models.recommendation import BreedRecommendation, MatchExplanation
from app.services.breed_service import BreedService
from app.config.matching_weights import MatchingWeights


class MatchingEngine:
    """
    Calculates compatibility scores between users and dog breeds.
    
    The matching engine uses a weighted scoring algorithm that considers:
    - Family compatibility (20% weight)
    - Activity/energy level match (25% weight)
    - Living space compatibility (15% weight)
    - Grooming requirements (10% weight)
    - Training difficulty (15% weight)
    - Other factors (shedding, noise, etc.)
    
    Attributes:
        breed_service (BreedService): Database service for accessing breed data
        
    Example:
        >>> engine = MatchingEngine()
        >>> matches = await engine.find_top_matches(user_profile, top_n=3)
        >>> print(f"Top match: {matches[0][0]} with {matches[0][1]}% compatibility")
    """
    
    def __init__(self):
        """
        Initialize the matching engine.
        """
        self.breed_service = BreedService()
        
    def calculate_match_score(
        self, 
        user_profile: UserProfile, 
        breed_traits: BreedTraits
    ) -> Tuple[float, List[MatchExplanation]]:
        """
        Calculate compatibility score between user and breed.
        
        Evaluates multiple dimensions of compatibility using weighted scoring:
        - Family needs (children, pets)
        - Lifestyle match (activity, space, schedule)
        - Practical considerations (grooming, training, allergies)
        
        Args:
            user_profile (UserProfile): User's preferences and lifestyle
            breed_traits (BreedTraits): Dog breed characteristics
            
        Returns:
            Tuple[float, List[MatchExplanation]]: 
                - Match score (0-100)
                - List of category-specific explanations
                
        Example:
            >>> score, explanations = engine.calculate_match_score(profile, traits)
            >>> print(f"Match: {score:.1f}%")
            >>> for exp in explanations:
            ...     print(f"{exp.category}: {exp.score}%")
        """
        
        score = 0.0
        max_score = 0.0
        explanations = []
        
        # Family compatibility
        if user_profile.has_children:
            weight = MatchingWeights.FAMILY_COMPATIBILITY
            max_score += weight
            child_score = breed_traits.good_with_young_children / 5.0
            score += child_score * weight
            explanations.append(MatchExplanation(
                category="Family Compatibility",
                score=child_score * 100,
                reasoning=f"{'Excellent' if child_score > 0.8 else 'Good' if child_score > 0.6 else 'Moderate'} with children"
            ))
        
        # Activity level match
        if user_profile.activity_level:
            weight = MatchingWeights.ACTIVITY_LEVEL
            max_score += weight
            user_energy = MatchingWeights.ACTIVITY_LEVEL_MAP.get(user_profile.activity_level, 3)
            energy_diff = abs(user_energy - breed_traits.energy_level)
            energy_score = max(0, 1 - (energy_diff / 4))
            score += energy_score * weight
            explanations.append(MatchExplanation(
                category="Energy Level Match",
                score=energy_score * 100,
                reasoning=f"Breed energy level ({breed_traits.energy_level}/5) matches your {user_profile.activity_level} lifestyle"
            ))
        
        # Living space compatibility
        if user_profile.living_space:
            weight = MatchingWeights.LIVING_SPACE
            max_score += weight
            space_score = self._calculate_space_compatibility(
                user_profile.living_space,
                breed_traits.adaptability_level,
                breed_traits.energy_level
            )
            score += space_score * weight
            # Format living space text nicely
            space_text = {
                "apartment": "apartments",
                "house_small": "small houses",
                "house_large": "large houses",
                "farm": "farms"
            }.get(user_profile.living_space, user_profile.living_space.replace('_', ' '))
            
            explanations.append(MatchExplanation(
                category="Living Space",
                score=space_score * 100,
                reasoning=f"Suitable for {space_text}"
            ))
        
        # Grooming & maintenance
        if user_profile.grooming_tolerance:
            weight = MatchingWeights.GROOMING_TOLERANCE
            max_score += weight
            user_grooming = MatchingWeights.GROOMING_MAP.get(user_profile.grooming_tolerance, 3)
            grooming_diff = abs(user_grooming - breed_traits.coat_grooming_frequency)
            grooming_score = max(0, 1 - (grooming_diff / 4))
            score += grooming_score * weight
            explanations.append(MatchExplanation(
                category="Grooming Needs",
                score=grooming_score * 100,
                reasoning=f"Grooming frequency matches your tolerance level"
            ))
        
        # Trainability for experience level
        if user_profile.dog_experience:
            weight = MatchingWeights.TRAINING_DIFFICULTY
            max_score += weight
            required_trainability = MatchingWeights.EXPERIENCE_TRAINABILITY_MAP.get(user_profile.dog_experience, 3)
            train_score = breed_traits.trainability_level / 5.0
            if user_profile.dog_experience == "first_time":
                train_score = train_score if breed_traits.trainability_level >= 4 else train_score * MatchingWeights.FIRST_TIME_LOW_TRAIN_PENALTY
            score += train_score * weight
            explanations.append(MatchExplanation(
                category="Training Difficulty",
                score=train_score * 100,
                reasoning=f"Suitable for {user_profile.dog_experience.replace('_', ' ')} owners"
            ))
        
        # Allergy considerations (deal-breaker)
        if user_profile.allergies and breed_traits.shedding_level > 3:
            score *= MatchingWeights.ALLERGY_PENALTY
            explanations.append(MatchExplanation(
                category="Allergy Concern",
                score=30.0,
                reasoning="High shedding may trigger allergies"
            ))
        
        # Other pets compatibility
        if user_profile.has_other_pets:
            weight = MatchingWeights.OTHER_PETS
            max_score += weight
            pet_score = breed_traits.good_with_other_dogs / 5.0
            score += pet_score * weight
            explanations.append(MatchExplanation(
                category="Pet Compatibility",
                score=pet_score * 100,
                reasoning=f"{'Great' if pet_score > 0.8 else 'Good'} with other pets"
            ))
        
        # Normalize score to 0-100
        if max_score > 0:
            final_score = (score / max_score) * 100
        else:
            final_score = 50.0  # Default if no criteria matched
        
        return final_score, explanations
    
    def _calculate_space_compatibility(
        self, 
        living_space: str, 
        adaptability: int, 
        energy: int
    ) -> float:
        """Calculate how well a breed fits the living space"""
        space_scores = {
            "apartment": 1.0 if adaptability >= 4 and energy <= 3 else 0.6,
            "house_small": 0.8 if energy <= 4 else 0.6,
            "house_large": 1.0,
            "farm": 1.0
        }
        return space_scores.get(living_space, 0.7)
    
    async def find_top_matches(
        self, 
        user_profile: UserProfile, 
        top_n: int = 3
    ) -> List[Tuple[str, float, List[MatchExplanation]]]:
        """Get top N breed matches for user profile"""
        
        all_breeds = await self.breed_service.get_all_breeds()
        matches = []
        seen_breeds = set()
        
        for breed_name in all_breeds:
            # Skip duplicates (shouldn't happen but safety check)
            if breed_name in seen_breeds:
                continue
            seen_breeds.add(breed_name)
            
            breed_traits = await self.breed_service.get_breed_traits(breed_name)
            if breed_traits:  # Only process if traits found
                score, explanations = self.calculate_match_score(user_profile, breed_traits)
                matches.append((breed_name, score, explanations))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Ensure we only return unique breeds (double-check)
        unique_matches = []
        unique_breed_names = set()
        for match in matches:
            if match[0] not in unique_breed_names:
                unique_breed_names.add(match[0])
                unique_matches.append(match)
                if len(unique_matches) >= top_n:
                    break
        
        return unique_matches
    
    def generate_pros_cons(
        self, 
        user_profile: UserProfile, 
        breed_traits: BreedTraits
    ) -> Tuple[List[str], List[str]]:
        """Generate pros and cons for a breed match"""
        
        pros = []
        cons = []
        
        # Energy level
        if user_profile.activity_level == "very_active" and breed_traits.energy_level >= 4:
            pros.append("High energy matches your active lifestyle")
        elif user_profile.activity_level == "sedentary" and breed_traits.energy_level <= 2:
            pros.append("Low energy, perfect for relaxed lifestyle")
        
        # Family friendly
        if breed_traits.good_with_young_children >= 4:
            pros.append("Excellent with children")
        elif breed_traits.good_with_young_children <= 2:
            cons.append("May not be ideal for young children")
        
        # Trainability
        if breed_traits.trainability_level >= 4:
            pros.append("Easy to train")
        elif breed_traits.trainability_level <= 2:
            cons.append("Can be stubborn, needs experienced handler")
        
        # Grooming
        if breed_traits.coat_grooming_frequency <= 2:
            pros.append("Low maintenance grooming")
        elif breed_traits.coat_grooming_frequency >= 4:
            cons.append("Requires frequent grooming")
        
        # Shedding
        if breed_traits.shedding_level <= 2:
            pros.append("Minimal shedding")
        elif breed_traits.shedding_level >= 4:
            cons.append("Heavy shedding")
        
        # Affectionate
        if breed_traits.affectionate_with_family >= 4:
            pros.append("Very affectionate and loving")
        
        # Adaptability
        if breed_traits.adaptability_level >= 4:
            pros.append("Highly adaptable to changes")
        
        return pros, cons