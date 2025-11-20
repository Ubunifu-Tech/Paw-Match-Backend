"""
Breed Research API Routes

Endpoints for comprehensive breed research with web search capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator
from typing import Optional, List
from app.services.breed_research import get_research_service
from app.services.usage_tracker import get_usage_tracker, UsageTracker
from app.core.security import get_current_user
from app.core.dependencies import get_db
from app.db.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


class BreedResearchRequest(BaseModel):
    """Request model for breed research"""
    breed_name: str
    user_query: Optional[str] = None
    include_health: bool = True
    include_costs: bool = True
    
    @validator('breed_name')
    def validate_breed_name(cls, v):
        """Validate breed name"""
        if not v or not v.strip():
            raise ValueError('Breed name cannot be empty')
        if len(v) > 100:
            raise ValueError('Breed name too long (max 100 characters)')
        return v.strip()
    
    @validator('user_query')
    def validate_user_query(cls, v):
        """Validate user query"""
        if v and len(v) > 500:
            raise ValueError('Query too long (max 500 characters)')
        return v.strip() if v else None


class BreedComparisonRequest(BaseModel):
    """Request model for breed comparison"""
    breed1: str
    breed2: str
    focus_areas: Optional[List[str]] = None


class SpecificQuestionRequest(BaseModel):
    """Request model for specific breed question"""
    breed_name: str
    question: str


@router.post("/breed")
async def research_breed(
    request: BreedResearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Research a dog breed with latest online information.
    
    **Authentication Required**
    
    **Rate Limit:** 5 requests per month per user
    
    **Features:**
    - Works for breeds in and out of our database
    - Uses AI with web search for up-to-date info
    - Comprehensive breed overview
    - Health, costs, and practical advice
    - Results cached for 24 hours
    
    **Example:**
    ```json
    {
        "breed_name": "Australian Shepherd",
        "user_query": "Are they good for apartments?",
        "include_health": true,
        "include_costs": true
    }
    ```
    """
    
    try:
        research_service = get_research_service()
        
        # Check cache first (doesn't count against quota)
        result = await research_service.research_breed(
            breed_name=request.breed_name,
            user_query=request.user_query,
            include_health=request.include_health,
            include_costs=request.include_costs,
            use_cache=True
        )
        
        # If from cache, return without tracking usage
        if result.get('from_cache'):
            logger.info(f"Returning cached research for {request.breed_name} (no quota used)")
            return {
                "breed_name": request.breed_name,
                "research": result.get("breed_research"),
                "provider": result.get("provider"),
                "model": result.get("model"),
                "from_cache": True
            }
        
        # Check and track usage (only for new API calls)
        tracker = get_usage_tracker(db)
        usage_info = await tracker.check_and_increment(
            user=current_user,
            api_type='research',
            endpoint='/research/breed'
        )
        
        if not result.get("success"):
            error_detail = result.get("error", "Research failed")
            error_type = result.get("error_type", "unknown")
            raise HTTPException(
                status_code=503 if error_type == "quota_error" else 500,
                detail=error_detail
            )
        
        return {
            "breed_name": request.breed_name,
            "research": result.get("breed_research"),
            "provider": result.get("provider"),
            "model": result.get("model"),
            "from_cache": False,
            "usage": usage_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Breed research error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Research service unavailable")


@router.post("/compare")
async def compare_breeds(request: BreedComparisonRequest):
    """
    Compare two dog breeds side-by-side.
    
    **Features:**
    - Detailed comparison across multiple dimensions
    - Latest breed information
    - Practical recommendations
    
    **Example:**
    ```json
    {
        "breed1": "Labrador Retriever",
        "breed2": "Golden Retriever",
        "focus_areas": ["temperament", "exercise", "family_compatibility"]
    }
    ```
    """
    
    try:
        research_service = get_research_service()
        
        result = await research_service.compare_breeds(
            breed1=request.breed1,
            breed2=request.breed2,
            focus_areas=request.focus_areas
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Comparison failed"))
        
        return {
            "breed1": request.breed1,
            "breed2": request.breed2,
            "comparison": result.get("breed_research"),
            "provider": result.get("provider")
        }
        
    except Exception as e:
        logger.error(f"Breed comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/question")
async def answer_breed_question(request: SpecificQuestionRequest):
    """
    Answer a specific question about a dog breed.
    
    **Features:**
    - Targeted answers to user questions
    - Up-to-date information
    - Expert advice
    
    **Example:**
    ```json
    {
        "breed_name": "Border Collie",
        "question": "How much exercise do they need daily?"
    }
    ```
    """
    
    try:
        research_service = get_research_service()
        
        result = await research_service.answer_specific_question(
            breed_name=request.breed_name,
            question=request.question
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Answer failed"))
        
        return {
            "breed_name": request.breed_name,
            "question": request.question,
            "answer": result.get("breed_research"),
            "provider": result.get("provider")
        }
        
    except Exception as e:
        logger.error(f"Breed question error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-check")
async def research_health_check():
    """Check if research service is configured"""
    research_service = get_research_service()
    
    return {
        "configured": True,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "has_key": research_service.gemini_key is not None
    }
