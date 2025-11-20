from pydantic import BaseModel
from typing import Optional, List

class BreedTraits(BaseModel):
    breed: str
    affectionate_with_family: int
    good_with_young_children: int
    good_with_other_dogs: int
    shedding_level: int
    coat_grooming_frequency: int
    drooling_level: int
    coat_type: str
    coat_length: str
    openness_to_strangers: int
    playfulness_level: int
    watchdog_protective_nature: int
    adaptability_level: int
    trainability_level: int
    energy_level: int
    barking_level: int
    mental_stimulation_needs: int

class BreedImage(BaseModel):
    url: str
    alt: str

class BreedDetails(BaseModel):
    breed: str
    traits: BreedTraits
    images: List[str] = []  # Changed to strings for simpler API
    description: Optional[str] = None