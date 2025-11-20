from typing import Dict, Any, List, Optional
import time
import random
import httpx
from google.genai import types
from app.services.gemini_service import GeminiService
from app.models.user_profile import UserProfile
from app.models.breed import BreedTraits

class ContentGenerator:
    def __init__(self, gemini_service: GeminiService):
        self.gemini = gemini_service
    
    def generate_day_in_life(
        self, 
        user_profile: UserProfile, 
        breed_name: str,
        breed_traits: BreedTraits,
        breed_images: Optional[List[Dict[str, str]]] = None,
        selected_image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate 'A Day in the Life' personalized content"""
        
        prompt = f"""Create a vivid, personalized "A Day in the Life with Your {breed_name}" story.

User Profile:
- Living space: {user_profile.living_space}
- Activity level: {user_profile.activity_level}
- Has children: {user_profile.has_children}
- Work schedule: {user_profile.work_schedule}

Breed Characteristics:
- Energy level: {breed_traits.energy_level}/5
- Playfulness: {breed_traits.playfulness_level}/5
- Affectionate: {breed_traits.affectionate_with_family}/5

Write a engaging narrative (200-300 words) describing a typical day with this breed, personalized to the user's lifestyle. Include:
- Morning routine
- Daytime activities
- Exercise/play time
- Evening wind-down

Make it vivid, emotional, and help them visualize life with this dog."""

        narrative = self.gemini.generate_text(prompt)
        
        # Generate care tips
        tips_prompt = f"""Generate 5 practical daily care tips for owning a {breed_name}, considering:
- Energy level: {breed_traits.energy_level}/5
- Grooming needs: {breed_traits.coat_grooming_frequency}/5
- Training needs: {breed_traits.trainability_level}/5

Format as a JSON array of strings."""

        tips_response = self.gemini.generate_text(tips_prompt)
        
        try:
            import json
            tips_response = tips_response.strip()
            if tips_response.startswith("```json"):
                tips_response = tips_response[7:]
            if tips_response.startswith("```"):
                tips_response = tips_response[3:]
            if tips_response.endswith("```"):
                tips_response = tips_response[:-3]
            tips = json.loads(tips_response.strip())
        except:
            tips = [
                "Provide daily exercise appropriate to energy level",
                "Establish consistent training routines",
                "Regular grooming and health checks",
                "Socialization with people and other dogs",
                "Mental stimulation through play and puzzles"
            ]
        
        # Generate social media caption
        social_prompt = f"""Create an engaging Instagram/TikTok caption for someone who just discovered their perfect dog match: {breed_name}.

Make it fun, relatable, and shareable. Include relevant emojis. Keep it under 150 characters."""

        social_caption = self.gemini.generate_text(social_prompt)
        
        # Determine which images to use for video generation
        images_for_video = selected_image_urls
        if not images_for_video and breed_images:
            # Use 2 random images from the breed dataset
            random.seed(breed_name)  # Consistent selection
            available_images = [img['url'] for img in breed_images]
            images_for_video = random.sample(available_images, min(2, len(available_images)))
            random.seed()  # Reset seed
        
        # DISABLED: Video generation takes 60+ seconds and blocks the response
        # TODO: Move to async background job or separate endpoint
        # video_result = self.generate_day_in_life_video(
        #     user_profile, 
        #     breed_name, 
        #     breed_traits,
        #     image_urls=images_for_video
        # )
        
        return {
            'narrative': narrative,
            'daily_tips': tips,
            'social_caption': social_caption.strip(),
            'breed_name': breed_name,
            'video_generation': None  # Disabled for performance
        }
    
    def generate_day_in_life_video(
        self,
        user_profile: UserProfile,
        breed_name: str,
        breed_traits: BreedTraits,
        image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate 'A Day in the Life' video using Veo with breed images
        
        Args:
            user_profile: User's preferences
            breed_name: Name of the breed
            breed_traits: Breed characteristics
            image_urls: List of 1-2 image URLs to use (default: None, will use random from dataset)
            
        Returns:
            Dict with video_url, images_used, and status
        """
        try:
            video_prompt = f"""Create a heartwarming 'A Day in the Life with Your {breed_name}' video showing:
            
- Morning: Owner waking up with their {breed_name}, playful morning energy
- Midday: {breed_name} playing {'with children' if user_profile.has_children else 'in the yard'}, showing affectionate behavior
- Afternoon: {'Active outdoor adventure' if user_profile.activity_level in ['active', 'very_active'] else 'Relaxing at home'}
- Evening: Cozy wind-down, {breed_name} cuddling with family

Style: Warm, cinematic, family-friendly. Show the dog's personality - energy level {breed_traits.energy_level}/5, playfulness {breed_traits.playfulness_level}/5.
Duration: 5-8 seconds. Include natural ambient sounds. Animate the dog naturally."""

            # Prepare image references (limit to 2 for cost control)
            images_to_use = image_urls[:2] if image_urls else []
            
            # Generate video with image references
            if images_to_use:
                print(f"Generating video for {breed_name} with {len(images_to_use)} reference images")
                
                # Download the first image to pass as bytes (Veo doesn't support direct HTTP URLs)
                try:
                    response = httpx.get(images_to_use[0], timeout=10.0)
                    response.raise_for_status()
                    image_bytes = response.content
                    
                    # Create Image object with bytes
                    image_obj = types.Image(
                        image_bytes=image_bytes,
                        mime_type='image/jpeg'
                    )
                    
                    # Generate with image reference
                    operation = self.gemini.client.models.generate_videos(
                        model="veo-3.1-fast-generate-preview",
                        prompt=video_prompt,
                        image=image_obj
                    )
                except Exception as img_error:
                    print(f"Warning: Could not load image {images_to_use[0]}: {img_error}")
                    print("Falling back to text-only generation")
                    # Fallback to text-only
                    operation = self.gemini.client.models.generate_videos(
                        model="veo-3.1-fast-generate-preview",
                        prompt=video_prompt
                    )
            else:
                # Text-only generation (fallback)
                print(f"Generating video for {breed_name} from text prompt only")
                operation = self.gemini.client.models.generate_videos(
                    model="veo-3.1-fast-generate-preview",
                    prompt=video_prompt
                )
            
            # Poll for completion (with timeout)
            max_wait = 60  # 60 seconds max
            start_time = time.time()
            
            print(f"Video generation started for {breed_name}: {operation.name}")
            
            # Poll until done (done will be True when complete, None/False while processing)
            while operation.done is not True and (time.time() - start_time) < max_wait:
                elapsed = int(time.time() - start_time)
                print(f"Generating video for {breed_name}... ({elapsed}s elapsed)")
                time.sleep(5)
                # Pass the operation object itself, not the name string
                operation = self.gemini.client.operations.get(operation)
            
            if operation.done is True and operation.response:
                generated_video = operation.response.generated_videos[0]
                video_uri = generated_video.video.uri
                print(f"✅ Video generated for {breed_name}: {video_uri}")
                return {
                    'video_url': video_uri,
                    'images_used': images_to_use,
                    'status': 'completed',
                    'operation_id': operation.name
                }
            else:
                print(f"⏳ Video generation timeout for {breed_name} after {max_wait}s")
                print(f"   Operation: {operation.name} (can be retrieved later)")
                return {
                    'video_url': None,
                    'images_used': images_to_use,
                    'status': 'timeout',
                    'operation_id': operation.name
                }
                
        except Exception as e:
            print(f"Error generating video: {e}")
            # Video is bonus feature, don't fail if it doesn't work
            return {
                'video_url': None,
                'images_used': [],
                'status': 'error',
                'error': str(e)
            }

    async def check_video_generation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation operation.
        
        Args:
            operation_id (str): The ID of the operation to check.
            
        Returns:
            Dict[str, Any]: A dictionary containing the status of the operation.
        """
        try:
            operation = self.gemini.client.operations.get(operation_id)
            
            if operation.done is True and operation.response:
                generated_video = operation.response.generated_videos[0]
                return {
                    "status": "completed",
                    "video_url": generated_video.video.uri,
                    "operation_id": operation_id
                }
            else:
                return {
                    "status": "processing",
                    "video_url": None,
                    "operation_id": operation_id,
                    "message": "Video is still generating. Please check again in a few seconds."
                }
        except Exception as e:
            return {
                "status": "error",
                "video_url": None,
                "operation_id": operation_id,
                "message": f"Failed to check status: {str(e)}"
            }