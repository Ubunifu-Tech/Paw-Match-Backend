from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from app.models.video import VideoGenerationRequest, VideoGenerationResponse
from app.services.content_generator import ContentGenerator
from app.services.breed_service import BreedService
from app.services.conversation_agent import ConversationAgent
from app.core.dependencies import (
    get_content_generator,
    get_breed_service,
    get_conversation_agent
)
from app.core.security import get_current_user
from app.db.models import User

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_custom_video(
    session_id: str = Form(...),
    breed_name: str = Form(...),
    selected_image_urls: Optional[List[str]] = Form(default=None, max_length=2),
    content_gen: ContentGenerator = Depends(get_content_generator),
    breed_service: BreedService = Depends(get_breed_service),
    agent: ConversationAgent = Depends(get_conversation_agent),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a custom 'Day in the Life' video with user-selected images
    
    - **session_id**: User's session ID
    - **breed_name**: Name of the breed
    - **selected_image_urls**: Up to 2 image URLs (from breed images or uploaded)
    """
    
    # Validate session
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    user_profile = await agent.get_user_profile(session_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found for this session")
    
    # Validate breed
    breed_traits = await breed_service.get_breed_traits(breed_name)
    if not breed_traits:
        raise HTTPException(status_code=404, detail=f"Breed not found: {breed_name}")
    
    # Limit to 2 images for cost control
    if selected_image_urls and len(selected_image_urls) > 2:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 2 images allowed for video generation"
        )
    
    # Generate video
    try:
        video_result = content_gen.generate_day_in_life_video(
            user_profile=user_profile,
            breed_name=breed_name,
            breed_traits=breed_traits,
            image_urls=selected_image_urls
        )
        
        return VideoGenerationResponse(
            video_url=video_result.get('video_url'),
            status=video_result.get('status', 'unknown'),
            operation_id=video_result.get('operation_id'),
            images_used=video_result.get('images_used', []),
            estimated_time=60 if video_result.get('status') == 'generating' else None,
            message=f"Video generation {video_result.get('status')} for {breed_name}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/status/{operation_id}")
async def check_video_status(
    operation_id: str,
    content_gen: ContentGenerator = Depends(get_content_generator),
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of a video generation operation
    
    - **operation_id**: The operation ID returned from video generation
    """
    try:
        video_status = await content_gen.check_video_generation_status(operation_id)
        return video_status
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")
