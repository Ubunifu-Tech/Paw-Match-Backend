from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.recommendation import RecommendationResponse, BreedRecommendation
from app.services.matching_engine import MatchingEngine
from app.services.conversation_agent import ConversationAgent
from app.services.content_generator import ContentGenerator
from app.services.breed_service import BreedService
from app.services.image_service import ImageService
from app.services.search_service import SearchService
from app.core.dependencies import (
    get_matching_engine, 
    get_conversation_agent, 
    get_content_generator, 
    get_breed_service, 
    get_image_service,
    get_search_service,
    get_db
)
from app.core.security import get_current_user
from app.db.models import User, SavedResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/")
async def get_user_recommendations_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all saved recommendations for the current user"""
    result = await db.execute(
        select(SavedResult)
        .where(SavedResult.user_id == current_user.id)
        .order_by(SavedResult.created_at.desc())
    )
    saved_results = result.scalars().all()
    
    # Group by session_id
    sessions = {}
    for saved in saved_results:
        session_id = str(saved.session_id)
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "created_at": saved.created_at,
                "recommendations": []
            }
        sessions[session_id]["recommendations"].append({
            "breed_name": saved.breed_name,
            "match_score": float(saved.match_score),
            "rank": saved.rank,
            "images": saved.match_data.get("breed", {}).get("images", [])
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": list(sessions.values())
    }

@router.get("/{session_id}")
async def get_recommendations(
    session_id: str,
    use_search: bool = Query(default=False, description="Enable web search for trusted sources (slower)"),
    force_regenerate: bool = Query(default=False, description="Force regenerate recommendations"),
    agent: ConversationAgent = Depends(get_conversation_agent),
    matching_engine: MatchingEngine = Depends(get_matching_engine),
    content_gen: ContentGenerator = Depends(get_content_generator),
    breed_service: BreedService = Depends(get_breed_service),
    image_service: ImageService = Depends(get_image_service),
    search_service: SearchService = Depends(get_search_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top 3 breed recommendations with optional web search enhancement"""
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    
    # Check for existing saved results (unless force regenerate)
    if not force_regenerate:
        existing_results = await db.execute(
            select(SavedResult)
            .where(SavedResult.session_id == session_id)
            .order_by(SavedResult.rank)
        )
        saved_results = existing_results.scalars().all()
        
        if saved_results:
            # Return saved results - deduplicate by breed name (keep first occurrence)
            from app.models.breed import BreedDetails
            recommendations = []
            seen_breeds = set()
            
            for saved in saved_results:
                breed_name = saved.breed_name
                # Skip duplicates
                if breed_name in seen_breeds:
                    continue
                seen_breeds.add(breed_name)
                
                breed_data = saved.match_data["breed"]
                breed_details = BreedDetails(**breed_data)
                recommendations.append(BreedRecommendation(
                    breed=breed_details,
                    match_score=float(saved.match_score),
                    explanations=saved.match_data["explanations"],
                    pros=saved.match_data["pros"],
                    cons=saved.match_data["cons"]
                ))
                
                # Only return top 3 unique breeds
                if len(recommendations) >= 3:
                    break
            
            return {
                "session_id": session_id,
                "top_three": recommendations,
                "user_profile": saved_results[0].match_data.get("user_profile", {}),
                "day_in_life_content": saved_results[0].match_data.get("day_in_life_content"),
                "web_research": None,
                "data_source": "Saved results",
                "from_cache": True
            }

    user_profile = await agent.get_user_profile(session_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found for this session")
    
    # Get top matches from OUR dataset
    top_matches = await matching_engine.find_top_matches(user_profile, top_n=3)
    
    recommendations = []
    web_research = []
    
    for breed_name, score, explanations in top_matches:
        breed_traits = await breed_service.get_breed_traits(breed_name)
        pros, cons = matching_engine.generate_pros_cons(user_profile, breed_traits)
        images = await image_service.get_breed_images(breed_name, count=3)
        
        # Convert MatchExplanation objects to strings
        explanation_strings = [exp.reasoning for exp in explanations]
        
        # Extract just the URLs from image objects
        image_urls = [img["url"] for img in images]
        
        # Build BreedDetails object
        from app.models.breed import BreedDetails
        breed_details = BreedDetails(
            breed=breed_name,
            traits=breed_traits,
            images=image_urls
        )
        
        # Build recommendation from OUR data
        recommendation = BreedRecommendation(
            breed=breed_details,
            match_score=score,
            explanations=explanation_strings,
            pros=pros,
            cons=cons
        )
        recommendations.append(recommendation)
        
        # Optionally enhance with web search from trusted sources
        if use_search:
            research = search_service.enhance_recommendation_with_research(
                breed_name, 
                score, 
                user_profile.dict()
            )
            web_research.append(research)
    
    # Generate personalized content for top match with images
    top_breed_name = top_matches[0][0]
    top_breed_traits = await breed_service.get_breed_traits(top_breed_name)
    top_breed_images = await image_service.get_breed_images(top_breed_name, count=5)
    
    day_in_life = content_gen.generate_day_in_life(
        user_profile, 
        top_breed_name,
        top_breed_traits,
        breed_images=top_breed_images,
        selected_image_urls=None  # User can specify via separate endpoint
    )
    
    # Delete any existing saved results for this session to prevent duplicates
    existing_to_delete = await db.execute(
        select(SavedResult).where(SavedResult.session_id == session_id)
    )
    for old_result in existing_to_delete.scalars().all():
        await db.delete(old_result)
    await db.flush()  # Flush deletions before adding new ones
    
    # Save results to database for persistence
    for rank, recommendation in enumerate(recommendations, 1):
        saved_result = SavedResult(
            user_id=current_user.id,
            session_id=session_id,
            breed_name=recommendation.breed.breed,
            match_score=recommendation.match_score,
            rank=rank,
            match_data={
                "breed": recommendation.breed.dict(),
                "explanations": recommendation.explanations,
                "pros": recommendation.pros,
                "cons": recommendation.cons,
                "user_profile": user_profile.dict(),
                "day_in_life_content": day_in_life if rank == 1 else None
            }
        )
        db.add(saved_result)
    
    await db.commit()
    
    return {
        "session_id": session_id,
        "top_three": recommendations,
        "user_profile": user_profile.dict(),
        "day_in_life_content": day_in_life,
        "web_research": web_research if use_search else None,
        "data_source": "195 breeds from curated dataset + web research" if use_search else "195 breeds from curated dataset",
        "from_cache": False
    }