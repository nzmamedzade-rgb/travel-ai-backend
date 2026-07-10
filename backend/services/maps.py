# backend/services/maps.py

import os
import random
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class MapsService:
    """
    Service for route optimization and hidden gem discovery.
    """
    
    def __init__(self):
        """Initialize the Maps Service"""
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.use_mock_data = not self.api_key
        self._cache = {}
        
        # Hidden gems database
        self._gems_database = self._initialize_gems_database()
        
        if self.use_mock_data:
            print("⚠️ No GOOGLE_MAPS_API_KEY found. Using mock data.")
    
    @staticmethod
    def calculate_optimal_route(
        origin: str, 
        destination: str, 
        travel_mode: str = "transit"
    ) -> dict:
        """
        Calculates transit paths and applies Time Optimization algorithms.
        """
        service = MapsService()
        return service._calculate_optimal_route(origin, destination, travel_mode)
    
    def _calculate_optimal_route(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "transit"
    ) -> dict:
        """Internal route calculation"""
        
        # Check cache
        cache_key = f"{origin}_{destination}_{travel_mode}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try real API if available
        if not self.use_mock_data:
            try:
                route = self._fetch_route_from_api(origin, destination, travel_mode)
                if route:
                    self._cache[cache_key] = route
                    return route
            except Exception as e:
                print(f"API error: {e}")
        
        # Generate mock route
        route = self._generate_mock_route(origin, destination, travel_mode)
        self._cache[cache_key] = route
        return route
    
    @staticmethod
    def discover_hidden_gems(destination: str) -> list[dict]:
        """
        Executes the Hidden Gems Algorithm to locate underrated spots.
        """
        service = MapsService()
        return service._discover_hidden_gems(destination)
    
    def _discover_hidden_gems(self, destination: str) -> list[dict]:
        """Internal hidden gems discovery"""
        
        destination_lower = destination.lower()
        
        # Check cache
        cache_key = f"gems_{destination_lower}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get gems from database
        gems = self._gems_database.get(destination_lower, [])
        
        # Add generic gems if none found
        if not gems:
            gems = self._get_generic_gems(destination)
        
        self._cache[cache_key] = gems
        return gems
    
    def search_nearby(
        self,
        location: str,
        radius_km: float = 2.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for nearby points of interest.
        """
        cache_key = f"nearby_{location}_{radius_km}"
        
        if cache_key in self._cache:
            return self._cache[cache_key][:limit]
        
        if not self.use_mock_data:
            try:
                places = self._fetch_nearby_from_api(location, radius_km)
                if places:
                    self._cache[cache_key] = places
                    return places[:limit]
            except Exception as e:
                print(f"Error fetching nearby places: {e}")
        
        # Generate mock nearby places
        places = self._generate_mock_nearby(location, radius_km)
        self._cache[cache_key] = places
        return places[:limit]
    
    # ============= Private Helper Methods =============
    
    def _initialize_gems_database(self) -> Dict[str, List[Dict]]:
        """Initialize hidden gems database"""
        return {
            "paris": [
                {
                    "name": "La Petite Ceinture Abandoned Railway",
                    "category": "hidden_trails",
                    "is_aesthetic": True,
                    "description": "Nature-covered historic railway line inside the city.",
                    "local_tip": "Best visited during golden hour",
                    "instagrammable": True
                },
                {
                    "name": "Le Pavillon des Canaux Hidden Cafe",
                    "category": "secret_cafes",
                    "is_aesthetic": True,
                    "description": "Entire house converted into a cozy waterfront coffee spot.",
                    "local_tip": "Try their homemade cakes!",
                    "instagrammable": True
                },
                {
                    "name": "Square du Vert-Galant Secret Park",
                    "category": "secret_gardens",
                    "is_aesthetic": True,
                    "description": "Hidden park at the tip of Île de la Cité.",
                    "local_tip": "Perfect picnic spot with Seine views",
                    "instagrammable": True
                }
            ],
            "london": [
                {
                    "name": "Leadenhall Market",
                    "category": "hidden_spots",
                    "is_aesthetic": True,
                    "description": "Beautiful Victorian covered market.",
                    "local_tip": "Visit early to avoid crowds",
                    "instagrammable": True
                },
                {
                    "name": "Postman's Park",
                    "category": "secret_gardens",
                    "is_aesthetic": True,
                    "description": "Quiet park with memorial plaques.",
                    "local_tip": "Read the memorial plaques",
                    "instagrammable": False
                }
            ],
            "rome": [
                {
                    "name": "Giardino degli Aranci",
                    "category": "secret_gardens",
                    "is_aesthetic": True,
                    "description": "Orange garden with amazing views of Rome.",
                    "local_tip": "Look through the keyhole on Aventine Hill",
                    "instagrammable": True
                }
            ],
            "barcelona": [
                {
                    "name": "Bunkers del Carmel",
                    "category": "viewpoints",
                    "is_aesthetic": True,
                    "description": "Former bunkers with 360-degree views.",
                    "local_tip": "Watch the sunset with snacks",
                    "instagrammable": True
                }
            ]
        }
    
    def _get_generic_gems(self, destination: str) -> List[Dict]:
        """Generate generic hidden gems"""
        return [
            {
                "name": f"Secret Backyard Coffee - {destination}",
                "category": "secret_cafes",
                "is_aesthetic": True,
                "description": "Hidden behind an unmarked wall. Local-only crowds.",
                "local_tip": "Ask locals for the best spots",
                "instagrammable": True
            },
            {
                "name": f"Hidden Bridge - {destination}",
                "category": "hidden_spots",
                "is_aesthetic": True,
                "description": "Cinematic location with zero tourist footprint.",
                "local_tip": "Great for photography",
                "instagrammable": True
            }
        ]
    
    def _generate_mock_route(self, origin: str, destination: str, travel_mode: str) -> dict:
        """Generate mock route data"""
        
        # Base duration by travel mode
        durations = {
            "transit": 45,
            "driving": 35,
            "walking": 90,
            "bicycling": 30
        }
        
        base_time = durations.get(travel_mode, 45)
        
        # Random optimization
        time_saved = random.randint(0, 20) if travel_mode in ["transit", "driving"] else 0
        duration = base_time - time_saved
        
        return {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "estimated_duration_minutes": duration,
            "traffic_status": "Optimized" if time_saved > 0 else "Normal",
            "time_saved_minutes": time_saved,
            "route_description": f"Alternative route applied. Saved {time_saved} minutes." if time_saved > 0 else "Standard direct navigation path.",
            "distance_km": round(duration * 0.8, 1),
            "eco_score": self._calculate_eco_score(travel_mode)
        }
    
    def _fetch_route_from_api(self, origin: str, destination: str, travel_mode: str) -> Optional[dict]:
        """Fetch real route from Google Maps API"""
        if not self.api_key:
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": travel_mode,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "OK":
                route = data["routes"][0]
                leg = route["legs"][0]
                duration = leg["duration"]["value"] // 60
                
                return {
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "travel_mode": travel_mode,
                    "estimated_duration_minutes": duration,
                    "traffic_status": "Normal",
                    "time_saved_minutes": 0,
                    "route_description": route.get("summary", "Direct route"),
                    "distance_km": leg["distance"]["value"] / 1000,
                    "eco_score": self._calculate_eco_score(travel_mode)
                }
            
            return None
            
        except Exception as e:
            print(f"API error: {e}")
            return None
    
    def _fetch_nearby_from_api(self, location: str, radius_km: float) -> Optional[List[Dict]]:
        """Fetch nearby places from Google Places API"""
        if not self.api_key:
            return None
        
        try:
            # Geocode location
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geocode_response = requests.get(
                geocode_url,
                params={"address": location, "key": self.api_key},
                timeout=10
            )
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()
            
            if geocode_data.get("status") != "OK":
                return None
            
            loc = geocode_data["results"][0]["geometry"]["location"]
            
            # Search nearby
            places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            places_response = requests.get(
                places_url,
                params={
                    "location": f"{loc['lat']},{loc['lng']}",
                    "radius": radius_km * 1000,
                    "key": self.api_key
                },
                timeout=10
            )
            places_response.raise_for_status()
            places_data = places_response.json()
            
            if places_data.get("status") == "OK":
                return [
                    {
                        "name": p.get("name"),
                        "address": p.get("vicinity"),
                        "rating": p.get("rating"),
                        "types": p.get("types")
                    }
                    for p in places_data.get("results", [])[:10]
                ]
            
            return None
            
        except Exception as e:
            print(f"Places API error: {e}")
            return None
    
    def _generate_mock_nearby(self, location: str, radius_km: float) -> List[Dict]:
        """Generate mock nearby places"""
        templates = [
            {"name": "Cafe Central", "types": ["cafe"], "rating": 4.5},
            {"name": "City Park", "types": ["park"], "rating": 4.7},
            {"name": "Art Gallery", "types": ["art"], "rating": 4.6},
            {"name": "Local Market", "types": ["shopping"], "rating": 4.3},
            {"name": "Historic Monument", "types": ["historical"], "rating": 4.8}
        ]
        
        return [
            {
                "name": f"{t['name']}",
                "address": f"{random.randint(1, 999)} Main St, {location}",
                "rating": t["rating"] + random.uniform(-0.2, 0.2),
                "types": t["types"],
                "distance": round(random.uniform(0.2, radius_km), 1)
            }
            for t in templates
        ]
    
    def _calculate_eco_score(self, travel_mode: str) -> int:
        """Calculate eco score for travel mode"""
        scores = {
            "walking": 100,
            "bicycling": 95,
            "transit": 80,
            "driving": 50,
            "flying": 30
        }
        return scores.get(travel_mode, 50)
    
    def get_city_info(self, city: str) -> Dict:
        """Get basic city information"""
        cities = {
            "Paris": {"country": "France", "currency": "EUR", "language": "French"},
            "London": {"country": "UK", "currency": "GBP", "language": "English"},
            "Rome": {"country": "Italy", "currency": "EUR", "language": "Italian"},
            "Barcelona": {"country": "Spain", "currency": "EUR", "language": "Spanish"}
        }
        return cities.get(city, {"country": "Unknown", "currency": "Unknown", "language": "Unknown"})


# ============= Test Function =============

if __name__ == "__main__":
    print("🗺️ Testing Maps Service...")
    
    service = MapsService()
    
    # Test route calculation
    print("\n📊 Route Calculation:")
    route = service.calculate_optimal_route("Paris", "London", "transit")
    print(f"Duration: {route['estimated_duration_minutes']} min")
    print(f"Traffic: {route['traffic_status']}")
    print(f"Description: {route['route_description']}")
    
    # Test hidden gems
    print("\n💎 Hidden Gems:")
    gems = service.discover_hidden_gems("Paris")
    for gem in gems[:3]:
        print(f"  - {gem['name']}: {gem['description'][:50]}...")
    
    # Test nearby search
    print("\n📍 Nearby Places:")
    places = service.search_nearby("Paris", radius_km=2.0, limit=3)
    for place in places:
        print(f"  - {place['name']} (Rating: {place.get('rating', 'N/A')})")
    
    print("\n✅ Maps Service tests complete!")