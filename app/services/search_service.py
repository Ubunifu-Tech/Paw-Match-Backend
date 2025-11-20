from google import genai
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Google Search integration for breed research from trusted sources"""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.client = gemini_service.client
        
    def search_breed_information(self, breed_name: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Search for breed information from trusted sources using Gemini grounding"""
        
        # Build search query based on user's specific concerns
        search_queries = [
            f"{breed_name} temperament and personality",
            f"{breed_name} living requirements and space needs",
        ]
        
        # Add specific queries based on user profile
        if user_profile.get('has_children'):
            search_queries.append(f"{breed_name} with children safety")
        
        if user_profile.get('allergies'):
            search_queries.append(f"{breed_name} hypoallergenic shedding")
            
        if user_profile.get('activity_level') in ['active', 'very_active']:
            search_queries.append(f"{breed_name} exercise requirements")
        
        # Use Gemini with Google Search grounding
        try:
            search_results = []
            for query in search_queries[:2]:  # Limit to 2 searches to avoid rate limits
                prompt = f"""Research the following about {breed_name} dogs from trusted sources like AKC, veterinary sites, and breed clubs:

Query: {query}

Provide a concise summary (2-3 sentences) with key facts. Focus on factual, authoritative information."""

                # Use Gemini with search grounding
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={
                        'tools': [{'google_search': {}}]  # Enable Google Search grounding
                    }
                )
                
                search_results.append({
                    'query': query,
                    'summary': response.text,
                    'grounding_metadata': self._extract_sources(response)
                })
            
            return {
                'breed': breed_name,
                'research': search_results,
                'sources_used': True
            }
            
        except Exception as e:
            logger.error(f"Search error for {breed_name}: {e}", exc_info=True)
            return {
                'breed': breed_name,
                'research': [],
                'sources_used': False,
                'error': str(e)
            }
    
    def _extract_sources(self, response) -> List[str]:
        """Extract source URLs from grounding metadata"""
        sources = []
        try:
            if hasattr(response, 'grounding_metadata'):
                for chunk in response.grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        sources.append({
                            'url': chunk.web.uri,
                            'title': chunk.web.title if hasattr(chunk.web, 'title') else ''
                        })
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not extract sources from response: {e}")
        return sources
    
    def enhance_recommendation_with_research(
        self, 
        breed_name: str, 
        match_score: float,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance a breed recommendation with web research"""
        
        research = self.search_breed_information(breed_name, user_profile)
        
        # Synthesize research into actionable insights
        if research.get('research'):
            insights_prompt = f"""Based on this research about {breed_name}:

{json.dumps(research['research'], indent=2)}

User profile: {json.dumps(user_profile, indent=2)}

Provide 3 key insights about why this breed is a {match_score:.0f}% match for this user. Be specific and reference the research."""

            insights = self.gemini.generate_text(insights_prompt)
            
            return {
                'breed': breed_name,
                'research_insights': insights,
                'sources': research.get('grounding_metadata', []),
                'research_available': True
            }
        
        return {
            'breed': breed_name,
            'research_available': False
        }
