"""
Breed Research Service

Uses Google Gemini 2.0 Flash with web search for fast, up-to-date information
about dog breeds, including breeds not in our database.

Optimized for speed with Gemini 2.0 Flash (not reasoning models).
"""

import logging
from typing import Dict, Optional
from google import genai
from app.core.config import get_settings
from app.services.research_cache import get_research_cache

logger = logging.getLogger(__name__)
settings = get_settings()


class BreedResearchService:
    """
    Provides comprehensive breed research using Gemini 2.0 Flash.
    
    Features:
    - Web search for latest breed information
    - Fast responses (no deep reasoning needed)
    - Support for breeds not in database
    - Structured research responses
    """
    
    def __init__(self):
        """Initialize research service with Gemini API"""
        self.gemini_key = settings.gemini_api_key
        
        if self.gemini_key:
            self.client = genai.Client(api_key=self.gemini_key)
            logger.info("Initialized Gemini 2.0 Flash for breed research")
        else:
            logger.error("No Gemini API key configured")
            raise ValueError("GEMINI_API_KEY is required for breed research")
    
    async def research_breed(
        self, 
        breed_name: str,
        user_query: Optional[str] = None,
        include_health: bool = True,
        include_costs: bool = True,
        use_cache: bool = True
    ) -> Dict:
        """
        Research a dog breed with latest online information.
        
        Args:
            breed_name: Name of the breed to research
            user_query: Specific user question (optional)
            include_health: Include health information
            include_costs: Include cost estimates
            use_cache: Use cached results if available (default True)
            
        Returns:
            Dict with comprehensive breed research
        """
        
        # Check cache first
        if use_cache:
            cache = get_research_cache()
            cached_result = cache.get(
                breed_name=breed_name,
                query=user_query,
                include_health=include_health,
                include_costs=include_costs
            )
            
            if cached_result:
                logger.info(f"Returning cached research for: {breed_name}")
                cached_result['from_cache'] = True
                return cached_result
        
        # Build research prompt
        prompt = self._build_research_prompt(
            breed_name, 
            user_query, 
            include_health, 
            include_costs
        )
        
        # Get research from Gemini
        result = await self._research_with_gemini(prompt)
        
        # Cache successful results
        if result.get('success') and use_cache:
            cache = get_research_cache()
            cache.set(
                result=result,
                breed_name=breed_name,
                query=user_query,
                include_health=include_health,
                include_costs=include_costs
            )
        
        result['from_cache'] = False
        return result
    
    def _build_research_prompt(
        self, 
        breed_name: str, 
        user_query: Optional[str],
        include_health: bool,
        include_costs: bool
    ) -> str:
        """Build comprehensive research prompt"""
        
        base_prompt = f"""
Please research the dog breed: {breed_name}

Provide up-to-date, comprehensive information including:

1. **Overview**: Brief introduction to the breed
2. **Temperament**: Personality traits and behavior
3. **Physical Characteristics**: Size, appearance, coat type
4. **Exercise Needs**: Daily activity requirements
5. **Training**: Trainability and best practices
6. **Living Environment**: Best suited for apartments, houses, etc.
7. **Family Compatibility**: Good with children, other pets
"""
        
        if include_health:
            base_prompt += """
8. **Health Considerations**: Common health issues and lifespan
9. **Grooming Requirements**: Maintenance needs
"""
        
        if include_costs:
            base_prompt += """
10. **Cost Estimates**: Purchase price, annual maintenance costs
"""
        
        if user_query:
            base_prompt += f"""

**User's Specific Question**: {user_query}

Please address this question specifically in your response.
"""
        
        base_prompt += """

**IMPORTANT**: 
- Use your knowledge but verify with recent information (2023-2024)
- Cite breed clubs, veterinary sources when relevant
- If breed doesn't exist or is very rare, clearly state that
- Provide practical, actionable advice
- Use markdown formatting for readability

Format your response in clear sections with headers.
"""
        
        return base_prompt
    
    async def _research_with_gemini(self, prompt: str) -> Dict:
        """Research using Google Gemini 2.5 Flash - Fast and efficient"""
        
        try:
            # Use Gemini 2.5 Flash - latest stable, fast responses
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 2000,
                }
            )
            
            # Extract text from response
            text_content = response.text if hasattr(response, 'text') else str(response)
            
            return {
                "success": True,
                "breed_research": text_content,
                "provider": "gemini",
                "model": "gemini-2.5-flash"
            }
        
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Gemini research error: {str(e)}", exc_info=True)
            
            # Determine error type based on message content
            if 'permission' in error_str or 'auth' in error_str or 'credential' in error_str:
                return {
                    "success": False,
                    "error": "API authentication failed",
                    "error_type": "auth_error"
                }
            elif 'quota' in error_str or 'limit' in error_str or 'exhausted' in error_str:
                return {
                    "success": False,
                    "error": "API quota exceeded. Please try again later.",
                    "error_type": "quota_error"
                }
            elif 'invalid' in error_str or 'argument' in error_str:
                return {
                    "success": False,
                    "error": "Invalid research request",
                    "error_type": "invalid_request"
                }
            else:
                return {
                    "success": False,
                    "error": f"Research service temporarily unavailable: {type(e).__name__}",
                    "error_type": "unknown_error"
                }
    
    async def compare_breeds(
        self, 
        breed1: str, 
        breed2: str, 
        focus_areas: Optional[list] = None
    ) -> Dict:
        """
        Compare two breeds with latest information.
        
        Args:
            breed1: First breed name
            breed2: Second breed name
            focus_areas: Specific areas to compare (optional)
            
        Returns:
            Dict with detailed comparison
        """
        
        focus = focus_areas or ["temperament", "size", "exercise", "grooming", "family_compatibility"]
        focus_str = ", ".join(focus)
        
        prompt = f"""
Compare these two dog breeds: {breed1} vs {breed2}

Focus areas: {focus_str}

Provide a detailed comparison including:
1. Key similarities
2. Key differences
3. Which breed is better for specific situations (families, apartments, first-time owners, etc.)
4. Pros and cons of each
5. Latest breed standards and trends

Use a table format where appropriate for easy comparison.
"""
        
        return await self._research_with_gemini(prompt)
    
    async def answer_specific_question(
        self, 
        breed_name: str, 
        question: str
    ) -> Dict:
        """
        Answer a specific question about a breed.
        
        Args:
            breed_name: Breed name
            question: User's specific question
            
        Returns:
            Dict with answer
        """
        
        prompt = f"""
Dog Breed: {breed_name}
User Question: {question}

Please provide a comprehensive, accurate answer to this question about the {breed_name}.
Use recent information and cite sources when relevant.
Be specific and practical in your advice.
"""
        
        return await self._research_with_gemini(prompt)


# Singleton instance
_research_service = None

def get_research_service() -> BreedResearchService:
    """Get singleton research service instance"""
    global _research_service
    if _research_service is None:
        _research_service = BreedResearchService()
    return _research_service
