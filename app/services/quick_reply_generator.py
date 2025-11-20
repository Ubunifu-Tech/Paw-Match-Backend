"""
Quick Reply Generator

Generates context-aware quick reply suggestions for chat conversations.
More robust than keyword matching - uses conversation state and AI context.

Author: PawMatch Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any


class QuickReplyGenerator:
    """
    Generates suggested quick replies based on conversation context.
    
    This eliminates brittle keyword matching on the frontend by having
    the backend (which knows the conversation state) suggest appropriate actions.
    """
    
    # Quick reply templates by conversation topic
    LIVING_SPACE_REPLIES = [
        "Apartment",
        "House with yard",
        "Large property"
    ]
    
    ACTIVITY_LEVEL_REPLIES = [
        "Very active",
        "Moderately active",
        "Low activity"
    ]
    
    CHILDREN_REPLIES = [
        "Yes, young children",
        "Yes, older children",
        "No children"
    ]
    
    EXPERIENCE_REPLIES = [
        "First-time owner",
        "Some experience",
        "Very experienced"
    ]
    
    GROOMING_REPLIES = [
        "Minimal grooming",
        "Moderate grooming",
        "High maintenance OK"
    ]
    
    YES_NO_REPLIES = [
        "Yes",
        "No"
    ]
    
    GENERIC_REPLIES = [
        "Tell me more",
        "Skip this",
        "Find matches now"
    ]
    
    @classmethod
    def generate_from_profile_gaps(
        cls,
        user_profile: Dict[str, Any],
        last_ai_message: str
    ) -> Optional[List[str]]:
        """
        Generate quick replies based on what information is still needed.
        
        Args:
            user_profile: Current user profile data
            last_ai_message: The AI's last message to the user
            
        Returns:
            List of suggested quick reply strings, or None if conversation complete
        """
        # Check what's missing from profile and suggest accordingly
        message_lower = last_ai_message.lower()
        
        # Living space question
        if not user_profile.get('living_space'):
            if any(keyword in message_lower for keyword in [
                'living space', 'home', 'apartment', 'house', 'property', 'live', 'space'
            ]):
                return cls.LIVING_SPACE_REPLIES
        
        # Activity level question
        if not user_profile.get('activity_level'):
            if any(keyword in message_lower for keyword in [
                'activity', 'active', 'exercise', 'energy', 'lifestyle', 'walks', 'hiking'
            ]):
                return cls.ACTIVITY_LEVEL_REPLIES
        
        # Children question
        if user_profile.get('has_children') is None:
            if any(keyword in message_lower for keyword in [
                'children', 'kids', 'family', 'child', 'young', 'baby'
            ]):
                return cls.CHILDREN_REPLIES
        
        # Experience question
        if not user_profile.get('dog_experience'):
            if any(keyword in message_lower for keyword in [
                'experience', 'owned', 'first time', 'beginner', 'novice', 'expert'
            ]):
                return cls.EXPERIENCE_REPLIES
        
        # Grooming question
        if not user_profile.get('grooming_tolerance'):
            if any(keyword in message_lower for keyword in [
                'grooming', 'brushing', 'maintenance', 'shedding', 'coat', 'fur'
            ]):
                return cls.GROOMING_REPLIES
        
        # Yes/No questions (allergies, other pets, time commitment, etc.)
        if any(keyword in message_lower for keyword in [
            'do you have', 'are you', 'will you', 'can you', 'have you'
        ]) and '?' in last_ai_message:
            return cls.YES_NO_REPLIES
        
        # Default fallback - generic helpful actions
        return cls.GENERIC_REPLIES
    
    @classmethod
    def generate_from_completion_status(
        cls,
        is_complete: bool,
        profile_completeness: float
    ) -> Optional[List[str]]:
        """
        Generate quick replies based on conversation completion status.
        
        Args:
            is_complete: Whether conversation is marked complete
            profile_completeness: How complete the profile is (0.0-1.0)
            
        Returns:
            List of suggested actions or None
        """
        if is_complete:
            # Conversation done - no more quick replies needed
            return None
        
        if profile_completeness >= 0.8:
            # Almost done - suggest completion
            return ["Find my matches", "Continue chatting", "Start over"]
        
        # Still gathering info
        return cls.GENERIC_REPLIES
