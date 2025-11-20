"""
Comprehensive Matching Algorithm Accuracy Tests

Tests the matching engine with various realistic user scenarios to ensure
recommendations are accurate and make sense.

Author: PawMatch Team
"""

import pytest
from app.services.matching_engine import MatchingEngine
from app.services.breed_service import BreedService
from app.models.user_profile import UserProfile


class TestMatchingAccuracy:
    """Test matching algorithm with real-world scenarios"""
    
    @pytest.fixture
    def engine(self):
        """Create matching engine instance"""
        return MatchingEngine()
    
    @pytest.fixture
    def breed_service(self):
        """Create breed service instance"""
        return BreedService()
    
    @pytest.mark.asyncio
    async def test_young_family_with_children(self, engine, breed_service):
        """
        Scenario: Young family with small children in suburban home
        Expected: Family-friendly, gentle, patient breeds (Golden Retriever, Labrador, Beagle)
        """
        user_profile = UserProfile(
            has_children=True,
            activity_level="moderate",
            living_space="house_with_yard",
            experience_level="first_time",
            time_availability="moderate",
            grooming_tolerance="moderate",
            has_other_pets=False,
            has_allergies=False
        )
        
        # Get top 10 matches to analyze
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        
        # Extract breed names
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== Young Family with Children ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Verify family-friendly breeds are recommended
        family_friendly_breeds = [
            "Golden Retrievers", "Labrador Retrievers", "Beagles", 
            "Cavalier King Charles Spaniels", "Poodles", "Bulldogs"
        ]
        
        # At least 2 of top 5 should be family-friendly
        top_5_breeds = breed_names[:5]
        family_matches = [b for b in top_5_breeds if any(fb in b for fb in family_friendly_breeds)]
        
        assert len(family_matches) >= 2, \
            f"Expected at least 2 family-friendly breeds in top 5, got {family_matches}"
        
        # Score should be reasonable (>60%)
        assert top_matches[0][1] > 60, \
            f"Top match score too low: {top_matches[0][1]:.1f}%"
    
    @pytest.mark.asyncio
    async def test_active_single_apartment_dweller(self, engine, breed_service):
        """
        Scenario: Active single person in apartment, wants running partner
        Expected: Medium-sized active breeds that adapt to apartments (Border Collie, Australian Shepherd)
        """
        user_profile = UserProfile(
            has_children=False,
            activity_level="very_active",
            living_space="apartment",
            experience_level="some",
            time_availability="high",
            grooming_tolerance="high",
            has_other_pets=False,
            has_allergies=False
        )
        
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== Active Apartment Dweller ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Should NOT recommend giant breeds for apartments
        giant_breeds = ["Great Danes", "Mastiffs", "St. Bernards"]
        top_5_breeds = breed_names[:5]
        
        giant_in_top_5 = [b for b in top_5_breeds if any(gb in b for gb in giant_breeds)]
        assert len(giant_in_top_5) == 0, \
            f"Giant breeds not suitable for apartments: {giant_in_top_5}"
        
        # Should recommend energetic breeds
        energetic_breeds = [
            "Border Collies", "Australian Shepherds", "Vizslas",
            "Weimaraners", "Belgian Malinois"
        ]
        
        energetic_matches = [b for b in top_5_breeds if any(eb in b for eb in energetic_breeds)]
        assert len(energetic_matches) >= 1, \
            f"Expected energetic breeds for very active user, got {top_5_breeds}"
    
    @pytest.mark.asyncio
    async def test_senior_low_maintenance(self, engine, breed_service):
        """
        Scenario: Senior citizen, sedentary lifestyle, low grooming tolerance
        Expected: Low-energy, low-maintenance breeds (Shih Tzu, Pug, Cavalier)
        """
        user_profile = UserProfile(
            has_children=False,
            activity_level="sedentary",
            living_space="apartment",
            experience_level="experienced",
            time_availability="moderate",
            grooming_tolerance="low",
            has_other_pets=False,
            has_allergies=False
        )
        
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== Senior Low Maintenance ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Should NOT recommend high-energy breeds
        high_energy_breeds = [
            "Border Collies", "Australian Shepherds", "Jack Russell Terriers",
            "Siberian Huskies"
        ]
        
        top_5_breeds = breed_names[:5]
        high_energy_in_top_5 = [b for b in top_5_breeds if any(hb in b for hb in high_energy_breeds)]
        
        assert len(high_energy_in_top_5) == 0, \
            f"High-energy breeds not suitable for sedentary lifestyle: {high_energy_in_top_5}"
        
        # Should recommend low-energy, companion breeds
        companion_breeds = [
            "Shih Tzu", "Pugs", "Cavalier King Charles Spaniels",
            "French Bulldogs", "Bichon Frise"
        ]
        
        companion_matches = [b for b in top_5_breeds if any(cb in b for cb in companion_breeds)]
        assert len(companion_matches) >= 1, \
            f"Expected low-energy companion breeds, got {top_5_breeds}"
    
    @pytest.mark.asyncio
    async def test_allergic_user(self, engine, breed_service):
        """
        Scenario: User with allergies needs hypoallergenic breed
        Expected: Low-shedding breeds (Poodles, Portuguese Water Dogs, Maltese)
        """
        user_profile = UserProfile(
            has_children=False,
            activity_level="moderate",
            living_space="house_with_yard",
            experience_level="some",
            time_availability="moderate",
            grooming_tolerance="high",
            has_other_pets=False,
            has_allergies=True
        )
        
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== Allergic User ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Get breed traits to verify low shedding
        top_breed_name = breed_names[0]
        top_breed_traits = await breed_service.get_breed_traits(top_breed_name)
        
        # Top recommendation should have low shedding (3 or less on 1-5 scale)
        assert top_breed_traits.shedding_level <= 3, \
            f"Top breed for allergic user has high shedding: {top_breed_traits.shedding_level}/5"
        
        # Should recommend hypoallergenic breeds
        hypoallergenic_breeds = [
            "Poodles", "Portuguese Water Dogs", "Maltese",
            "Bichon Frise", "Schnauzers", "Yorkshire Terriers"
        ]
        
        top_5_breeds = breed_names[:5]
        hypo_matches = [b for b in top_5_breeds if any(hb in b for hb in hypoallergenic_breeds)]
        
        assert len(hypo_matches) >= 2, \
            f"Expected hypoallergenic breeds for allergic user, got {top_5_breeds}"
    
    @pytest.mark.asyncio
    async def test_first_time_owner(self, engine, breed_service):
        """
        Scenario: First-time dog owner, needs easy-to-train breed
        Expected: Highly trainable, forgiving breeds (Golden Retriever, Poodle, Labrador)
        """
        user_profile = UserProfile(
            has_children=False,
            activity_level="moderate",
            living_space="house_with_yard",
            experience_level="first_time",
            time_availability="moderate",
            grooming_tolerance="moderate",
            has_other_pets=False,
            has_allergies=False
        )
        
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== First-Time Owner ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Get trainability of top recommendation
        top_breed_name = breed_names[0]
        top_breed_traits = await breed_service.get_breed_traits(top_breed_name)
        
        # Should have high trainability (4 or 5 on 1-5 scale)
        assert top_breed_traits.trainability_level >= 4, \
            f"Top breed for first-time owner has low trainability: {top_breed_traits.trainability_level}/5"
        
        # Should NOT recommend stubborn/independent breeds
        difficult_breeds = [
            "Afghan Hounds", "Basenjis", "Bulldogs",
            "Chow Chows", "Siberian Huskies"
        ]
        
        top_5_breeds = breed_names[:5]
        difficult_in_top_5 = [b for b in top_5_breeds if any(db in b for db in difficult_breeds)]
        
        assert len(difficult_in_top_5) == 0, \
            f"Difficult breeds not suitable for first-time owner: {difficult_in_top_5}"
    
    @pytest.mark.asyncio
    async def test_multi_pet_household(self, engine, breed_service):
        """
        Scenario: House with existing pets (cats/dogs)
        Expected: Breeds good with other animals (Golden Retriever, Beagle, Basset Hound)
        """
        user_profile = UserProfile(
            has_children=False,
            activity_level="moderate",
            living_space="house_with_yard",
            experience_level="some",
            time_availability="moderate",
            grooming_tolerance="moderate",
            has_other_pets=True,
            has_allergies=False
        )
        
        top_matches = await engine.find_top_matches(user_profile, top_n=10)
        breed_names = [match[0] for match in top_matches]
        
        print("\n=== Multi-Pet Household ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        # Get pet-friendliness of top recommendation
        top_breed_name = breed_names[0]
        top_breed_traits = await breed_service.get_breed_traits(top_breed_name)
        
        # Should have high pet friendliness (4 or 5 on 1-5 scale)
        assert top_breed_traits.good_with_other_dogs >= 4, \
            f"Top breed for multi-pet home has low pet compatibility: {top_breed_traits.good_with_other_dogs}/5"
        
        # Should NOT recommend breeds with high prey drive or dog aggression
        not_pet_friendly = [
            "Akitas", "Pit Bull Terriers", "Chow Chows"
        ]
        
        top_5_breeds = breed_names[:5]
        aggressive_in_top_5 = [b for b in top_5_breeds if any(ab in b for ab in not_pet_friendly)]
        
        assert len(aggressive_in_top_5) == 0, \
            f"Breeds with potential pet aggression: {aggressive_in_top_5}"
    
    @pytest.mark.asyncio
    async def test_score_distribution(self, engine, breed_service):
        """Test that scores are properly distributed and make sense"""
        
        # Perfect match scenario
        perfect_profile = UserProfile(
            has_children=True,
            activity_level="moderate",
            living_space="house_with_yard",
            experience_level="some",
            time_availability="high",
            grooming_tolerance="high",
            has_other_pets=False,
            has_allergies=False
        )
        
        top_matches = await engine.find_top_matches(perfect_profile, top_n=20)
        
        print("\n=== Score Distribution ===")
        print("Top 10 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:10], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        scores = [match[1] for match in top_matches]
        
        # Top score should be reasonable (not 100% or too low)
        assert 70 <= scores[0] <= 95, \
            f"Top score seems unrealistic: {scores[0]:.1f}%"
        
        # Scores should be descending
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1], \
                f"Scores not properly ordered: {scores[i]:.1f}% > {scores[i+1]:.1f}%"
        
        # Should have good spread (top score - 10th score > 10%)
        score_spread = scores[0] - scores[9]
        assert score_spread > 10, \
            f"Insufficient score differentiation: {score_spread:.1f}%"
    
    @pytest.mark.asyncio
    async def test_conflicting_requirements(self, engine, breed_service):
        """
        Scenario: Contradictory requirements (very active + sedentary preference)
        System should handle gracefully and prioritize reasonably
        """
        # Intentionally conflicting profile
        conflicting_profile = UserProfile(
            has_children=True,  # Needs gentle breed
            activity_level="very_active",  # But also very active
            living_space="apartment",  # Limited space
            experience_level="first_time",  # Needs easy breed
            time_availability="limited",  # Limited time
            grooming_tolerance="low",  # Low grooming
            has_other_pets=True,  # Multiple pets
            has_allergies=True  # Allergies
        )
        
        # Should still return results without error
        top_matches = await engine.find_top_matches(conflicting_profile, top_n=5)
        
        print("\n=== Conflicting Requirements ===")
        print("Top 5 matches:")
        for i, (breed, score, _) in enumerate(top_matches[:5], 1):
            print(f"{i}. {breed}: {score:.1f}%")
        
        assert len(top_matches) == 5, "Should return matches even with conflicts"
        
        # Scores might be lower but should still be reasonable
        assert top_matches[0][1] > 50, \
            f"Even with conflicts, should find some decent matches: {top_matches[0][1]:.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
