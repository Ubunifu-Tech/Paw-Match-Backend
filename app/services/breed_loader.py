import pandas as pd
from typing import List, Dict
from pathlib import Path
from app.models.breed import BreedTraits

class BreedDataLoader:
    def __init__(self):
        self.data_dir = Path("app/data")
        self.breeds_df = None
        self.traits_df = None
        self.load_data()
    
    def load_data(self):
        """Load breed traits and trait descriptions"""
        self.breeds_df = pd.read_csv(self.data_dir / "breed_traits.csv")
        self.traits_df = pd.read_csv(self.data_dir / "trait_description.csv")
        
        # Clean column names
        self.breeds_df.columns = self.breeds_df.columns.str.strip()
        
    def get_all_breeds(self) -> List[str]:
        """Get list of all breed names"""
        return self.breeds_df['Breed'].tolist()
    
    def get_breed_traits(self, breed_name: str) -> BreedTraits:
        """Get traits for a specific breed"""
        breed_data = self.breeds_df[self.breeds_df['Breed'] == breed_name].iloc[0]
        
        return BreedTraits(
            breed=breed_data['Breed'],
            affectionate_with_family=int(breed_data['Affectionate With Family']),
            good_with_young_children=int(breed_data['Good With Young Children']),
            good_with_other_dogs=int(breed_data['Good With Other Dogs']),
            shedding_level=int(breed_data['Shedding Level']),
            coat_grooming_frequency=int(breed_data['Coat Grooming Frequency']),
            drooling_level=int(breed_data['Drooling Level']),
            coat_type=breed_data['Coat Type'],
            coat_length=breed_data['Coat Length'],
            openness_to_strangers=int(breed_data['Openness To Strangers']),
            playfulness_level=int(breed_data['Playfulness Level']),
            watchdog_protective_nature=int(breed_data['Watchdog/Protective Nature']),
            adaptability_level=int(breed_data['Adaptability Level']),
            trainability_level=int(breed_data['Trainability Level']),
            energy_level=int(breed_data['Energy Level']),
            barking_level=int(breed_data['Barking Level']),
            mental_stimulation_needs=int(breed_data['Mental Stimulation Needs'])
        )
    
    def get_all_breeds_data(self) -> pd.DataFrame:
        """Get the full breeds dataframe"""
        return self.breeds_df
    
    def get_trait_descriptions(self) -> Dict[str, Dict]:
        """Get trait descriptions for UI display"""
        descriptions = {}
        for _, row in self.traits_df.iterrows():
            descriptions[row['Trait']] = {
                'low': row['Trait_1'],
                'high': row['Trait_5'],
                'description': row['Description']
            }
        return descriptions