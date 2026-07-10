# backend/services/safe.py

import os
import random
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class SafetyService:
    """
    Service for evaluating zone security, identifying risks, and providing safety guidance.
    """
    
    def __init__(self):
        """Initialize the Safety Service"""
        self.api_key = os.getenv("SAFETY_API_KEY")
        self.use_mock_data = not self.api_key
        self._cache = {}
        
        if self.use_mock_data:
            print("⚠️ No SAFETY_API_KEY found. Using mock safety data.")
    
    @staticmethod
    def evaluate_zone_security(destination: str) -> dict:
        """
        Analyzes regional risk profiles, scam areas, unsafe transport methods,
        and provides emergency safety guidance parameters.
        
        Args:
            destination: City or region to evaluate
            
        Returns:
            dict: Security profile with safety recommendations
        """
        service = SafetyService()
        return service._evaluate_zone_security(destination)
    
    def _evaluate_zone_security(self, destination: str) -> dict:
        """Internal security evaluation"""
        
        destination_lower = destination.lower()
        
        # Check cache
        cache_key = f"safety_{destination_lower}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to fetch from real API if available
        if not self.use_mock_data:
            try:
                profile = self._fetch_safety_from_api(destination)
                if profile:
                    self._cache[cache_key] = profile
                    return profile
            except Exception as e:
                print(f"Safety API error: {e}")
        
        # Generate mock safety profile
        profile = self._generate_safety_profile(destination)
        self._cache[cache_key] = profile
        return profile
    
    @staticmethod
    def get_emergency_contacts(destination: str) -> dict:
        """
        Get emergency contact numbers for a destination.
        
        Args:
            destination: City or country
            
        Returns:
            dict: Emergency contact numbers
        """
        service = SafetyService()
        return service._get_emergency_contacts(destination)
    
    def _get_emergency_contacts(self, destination: str) -> dict:
        """Internal emergency contacts retrieval"""
        
        # Common emergency numbers by country
        contacts = {
            "france": {
                "police": "17",
                "ambulance": "15",
                "fire": "18",
                "european_emergency": "112"
            },
            "uk": {
                "police": "999",
                "ambulance": "999",
                "fire": "999",
                "european_emergency": "112"
            },
            "italy": {
                "police": "113",
                "ambulance": "118",
                "fire": "115",
                "european_emergency": "112"
            },
            "spain": {
                "police": "091",
                "ambulance": "061",
                "fire": "080",
                "european_emergency": "112"
            },
            "germany": {
                "police": "110",
                "ambulance": "112",
                "fire": "112",
                "european_emergency": "112"
            }
        }
        
        # Find matching country
        destination_lower = destination.lower()
        for country, numbers in contacts.items():
            if country in destination_lower:
                return numbers
        
        # Default to European emergency
        return {
            "police": "112",
            "ambulance": "112",
            "fire": "112",
            "european_emergency": "112",
            "note": "Use 112 for all emergencies in Europe"
        }
    
    @staticmethod
    def check_area_safety(destination: str, area: str, time: str = "day") -> dict:
        """
        Check safety for a specific area within a destination.
        
        Args:
            destination: City name
            area: Specific area/neighborhood
            time: "day" or "night"
            
        Returns:
            dict: Area safety assessment
        """
        service = SafetyService()
        return service._check_area_safety(destination, area, time)
    
    def _check_area_safety(self, destination: str, area: str, time: str = "day") -> dict:
        """Internal area safety check"""
        
        # Get destination profile
        profile = self._generate_safety_profile(destination)
        
        # Check if area is flagged
        flagged_zones = profile.get("flagged_night_zones", [])
        is_flagged = any(area.lower() in zone.lower() for zone in flagged_zones)
        
        # Determine safety level
        if is_flagged and time == "night":
            safety_level = "High Risk - Avoid"
            recommendation = "Avoid this area at night. Use transportation instead."
        elif is_flagged and time == "day":
            safety_level = "Medium Risk - Caution"
            recommendation = "Exercise caution. Keep valuables secure."
        else:
            safety_level = "Low Risk - Safe"
            recommendation = "Normal safety precautions recommended."
        
        return {
            "area": area,
            "destination": destination,
            "time": time,
            "safety_level": safety_level,
            "is_flagged": is_flagged,
            "recommendation": recommendation,
            "tips": self._get_area_tips(safety_level)
        }
    
    def get_safety_guidelines(self, destination: str) -> List[str]:
        """
        Get general safety guidelines for a destination.
        
        Args:
            destination: City name
            
        Returns:
            List[str]: Safety guidelines
        """
        guidelines = [
            "Keep copies of important documents (passport, ID) in a secure location",
            "Save emergency numbers on your phone before traveling",
            "Share your itinerary with someone you trust",
            "Stay in well-lit, populated areas, especially at night",
            "Keep valuables secure and out of sight",
            "Trust your instincts - if something feels wrong, leave"
        ]
        
        # Add destination-specific guidelines
        destination_lower = destination.lower()
        
        if "paris" in destination_lower:
            guidelines.extend([
                "Watch for distraction scams near major tourist sites",
                "Use official taxi services (G7) or ride-sharing apps",
                "Keep your phone and wallet in front pockets on the metro"
            ])
        elif "barcelona" in destination_lower:
            guidelines.extend([
                "Be extra vigilant on Las Ramblas and in crowded areas",
                "Avoid engaging with street performers or games",
                "Keep bags zipped and secure at all times"
            ])
        elif "rome" in destination_lower:
            guidelines.extend([
                "Watch for scammers near the Colosseum and Vatican",
                "Avoid accepting 'free' bracelets or gifts",
                "Use only registered taxis with official meters"
            ])
        
        return guidelines
    
    # ============= Private Helper Methods =============
    
    def _generate_safety_profile(self, destination: str) -> dict:
        """Generate mock safety profile for destination"""
        
        destination_lower = destination.lower()
        
        # Default profile
        profile = {
            "destination_name": destination,
            "safety_index_rating": 85,
            "overall_status": "Low Risk Level",
            "flagged_night_zones": [],
            "common_scams_to_avoid": [],
            "emergency_copilot_guidance": "Local emergency numbers are configured. Keep digital copies of your passport offline.",
            "risk_level": "Low"
        }
        
        # Destination-specific safety data
        safety_data = {
            "paris": {
                "safety_index_rating": 74,
                "overall_status": "Medium Risk Alert",
                "flagged_night_zones": [
                    "Châtelet les Halles corridors late at night",
                    "Gare du Nord surroundings after 22:00",
                    "La Chapelle area at night"
                ],
                "common_scams_to_avoid": [
                    "The gold ring scam near the Seine riverbanks",
                    "Aggressive petition signers around Sacré-Cœur",
                    "Unofficial taxi touts at Charles de Gaulle airport",
                    "Fake petition scammers on the metro"
                ],
                "emergency_copilot_guidance": "Avoid walking alone at night in these zones. Use official G7 rideshare options.",
                "risk_level": "Medium"
            },
            "barcelona": {
                "safety_index_rating": 71,
                "overall_status": "High Pickpocket Advisory",
                "flagged_night_zones": [
                    "El Raval narrow alleyways past midnight",
                    "Crowded areas along Las Ramblas",
                    "Poble Sec area at night"
                ],
                "common_scams_to_avoid": [
                    "Distraction games (shell game) on street walkways",
                    "Spilled liquid trick where someone tries to 'clean' your jacket",
                    "Fake police officers asking for identification",
                    "The 'dropped wallet' scam"
                ],
                "emergency_copilot_guidance": "Keep your backpack on your front when riding the metro. Avoid accepting help from strangers.",
                "risk_level": "Medium-High"
            },
            "rome": {
                "safety_index_rating": 78,
                "overall_status": "Medium Risk Advisory",
                "flagged_night_zones": [
                    "Termini Station area after midnight",
                    "Esquilino neighborhood at night",
                    "Piazza Vittorio Emanuele area"
                ],
                "common_scams_to_avoid": [
                    "The 'free' bracelet/rose givers near tourist sites",
                    "Fake street artists charging for photos",
                    "Unofficial tour guides at the Colosseum",
                    "Pickpockets on crowded buses and metro"
                ],
                "emergency_copilot_guidance": "Book official guided tours. Keep wallets in front pockets on public transport.",
                "risk_level": "Medium"
            },
            "london": {
                "safety_index_rating": 82,
                "overall_status": "Low-Medium Risk",
                "flagged_night_zones": [
                    "Soho alleyways late at night",
                    "Some areas of East London after dark"
                ],
                "common_scams_to_avoid": [
                    "Fake city tours offered by non-accredited guides",
                    "Mobile phone snatching in busy areas"
                ],
                "emergency_copilot_guidance": "Use licensed black cabs or Uber. Avoid walking alone in dimly lit areas.",
                "risk_level": "Low-Medium"
            },
            "amsterdam": {
                "safety_index_rating": 85,
                "overall_status": "Low Risk",
                "flagged_night_zones": [
                    "Red Light District alleyways at night",
                    "Some park areas after midnight"
                ],
                "common_scams_to_avoid": [
                    "Fake ticket sellers for attractions",
                    "Pickpockets in crowded tourist areas"
                ],
                "emergency_copilot_guidance": "Use official transportation. Be cautious around canals at night.",
                "risk_level": "Low"
            },
            "berlin": {
                "safety_index_rating": 80,
                "overall_status": "Low-Medium Risk",
                "flagged_night_zones": [
                    "Some areas of Kreuzberg at night",
                    "Less busy U-Bahn stations after midnight"
                ],
                "common_scams_to_avoid": [
                    "Fake charity collectors near tourist sites",
                    "Unofficial taxi drivers at airports"
                ],
                "emergency_copilot_guidance": "Use official transport. Some areas quieter at night.",
                "risk_level": "Low-Medium"
            }
        }
        
        # Update with destination-specific data
        for city, data in safety_data.items():
            if city in destination_lower:
                profile.update(data)
                break
        
        # Add generic safety rating if not specified
        if profile["safety_index_rating"] == 85:
            # Random rating between 75-90 for unknown destinations
            profile["safety_index_rating"] = random.randint(75, 90)
            if profile["safety_index_rating"] < 80:
                profile["overall_status"] = "Medium Risk Advisory"
                profile["risk_level"] = "Medium"
        
        return profile
    
    def _fetch_safety_from_api(self, destination: str) -> Optional[dict]:
        """Fetch safety data from external API"""
        # Placeholder for real API integration
        # You could integrate with:
        # - Travel safety APIs
        # - World Bank safety data
        # - Government travel advisory APIs
        return None
    
    def _get_area_tips(self, safety_level: str) -> List[str]:
        """Get tips based on safety level"""
        tips = {
            "High Risk - Avoid": [
                "Avoid this area entirely if possible",
                "If you must go, stay in groups",
                "Keep valuables completely out of sight",
                "Have emergency contacts ready"
            ],
            "Medium Risk - Caution": [
                "Stay alert and aware of surroundings",
                "Keep valuables secure",
                "Avoid carrying large amounts of cash",
                "Save emergency numbers on your phone"
            ],
            "Low Risk - Safe": [
                "Standard safety precautions apply",
                "Keep valuables secure in crowds",
                "Stay in well-lit areas at night"
            ]
        }
        return tips.get(safety_level, tips["Low Risk - Safe"])


