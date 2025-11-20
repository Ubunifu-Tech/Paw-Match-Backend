from pydantic import BaseModel, Field
from typing import List, Optional

class VideoGenerationRequest(BaseModel):
    """Request model for video generation with image selection"""
    session_id: str
    breed_name: str
    selected_image_urls: Optional[List[str]] = Field(
        default=None, 
        max_length=2,
        description="Up to 2 image URLs selected by user (from breed images or uploaded)"
    )
    use_default_images: bool = Field(
        default=True,
        description="If true, use 2 random images from breed dataset"
    )

class VideoGenerationResponse(BaseModel):
    """Response model for video generation"""
    video_url: Optional[str] = None
    status: str  # "generating", "completed", "timeout", "error"
    operation_id: Optional[str] = None
    images_used: List[str] = []
    estimated_time: Optional[int] = None  # seconds
    message: str
