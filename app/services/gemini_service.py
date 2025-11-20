from google import genai
from typing import Dict, Any, List, Optional
import os
import time

class GeminiService:
    """Gemini API wrapper for conversation and content generation
    
    Uses Gemini 2.0 Flash Experimental - Fast model optimized for speed.
    NOT using thinking/reasoning models (Gemini 2.0 Flash Thinking) as we 
    don't need deep reasoning for breed recommendations.
    """
    
    def __init__(self, api_key: str, breed_context: Optional[str] = None):
        self.client = genai.Client(api_key=api_key)
        # Using gemini-2.5-flash - latest stable Flash model
        self.model_name = 'gemini-2.5-flash'
        self.breed_context = breed_context  # Dataset context for grounding
        
    def generate_text(self, prompt: str, max_retries: int = 3) -> str:
        """Generate text response from Gemini 2.0 Flash with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                last_error = e
                print(f"Gemini error (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Don't retry on certain errors
                error_str = str(e).lower()
                if 'quota' in error_str or 'permission' in error_str or 'invalid' in error_str:
                    break
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1  # 1s, 2s, 4s
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        print(f"All retry attempts failed. Last error: {last_error}")
        return "I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    def extract_user_preferences(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Extract structured user preferences from conversation"""
        
        # Build conversation context
        context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation_history
        ])
        
        prompt = f"""Based on this conversation, extract the user's dog preferences in JSON format.

Conversation:
{context}

Extract the following information (use null if not mentioned):
- living_space: "apartment", "house", "condo", or "farm" (if they say "house" without specifying size, use "house")
- has_yard: true/false
- has_children: true/false
- children_age: "toddler", "school_age", or "teen"
- has_other_pets: true/false
- activity_level: Based on exercise description - "sedentary" (minimal activity), "moderate" (1-2 miles walk daily), "active" (3-5 miles daily), or "very_active" (5+ miles or running)
- dog_experience: "first_time", "some", or "experienced" (if they mention growing up with dogs or having had dogs, use "experienced")
- allergies: true/false
- grooming_tolerance: "low", "moderate", or "high"
- noise_tolerance: "quiet", "moderate", or "any"
- work_schedule: "home", "part_time", or "full_time"

IMPORTANT: Only extract information that is clearly stated in the conversation. Use null for anything not explicitly mentioned.
Return ONLY valid JSON, no other text."""

        response = self.generate_text(prompt)
        
        # Parse JSON response
        try:
            import json
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            parsed = json.loads(response)
            print(f"✓ Profile extracted: {parsed}")
            return parsed
        except Exception as e:
            print(f"✗ Profile extraction failed: {e}")
            print(f"  Raw response: {response[:200]}")
            return {}
    
    def generate_conversational_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict],
        current_profile: Dict[str, Any]
    ) -> str:
        """Generate natural conversational response grounded in dataset"""
        
        # Use full conversation history for better context (or last 15 for very long conversations)
        recent_history = conversation_history[-15:] if len(conversation_history) > 15 else conversation_history
        context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in recent_history
        ])
        
        # Build list of what we already know
        known_info = []
        info_map = {
            'living_space': 'Living space',
            'has_yard': 'Has yard',
            'has_children': 'Has children',
            'children_age': 'Children age',
            'has_other_pets': 'Has other pets',
            'activity_level': 'Activity level',
            'dog_experience': 'Dog experience',
            'allergies': 'Allergies',
            'grooming_tolerance': 'Grooming tolerance',
            'noise_tolerance': 'Noise tolerance',
            'work_schedule': 'Work schedule'
        }
        
        for key, label in info_map.items():
            value = current_profile.get(key)
            if value is not None and value != "":
                known_info.append(f"- {label}: {value}")
        
        known_info_str = "\n".join(known_info) if known_info else "None yet"
        
        # Build list of what we still need
        missing_info = []
        for key, label in info_map.items():
            if current_profile.get(key) is None or current_profile.get(key) == "":
                missing_info.append(f"- {label}")
        
        missing_info_str = "\n".join(missing_info) if missing_info else "All information gathered"
        
        # Add breed dataset context for grounding
        dataset_info = ""
        if self.breed_context:
            dataset_info = f"\n\nDATASET CONTEXT (for your reference only):\n{self.breed_context}\n"
        
        prompt = f"""You are a friendly dog breed recommendation assistant. Your goal is to learn about the user's lifestyle and preferences through natural conversation.

CRITICAL RULES:
1. Do NOT mention specific dog breeds in your responses
2. Do NOT ask about information you already have (see "INFORMATION ALREADY GATHERED" below)
3. Only ask about missing information (see "STILL NEED TO LEARN" below)
4. Ask ONE question at a time
5. Be conversational and friendly
{dataset_info}
FULL CONVERSATION HISTORY:
{context}

User's latest message: {user_message}

INFORMATION ALREADY GATHERED:
{known_info_str}

STILL NEED TO LEARN:
{missing_info_str}

Based on what you already know and what's still missing, respond naturally. If you have enough information (at least living space, activity level, and dog experience), acknowledge their answer and ask if there's anything else they'd like to share. Otherwise, ask about ONE missing piece of information.

Keep responses friendly, concise (2-3 sentences), and conversational. Do NOT repeat questions about information you already have."""

        return self.generate_text(prompt)
    
    def should_make_recommendation(
        self, 
        conversation_history: List[Dict],
        current_profile: Dict[str, Any]
    ) -> bool:
        """Determine if enough information has been gathered"""
        
        # Core required fields - must have all 3
        core_required = ['living_space', 'activity_level', 'dog_experience']
        core_gathered = sum(1 for field in core_required if current_profile.get(field))
        
        # Important optional fields - should have at least 2
        important_fields = ['has_children', 'has_yard', 'allergies', 'grooming_tolerance']
        important_gathered = sum(1 for field in important_fields if current_profile.get(field) is not None)
        
        # Need all core fields + at least 2 important fields + minimum 5 conversation turns
        return (core_gathered == 3 and 
                important_gathered >= 2 and 
                len(conversation_history) >= 5)
    
    def summarize_conversation(self, messages: List[Dict]) -> str:
        """
        Summarize older messages for context optimization.
        
        Reduces token usage by summarizing long conversations while
        maintaining important context.
        
        Args:
            messages (List[Dict]): Messages to summarize
            
        Returns:
            str: Conversation summary
        """
        if not messages:
            return ""
        
        context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        prompt = f"""Summarize this conversation between a user and a dog breed assistant. Focus on:
1. Key facts about the user's lifestyle (living space, family, activity level)
2. Important preferences mentioned (size, grooming, energy level)
3. Any specific requirements or constraints

Conversation:
{context}

Provide a concise summary (2-3 sentences) that captures the essential information."""

        return self.generate_text(prompt)
    
    def optimize_context(
        self, 
        messages: List[Dict], 
        summary: Optional[str] = None,
        keep_recent: int = 5
    ) -> tuple[Optional[str], List[Dict]]:
        """
        Optimize conversation context for token efficiency.
        
        Strategy:
        - If messages > 10: Summarize old messages, keep recent ones
        - If summary exists: Use it instead of old messages
        - Always keep the most recent messages
        
        Args:
            messages (List[Dict]): All messages
            summary (str): Existing summary (optional)
            keep_recent (int): Number of recent messages to keep
            
        Returns:
            tuple[Optional[str], List[Dict]]: (summary, recent_messages)
        """
        if len(messages) <= 10:
            # Short conversation, no optimization needed
            return None, messages
        
        # Split into old and recent
        old_messages = messages[:-keep_recent]
        recent_messages = messages[-keep_recent:]
        
        # Generate or use existing summary
        if not summary and old_messages:
            summary = self.summarize_conversation(old_messages)
        
        return summary, recent_messages