"""
Direct test of video generation without RQ worker
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gemini_service import GeminiService
from app.services.content_generator import ContentGenerator
from app.models.user_profile import UserProfile
from app.models.breed import BreedTraits
from app.core.config import get_settings

settings = get_settings()

# Create test data
user_profile = UserProfile(
    living_space="house",
    has_yard=True,
    family_members=3,
    has_children=True,
    has_other_pets=False,
    work_schedule="full_time",
    activity_level="moderate",
    experience_level="intermediate"
)

breed_traits = BreedTraits(
    breed="Labrador Retriever",
    affectionate_with_family=5,
    good_with_young_children=5,
    good_with_other_dogs=4,
    shedding_level=4,
    coat_grooming_frequency=2,
    drooling_level=3,
    coat_type="Double",
    coat_length="Short",
    openness_to_strangers=5,
    playfulness_level=5,
    watchdog_protective_nature=3,
    adaptability_level=5,
    trainability_level=5,
    energy_level=4,
    barking_level=3,
    mental_stimulation_needs=4
)

image_urls = [
    "https://storage.googleapis.com/dawg-match/breed_images/retrievers_labrador/retrievers_labrador_001.jpg",
    "https://storage.googleapis.com/dawg-match/breed_images/retrievers_labrador/retrievers_labrador_002.jpg"
]

print("Initializing Gemini service...")
gemini_service = GeminiService(api_key=settings.gemini_api_key)

print("Initializing content generator...")
generator = ContentGenerator(gemini_service=gemini_service)

print("\n🎬 Starting video generation...")
print("⏰ This will take approximately 60-90 seconds...\n")

try:
    result = generator.generate_day_in_life_video(
        user_profile=user_profile,
        breed_name="Labrador Retriever",
        breed_traits=breed_traits,
        image_urls=image_urls
    )
    
    print("✅ VIDEO GENERATION SUCCESSFUL!\n")
    print(f"Video URL: {result.get('video_url', 'N/A')}")
    print(f"Thumbnail: {result.get('thumbnail', 'N/A')}")
    print(f"Duration: {result.get('duration', 'N/A')}")
    print(f"\nFull result: {result}")
    
except Exception as e:
    print(f"❌ VIDEO GENERATION FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
