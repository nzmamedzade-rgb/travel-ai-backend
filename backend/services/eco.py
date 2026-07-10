# backend/services/eco.py

import os
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ============= Enums and Constants =============

class TransportMode(Enum):
    """Transportation modes with their eco characteristics"""
    TRAIN = "train"
    FLIGHT = "flight"
    ELECTRIC = "electric"
    EV = "ev"
    BUS = "bus"
    CAR = "car"
    WALK = "walk"
    BICYCLE = "bicycle"
    FERRY = "ferry"
    METRO = "metro"

class EcoCategory(Enum):
    """Eco-friendliness categories"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

# Carbon emission factors (kg CO2 per passenger km)
CARBON_FACTORS = {
    TransportMode.TRAIN.value: 0.041,
    TransportMode.FLIGHT.value: 0.255,
    TransportMode.BUS.value: 0.089,
    TransportMode.CAR.value: 0.171,
    TransportMode.ELECTRIC.value: 0.030,  # Average for EV
    TransportMode.EV.value: 0.030,
    TransportMode.WALK.value: 0.0,
    TransportMode.BICYCLE.value: 0.0,
    TransportMode.FERRY.value: 0.115,
    TransportMode.METRO.value: 0.033,
}


# ============= Data Classes =============

@dataclass
class EcoMetrics:
    """Eco metrics for a transportation or activity"""
    transport_mode: str
    carbon_footprint_kg: float
    green_score: int  # 0-100
    is_sustainable: bool
    optimization_tip: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    category: str = "fair"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "transport_mode": self.transport_mode,
            "carbon_footprint_kg": self.carbon_footprint_kg,
            "green_score": self.green_score,
            "is_sustainable": self.is_sustainable,
            "optimization_tip": self.optimization_tip,
            "distance_km": self.distance_km,
            "duration_minutes": self.duration_minutes,
            "category": self.category,
            "timestamp": datetime.now().isoformat()
        }


@dataclass
class SustainableVenue:
    """Sustainable venue information"""
    name: str
    type: str  # hotel, restaurant, attraction, shop
    local_business_score: float  # 0-10
    eco_note: str
    address: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type,
            "local_business_score": self.local_business_score,
            "eco_note": self.eco_note,
            "address": self.address,
            "rating": self.rating,
            "price_level": self.price_level,
            "website": self.website,
            "phone": self.phone
        }


# ============= Main Service Class =============

class EcoService:
    """
    Service for calculating and optimizing eco-friendliness of travel choices.
    Integrates with external APIs for real carbon data.
    """
    
    def __init__(self):
        """Initialize the Eco Service"""
        self.carbon_api_key = os.getenv("CARBON_API_KEY")
        self.use_mock_data = not self.carbon_api_key
        self._cache = {}
        
        if self.use_mock_data:
            print("⚠️  No CARBON_API_KEY found. Using mock carbon data.")
    
    def calculate_eco_score(
        self, 
        transport_type: str, 
        distance_km: Optional[float] = None
    ) -> dict:
        """
        Calculates carbon emissions and sustainability metrics for transport modes.
        
        Args:
            transport_type: Type of transport (train, flight, car, etc.)
            distance_km: Distance in kilometers (optional)
            
        Returns:
            dict: Eco metrics including carbon footprint and green score
        """
        transport_lower = transport_type.lower()
        
        # Try to get from cache first
        cache_key = f"{transport_lower}_{distance_km if distance_km else 'default'}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get carbon factor for the transport mode
        carbon_factor = CARBON_FACTORS.get(transport_lower, 0.17)  # Default to car
        
        # Calculate carbon footprint
        if distance_km:
            carbon_kg = carbon_factor * distance_km
        else:
            # Use average distances for different modes
            carbon_kg = self._get_average_carbon(transport_lower)
        
        # Determine eco category and score
        eco_metrics = self._calculate_eco_metrics(
            transport_lower, 
            carbon_kg, 
            distance_km
        )
        
        # Cache the result
        self._cache[cache_key] = eco_metrics
        
        return eco_metrics
    
    def get_sustainable_venues(
        self, 
        destination: str, 
        venue_type: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """
        Returns verified green hotels, local organic cafes, or zero-waste spots.
        
        Args:
            destination: City or region name
            venue_type: Type of venue (hotel, restaurant, attraction, all)
            limit: Maximum number of venues to return
            
        Returns:
            List[dict]: List of sustainable venues
        """
        # Check cache
        cache_key = f"{destination}_{venue_type or 'all'}"
        if cache_key in self._cache:
            venues = self._cache[cache_key]
            return venues[:limit]
        
        # Try to fetch from external API
        if not self.use_mock_data:
            try:
                venues = self._fetch_sustainable_venues_api(destination, venue_type)
                if venues:
                    self._cache[cache_key] = venues
                    return venues[:limit]
            except Exception as e:
                print(f"Error fetching venues from API: {e}")
        
        # Fallback to mock data
        venues = self._get_mock_venues(destination, venue_type)
        self._cache[cache_key] = venues
        return venues[:limit]
    
    def get_total_trip_eco_score(self, trip_plan: dict) -> dict:
        """
        Calculate total eco score for an entire trip plan.
        
        Args:
            trip_plan: Complete trip plan with activities
            
        Returns:
            dict: Overall eco metrics for the trip
        """
        total_carbon = 0
        total_green_score = 0
        count = 0
        
        # Calculate for each activity
        for day, schedule in trip_plan.get("daily_itinerary", {}).items():
            activities = schedule.get("activities", [])
            for activity in activities:
                if isinstance(activity, dict):
                    transport = activity.get("transport", "walk")
                    distance = activity.get("distance_km")
                    
                    eco = self.calculate_eco_score(transport, distance)
                    total_carbon += eco.get("carbon_footprint_kg", 0)
                    total_green_score += eco.get("green_score", 50)
                    count += 1
        
        # Average scores
        avg_green_score = total_green_score / count if count > 0 else 0
        
        # Calculate accommodation eco impact (estimated)
        hotel_eco = self._estimate_hotel_eco_score(trip_plan)
        
        return {
            "total_carbon_kg": round(total_carbon, 2),
            "average_green_score": round(avg_green_score, 2),
            "total_activities": count,
            "accommodation_eco_score": hotel_eco,
            "overall_eco_rating": self._get_eco_rating(avg_green_score, hotel_eco),
            "recommendations": self._get_eco_recommendations(total_carbon, avg_green_score),
            "carbon_offset_cost": self._calculate_carbon_offset_cost(total_carbon)
        }
    
    def compare_transport_options(
        self, 
        from_location: str, 
        to_location: str,
        modes: List[str]
    ) -> List[dict]:
        """
        Compare different transport options for a route.
        
        Args:
            from_location: Starting location
            to_location: Destination
            modes: List of transport modes to compare
            
        Returns:
            List[dict]: Comparison results
        """
        results = []
        
        for mode in modes:
            # Get distance (mock for now)
            distance = self._get_distance_between(from_location, to_location)
            
            eco_metrics = self.calculate_eco_score(mode, distance)
            eco_metrics["mode"] = mode
            eco_metrics["distance_km"] = distance
            
            # Add time estimate (mock)
            eco_metrics["estimated_time"] = self._estimate_travel_time(mode, distance)
            
            results.append(eco_metrics)
        
        # Sort by green score (best first)
        results.sort(key=lambda x: x.get("green_score", 0), reverse=True)
        
        return results
    
    def get_eco_tips(self, destination: str) -> List[str]:
        """
        Get eco-friendly travel tips for a destination.
        
        Args:
            destination: City or region
            
        Returns:
            List[str]: Eco tips
        """
        tips = {
            "Paris": [
                "Use the metro instead of taxis - it's electric and efficient",
                "Visit parks like Jardin du Luxembourg - free and green",
                "Try local organic cafes in the Marais district",
                "Rent a bike through Vélib' for short trips",
                "Avoid tourist traps - support local businesses"
            ],
            "London": [
                "Use the Tube - one of the most efficient metro systems",
                "Walk between central London attractions - they're close",
                "Visit green spaces like Hyde Park and Regent's Park",
                "Use electric black cabs for longer trips",
                "Try zero-waste shops in Camden"
            ],
            "Rome": [
                "Walk - the historic center is pedestrian-friendly",
                "Use the metro or trams for longer journeys",
                "Visit Villa Borghese for a green escape",
                "Choose restaurants that use local, seasonal ingredients",
                "Stay in eco-certified hotels"
            ]
        }
        
        # Get tips for destination or default
        dest_tips = tips.get(destination, [
            f"Use public transportation in {destination}",
            "Walk or cycle when possible",
            "Support local, eco-friendly businesses",
            "Choose accommodations with green certifications",
            "Reduce waste - carry a reusable water bottle"
        ])
        
        return dest_tips
    
    def calculate_carbon_offset(self, carbon_kg: float) -> dict:
        """
        Calculate carbon offset cost and recommendations.
        
        Args:
            carbon_kg: Carbon footprint in kilograms
            
        Returns:
            dict: Offset information
        """
        # Average cost per ton of CO2 offset: $10-30
        offset_cost_per_ton = 15
        offset_cost = (carbon_kg / 1000) * offset_cost_per_ton
        
        # Trees needed to offset (1 tree absorbs ~20kg CO2/year)
        trees_needed = carbon_kg / 20
        
        return {
            "carbon_kg": round(carbon_kg, 2),
            "offset_cost_usd": round(offset_cost, 2),
            "trees_needed": round(trees_needed, 1),
            "offset_organizations": [
                "CarbonFund.org - $10/ton",
                "CoolEffect.org - Verified projects",
                "Plant-for-the-Planet - Tree planting"
            ],
            "recommendation": (
                "Offset your carbon footprint by donating "
                f"${round(offset_cost, 2)} to plant {round(trees_needed, 1)} trees "
                "or support verified renewable energy projects."
            )
        }
    
    # ============= Private Helper Methods =============
    
    def _calculate_eco_metrics(
        self, 
        transport: str, 
        carbon_kg: float,
        distance: Optional[float] = None
    ) -> dict:
        """Calculate eco metrics based on carbon footprint"""
        
        # Determine green score (0-100, lower carbon = higher score)
        if carbon_kg == 0:
            green_score = 100
            is_sustainable = True
            category = EcoCategory.EXCELLENT.value
        elif carbon_kg < 20:
            green_score = 85
            is_sustainable = True
            category = EcoCategory.EXCELLENT.value
        elif carbon_kg < 50:
            green_score = 70
            is_sustainable = True
            category = EcoCategory.GOOD.value
        elif carbon_kg < 100:
            green_score = 50
            is_sustainable = False
            category = EcoCategory.FAIR.value
        elif carbon_kg < 200:
            green_score = 30
            is_sustainable = False
            category = EcoCategory.POOR.value
        else:
            green_score = 20
            is_sustainable = False
            category = EcoCategory.POOR.value
        
        # Get optimization tip
        tip = self._get_optimization_tip(transport, carbon_kg)
        
        return {
            "transport_mode": transport,
            "carbon_footprint_kg": round(carbon_kg, 2),
            "green_score": green_score,
            "is_sustainable": is_sustainable,
            "optimization_tip": tip,
            "distance_km": round(distance, 2) if distance else None,
            "category": category
        }
    
    def _get_optimization_tip(self, transport: str, carbon_kg: float) -> str:
        """Get optimization tips based on transport mode and carbon impact"""
        tips = {
            TransportMode.TRAIN.value: (
                "🚆 Train chosen. Carbon emissions reduced by up to 85%! "
                "Consider booking in advance for better prices."
            ),
            TransportMode.FLIGHT.value: (
                "✈️ High carbon impact. Consider switching to rail for "
                "short distances or purchasing verified carbon offsets."
            ),
            TransportMode.ELECTRIC.value: (
                "⚡ Zero tailpipe emissions! Use renewable energy charging "
                "for an even better eco profile."
            ),
            TransportMode.BUS.value: (
                "🚌 Bus travel is eco-friendly. Carpooling options can "
                "further reduce emissions per passenger."
            ),
            TransportMode.CAR.value: (
                "🚗 Consider carpooling, using an electric vehicle, or "
                "switching to public transport to reduce emissions."
            ),
            TransportMode.WALK.value: (
                "🚶 Great choice! Walking is zero-carbon and healthy."
            ),
            TransportMode.BICYCLE.value: (
                "🚲 Excellent eco choice! Cycling is zero-carbon and "
                "good for your health."
            ),
            TransportMode.METRO.value: (
                "🚇 Metro systems are highly efficient. Continue using "
                "public transport for city travel."
            )
        }
        
        # Get specific tip or generic one
        tip = tips.get(transport, "Consider more sustainable transport options.")
        
        # Add carbon-specific advice
        if carbon_kg > 200:
            tip += " This route has high emissions. Please consider offsets."
        elif carbon_kg < 10:
            tip += " Great job keeping emissions low!"
        
        return tip
    
    def _get_average_carbon(self, transport: str) -> float:
        """Get average carbon for transport modes with typical distances"""
        average_distances = {
            TransportMode.TRAIN.value: 100,  # km
            TransportMode.FLIGHT.value: 800,
            TransportMode.BUS.value: 100,
            TransportMode.CAR.value: 50,
            TransportMode.ELECTRIC.value: 50,
            TransportMode.WALK.value: 2,
            TransportMode.BICYCLE.value: 5,
            TransportMode.FERRY.value: 50,
            TransportMode.METRO.value: 15,
        }
        
        distance = average_distances.get(transport, 50)
        factor = CARBON_FACTORS.get(transport, 0.171)
        
        return distance * factor
    
    def _get_mock_venues(self, destination: str, venue_type: Optional[str] = None) -> List[dict]:
        """Generate mock sustainable venues for testing"""
        venues = []
        
        # Base venues by type
        all_venues = [
            SustainableVenue(
                name=f"Green Leaf Organic Cafe - {destination}",
                type="restaurant",
                local_business_score=9.4,
                eco_note="Sources 100% ingredients locally from organic urban farming systems.",
                address=f"123 Green St, {destination}",
                rating=4.8,
                price_level="$$",
                website="https://greenleafcafe.example.com"
            ),
            SustainableVenue(
                name=f"Eco-Lodge Boutique Stay - {destination}",
                type="hotel",
                local_business_score=8.8,
                eco_note="Powered fully by renewable solar grids and uses strict rainwater filtration.",
                address=f"456 Eco Ave, {destination}",
                rating=4.9,
                price_level="$$$",
                website="https://ecolodge.example.com"
            ),
            SustainableVenue(
                name=f"Zero Waste Market - {destination}",
                type="shop",
                local_business_score=9.1,
                eco_note="Plastic-free, zero-waste grocery store with local produce.",
                address=f"789 Zero St, {destination}",
                rating=4.7,
                price_level="$",
                website="https://zerowaste.example.com"
            ),
            SustainableVenue(
                name=f"Green Space Park - {destination}",
                type="attraction",
                local_business_score=9.6,
                eco_note="Urban park with native plants, community gardens, and renewable energy.",
                address=f"321 Park Blvd, {destination}",
                rating=4.9,
                price_level="Free",
                website="https://greenspace.example.com"
            ),
            SustainableVenue(
                name=f"Organic Bistro - {destination}",
                type="restaurant",
                local_business_score=8.5,
                eco_note="Farm-to-table restaurant with seasonal menus and zero food waste policy.",
                address=f"654 Bistro Ln, {destination}",
                rating=4.6,
                price_level="$$",
                website="https://organicbistro.example.com"
            ),
        ]
        
        # Filter by type if specified
        if venue_type and venue_type != "all":
            all_venues = [v for v in all_venues if v.type == venue_type]
        
        return [v.to_dict() for v in all_venues]
    
    def _fetch_sustainable_venues_api(self, destination: str, venue_type: Optional[str] = None) -> List[dict]:
        """Fetch sustainable venues from external API (placeholder)"""
        # This would integrate with Google Places API, TripAdvisor, etc.
        # For now, return mock data
        return self._get_mock_venues(destination, venue_type)
    
    def _estimate_hotel_eco_score(self, trip_plan: dict) -> int:
        """Estimate hotel eco score from trip plan"""
        # Look for eco score in accommodation data
        accommodation = trip_plan.get("chosen_accommodation", {})
        if "eco_rating" in accommodation:
            return accommodation["eco_rating"]
        
        # Default score
        return 65
    
    def _get_eco_rating(self, avg_green_score: float, hotel_eco: int) -> str:
        """Get overall eco rating"""
        overall = (avg_green_score * 0.6) + (hotel_eco * 0.4)
        
        if overall >= 80:
            return "Excellent 🌟"
        elif overall >= 60:
            return "Good ✅"
        elif overall >= 40:
            return "Fair ⚠️"
        else:
            return "Needs Improvement ❌"
    
    def _get_eco_recommendations(self, total_carbon: float, avg_score: float) -> List[str]:
        """Get eco recommendations based on metrics"""
        recommendations = []
        
        if total_carbon > 200:
            recommendations.append("🌍 Consider carbon offsetting for this trip")
        if avg_score < 50:
            recommendations.append("🚲 Try to use more sustainable transport options")
        if total_carbon > 100:
            recommendations.append("🌱 Choose eco-friendly hotels and activities")
        
        if not recommendations:
            recommendations.append("👏 Great eco choices! Keep it up!")
        
        return recommendations
    
    def _calculate_carbon_offset_cost(self, carbon_kg: float) -> float:
        """Calculate carbon offset cost in USD"""
        return round((carbon_kg / 1000) * 15, 2)  # $15 per ton
    
    def _get_distance_between(self, from_loc: str, to_loc: str) -> float:
        """Get distance between two locations (mock)"""
        # In production, use Google Maps API or similar
        # Mock distances between common cities
        distances = {
            ("Paris", "London"): 344,
            ("Paris", "Rome"): 1100,
            ("London", "Rome"): 1432,
            ("Paris", "Berlin"): 877,
            ("Berlin", "Rome"): 1180,
        }
        
        key = (from_loc, to_loc)
        reverse_key = (to_loc, from_loc)
        
        if key in distances:
            return distances[key]
        elif reverse_key in distances:
            return distances[reverse_key]
        else:
            return 100  # Default distance
    
    def _estimate_travel_time(self, mode: str, distance: float) -> str:
        """Estimate travel time based on mode and distance"""
        speeds = {
            TransportMode.TRAIN.value: 150,  # km/h
            TransportMode.FLIGHT.value: 800,
            TransportMode.BUS.value: 80,
            TransportMode.CAR.value: 90,
            TransportMode.ELECTRIC.value: 80,
            TransportMode.WALK.value: 5,
            TransportMode.BICYCLE.value: 15,
            TransportMode.FERRY.value: 30,
            TransportMode.METRO.value: 50,
        }
        
        speed = speeds.get(mode, 50)
        hours = distance / speed
        
        if hours >= 1:
            return f"{int(hours)}h {int((hours % 1) * 60)}m"
        else:
            return f"{int(hours * 60)}m"


# ============= Legacy Functions (Backward Compatibility) =============

def calculate_eco_score(transport_type: str, distance_km: Optional[float] = None) -> dict:
    """
    Legacy function for backward compatibility.
    Delegates to EcoService class.
    """
    service = EcoService()
    return service.calculate_eco_score(transport_type, distance_km)


def get_sustainable_venues(destination: str) -> List[dict]:
    """
    Legacy function for backward compatibility.
    Delegates to EcoService class.
    """
    service = EcoService()
    return service.get_sustainable_venues(destination)


# ============= Test Function =============

if __name__ == "__main__":
    print("🌍 Testing Eco Service...")
    
    # Initialize service
    eco = EcoService()
    
    # Test 1: Calculate eco score for different transport modes
    print("\n" + "="*50)
    print("📊 Transport Eco Scores")
    print("="*50)
    
    for mode in ["train", "flight", "electric", "bus", "walk"]:
        score = eco.calculate_eco_score(mode, 100)
        print(f"\n{mode.upper()}:")
        print(f"  Carbon: {score['carbon_footprint_kg']} kg")
        print(f"  Score: {score['green_score']}/100")
        print(f"  Sustainable: {score['is_sustainable']}")
        print(f"  Tip: {score['optimization_tip']}")
    
    # Test 2: Get sustainable venues
    print("\n" + "="*50)
    print("🏨 Sustainable Venues")
    print("="*50)
    
    venues = eco.get_sustainable_venues("Paris", limit=3)
    for venue in venues:
        print(f"\n{venue['name']}")
        print(f"  Type: {venue['type']}")
        print(f"  Score: {venue['local_business_score']}/10")
        print(f"  Note: {venue['eco_note']}")
    
    # Test 3: Compare transport options
    print("\n" + "="*50)
    print("🚗 Transport Comparison")
    print("="*50)
    
    comparison = eco.compare_transport_options(
        "Paris", "London", 
        ["train", "flight", "bus"]
    )
    
    for result in comparison:
        print(f"\n{result['mode'].upper()}:")
        print(f"  Distance: {result['distance_km']} km")
        print(f"  Carbon: {result['carbon_footprint_kg']} kg")
        print(f"  Score: {result['green_score']}/100")
    
    # Test 4: Get eco tips
    print("\n" + "="*50)
    print("💡 Eco Tips")
    print("="*50)
    
    tips = eco.get_eco_tips("Paris")
    for tip in tips:
        print(f"• {tip}")
    
    print("\n✅ Eco Service tests complete!")