# ============= Test Function =============

if __name__ == "__main__":
    print("🛡️ Testing Safety Service...")
    
    service = SafetyService()
    
    # Test 1: Evaluate security for different cities
    print("\n📊 Security Evaluation:")
    
    for city in ["Paris", "Barcelona", "London", "Unknown City"]:
        profile = service.evaluate_zone_security(city)
        print(f"\n{city}:")
        print(f"  Status: {profile['overall_status']}")
        print(f"  Rating: {profile['safety_index_rating']}/100")
        print(f"  Risk Level: {profile.get('risk_level', 'Unknown')}")
    
    # Test 2: Get emergency contacts
    print("\n📞 Emergency Contacts:")
    contacts = service.get_emergency_contacts("Paris")
    for service_name, number in contacts.items():
        print(f"  {service_name}: {number}")
    
    # Test 3: Check specific area
    print("\n📍 Area Safety Check:")
    area_check = service.check_area_safety("Paris", "Châtelet les Halles", "night")
    print(f"Area: {area_check['area']}")
    print(f"Safety Level: {area_check['safety_level']}")
    print(f"Recommendation: {area_check['recommendation']}")
    
    # Test 4: Get safety guidelines
    print("\n📋 Safety Guidelines (Paris):")
    guidelines = service.get_safety_guidelines("Paris")
    for i, guideline in enumerate(guidelines, 1):
        print(f"  {i}. {guideline}")
    
    print("\n✅ Safety Service tests complete!")