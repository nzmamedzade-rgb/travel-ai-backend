# backend/services/hotels.py

import os
import json
import random
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# ============= Enums and Constants =============

class HotelType(Enum):
    """Types of hotels"""
    LUXURY = "luxury"
    BOUTIQUE = "boutique"
    ECO_LODGE = "eco_lodge"
    HOSTEL = "hostel"
    APARTMENT = "apartment"
    RESORT = "resort"
    BUDGET = "budget"
    BUSINESS = "business"

class Amenity(Enum):
    """Hotel amenities"""
    WIFI = "wifi"
    POOL = "pool"
    SPA = "spa"
    GYM = "gym"
    RESTAURANT = "restaurant"
    BAR = "bar"
    PARKING = "parking"
    AIRPORT_SHUTTLE = "airport_shuttle"
    PET_FRIENDLY = "pet_friendly"
    FAMILY_FRIENDLY = "family_friendly"
    ECO_CERTIFIED = "eco_certified"
    ROOM_SERVICE = "room_service"
    BREAKFAST = "breakfast"
    AIR_CONDITIONING = "air_conditioning"


# ============= Data Classes =============

@dataclass
class HotelOption:
    """Hotel option data structure"""
    name: str
    original_rate: float
    rate_per_night: float
    is_eco_friendly: bool
    safety_rating: float
    smart_saving_alert: str
    hotel_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    amenities: List[str] = None
    distance_to_center: Optional[float] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    cancellation_policy: Optional[str] = None
    images: List[str] = None
    eco_score: Optional[int] = None
    available_rooms: int = 5
    
    def __post_init__(self):
        if self.amenities is None:
            self.amenities = []
        if self.images is None:
            self.images = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "hotel_name": self.name,
            "original_rate": self.original_rate,
            "rate_per_night": self.rate_per_night,
            "is_eco_friendly": self.is_eco_friendly,
            "safety_rating": self.safety_rating,
            "smart_saving_alert": self.smart_saving_alert,
            "hotel_type": self.hotel_type,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "amenities": self.amenities,
            "distance_to_center": self.distance_to_center,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "cancellation_policy": self.cancellation_policy,
            "images": self.images,
            "eco_score": self.eco_score,
            "available_rooms": self.available_rooms
        }


# ============= Main Service Class =============

class HotelService:
    """
    Service for searching and optimizing hotel accommodations.
    Integrates with real hotel APIs and provides dynamic pricing logic.
    """
    
    def __init__(self):
        """Initialize the Hotel Service"""
        self.api_key = os.getenv("HOTEL_API_KEY")
        self.use_mock_data = not self.api_key
        self._cache = {}
        
        # Amenities by hotel type
        self.amenity_map = {
            HotelType.LUXURY.value: [
                "wifi", "pool", "spa", "gym", "restaurant", "bar", 
                "parking", "room_service", "air_conditioning", "breakfast"
            ],
            HotelType.BOUTIQUE.value: [
                "wifi", "restaurant", "bar", "air_conditioning", "breakfast"
            ],
            HotelType.ECO_LODGE.value: [
                "wifi", "eco_certified", "breakfast", "parking"
            ],
            HotelType.HOSTEL.value: ["wifi", "breakfast"],
            HotelType.APARTMENT.value: [
                "wifi", "parking", "air_conditioning", "kitchen"
            ],
            HotelType.RESORT.value: [
                "wifi", "pool", "spa", "gym", "restaurant", "bar", 
                "parking", "airport_shuttle", "room_service", "breakfast"
            ],
            HotelType.BUDGET.value: ["wifi", "breakfast", "parking"],
            HotelType.BUSINESS.value: [
                "wifi", "gym", "restaurant", "bar", "parking", 
                "room_service", "breakfast", "air_conditioning"
            ]
        }
        
        if self.use_mock_data:
            print("⚠️  No HOTEL_API_KEY found. Using mock hotel data.")
    
    @staticmethod
    def fetch_available_hotels(
        destination: str, 
        budget: float,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 2,
        rooms: int = 1,
        hotel_type: Optional[str] = None,
        eco_only: bool = False,
        min_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries accommodation aggregators and evaluates dynamic market pricing
        trends to return optimized hotel selections within budget limits.
        
        Args:
            destination: Destination city
            budget: Maximum budget per night
            check_in: Check-in date (optional)
            check_out: Check-out date (optional)
            guests: Number of guests (default: 2)
            rooms: Number of rooms (default: 1)
            hotel_type: Type of hotel (optional)
            eco_only: Only show eco-friendly hotels
            min_rating: Minimum rating (optional)
            
        Returns:
            List[Dict]: Available hotel options with pricing
        """
        service = HotelService()
        return service._fetch_available_hotels(
            destination, budget, check_in, check_out, 
            guests, rooms, hotel_type, eco_only, min_rating
        )
    
    def _fetch_available_hotels(
        self,
        destination: str,
        budget: float,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 2,
        rooms: int = 1,
        hotel_type: Optional[str] = None,
        eco_only: bool = False,
        min_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Internal fetch implementation"""
        
        # Build cache key
        cache_key = f"{destination}_{budget}_{check_in}_{check_out}_{guests}_{rooms}_{hotel_type}_{eco_only}_{min_rating}"
        
        # Check cache
        if cache_key in self._cache:
            return self._filter_and_sort_options(
                self._cache[cache_key], budget, eco_only, min_rating
            )
        
        # Try to fetch from real API
        if not self.use_mock_data:
            try:
                options = self._fetch_hotels_from_api(
                    destination, check_in, check_out, guests, rooms
                )
                if options:
                    self._cache[cache_key] = options
                    return self._filter_and_sort_options(
                        options, budget, eco_only, min_rating
                    )
            except Exception as e:
                print(f"⚠️ Error fetching hotels from API: {e}")
                print("Falling back to mock data...")
        
        # Fallback to mock data
        options = self._generate_mock_hotels(
            destination, hotel_type, guests, rooms
        )
        self._cache[cache_key] = options
        return self._filter_and_sort_options(
            options, budget, eco_only, min_rating
        )
    
    def search_best_hotel(
        self,
        destination: str,
        budget: float,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 2,
        prefer_eco: bool = True
    ) -> Dict[str, Any]:
        """
        Find the best hotel option based on preferences.
        
        Args:
            destination: Destination city
            budget: Maximum budget
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            prefer_eco: Prefer eco-friendly hotels
            
        Returns:
            Dict: Best hotel option with details
        """
        # Get all options
        options = self._fetch_available_hotels(
            destination, budget, check_in, check_out, guests
        )
        
        if not options:
            return {"message": "No hotels found within your budget"}
        
        # Score each option
        scored_options = []
        for option in options:
            score = 0
            
            # Rating score (0-50)
            score += option.get("safety_rating", 0) * 10
            
            # Eco bonus (0-20)
            if option.get("is_eco_friendly", False) and prefer_eco:
                score += 20
            elif option.get("is_eco_friendly", False):
                score += 10
            
            # Price score (0-30) - cheaper is better
            price_ratio = option.get("rate_per_night", budget) / budget
            score += (1 - price_ratio) * 30
            
            # Add eco_score if available
            score += option.get("eco_score", 0) * 0.1
            
            scored_options.append((score, option))
        
        # Return the best option
        best_option = max(scored_options, key=lambda x: x[0])[1]
        
        return {
            "best_option": best_option,
            "score": max(scored_options, key=lambda x: x[0])[0],
            "total_options": len(options),
            "recommendation": self._get_hotel_recommendation(best_option)
        }
    
    def compare_hotels(
        self,
        destination: str,
        budget: float,
        hotel_names: List[str]
    ) -> Dict[str, Any]:
        """
        Compare specific hotels.
        
        Args:
            destination: Destination city
            budget: Maximum budget
            hotel_names: List of hotel names to compare
            
        Returns:
            Dict: Comparison results
        """
        # Get all options
        options = self._fetch_available_hotels(destination, budget)
        
        # Filter by hotel names
        comparison = {}
        for hotel in options:
            if any(name.lower() in hotel.get("hotel_name", "").lower() for name in hotel_names):
                comparison[hotel.get("hotel_name")] = hotel
        
        return {
            "comparison": comparison,
            "best_value": self._find_best_value(list(comparison.values())),
            "most_eco": self._find_most_eco(list(comparison.values()))
        }
    
    def get_availability(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        guests: int = 2
    ) -> Dict[str, Any]:
        """
        Check hotel availability for specific dates.
        
        Args:
            destination: Destination city
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            
        Returns:
            Dict: Availability information
        """
        # Get all options
        options = self._fetch_available_hotels(
            destination, 1000, check_in, check_out, guests
        )
        
        # Filter by availability
        available = [opt for opt in options if opt.get("available_rooms", 0) > 0]
        
        return {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "total_hotels": len(options),
            "available_hotels": len(available),
            "options": available[:10]  # Top 10 available
        }
    
    def book_hotel(
        self,
        hotel_option: Dict[str, Any],
        guest_details: Dict[str, Any],
        check_in: str,
        check_out: str
    ) -> Dict[str, Any]:
        """
        Book a hotel.
        
        Args:
            hotel_option: Selected hotel option
            guest_details: Guest information
            check_in: Check-in date
            check_out: Check-out date
            
        Returns:
            Dict: Booking confirmation
        """
        booking_reference = f"HB{random.randint(100000, 999999)}"
        
        return {
            "booking_reference": booking_reference,
            "status": "confirmed",
            "hotel_name": hotel_option.get("hotel_name"),
            "check_in": check_in,
            "check_out": check_out,
            "total_price": hotel_option.get("rate_per_night", 0) * self._calculate_nights(check_in, check_out),
            "confirmation_sent": True,
            "message": "Booking confirmed! Check your email for details."
        }
    
    # ============= Private Helper Methods =============
    
    def _generate_mock_hotels(
        self,
        destination: str,
        hotel_type: Optional[str] = None,
        guests: int = 2,
        rooms: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate mock hotel data"""
        
        # Base hotel templates
        hotel_templates = [
            {
                "name": f"Grand {destination} Luxury Resort",
                "base_price": 250.0,
                "safety_rating": 4.9,
                "is_eco": False,
                "type": HotelType.LUXURY.value,
                "rating": 4.8,
                "reviews": 1245,
                "distance": 0.5,
                "eco_score": 65
            },
            {
                "name": f"{destination} Boutique Eco-Lodge",
                "base_price": 110.0,
                "safety_rating": 4.7,
                "is_eco": True,
                "type": HotelType.ECO_LODGE.value,
                "rating": 4.6,
                "reviews": 876,
                "distance": 1.2,
                "eco_score": 92
            },
            {
                "name": f"Central Urban Hostel {destination}",
                "base_price": 45.0,
                "safety_rating": 4.1,
                "is_eco": False,
                "type": HotelType.HOSTEL.value,
                "rating": 4.2,
                "reviews": 2345,
                "distance": 0.8,
                "eco_score": 55
            },
            {
                "name": f"Green Stay Apartments {destination}",
                "base_price": 95.0,
                "safety_rating": 4.5,
                "is_eco": True,
                "type": HotelType.APARTMENT.value,
                "rating": 4.4,
                "reviews": 543,
                "distance": 1.8,
                "eco_score": 88
            },
            {
                "name": f"Business Suites {destination}",
                "base_price": 180.0,
                "safety_rating": 4.6,
                "is_eco": False,
                "type": HotelType.BUSINESS.value,
                "rating": 4.5,
                "reviews": 987,
                "distance": 0.3,
                "eco_score": 70
            },
            {
                "name": f"Eco Paradise Resort {destination}",
                "base_price": 320.0,
                "safety_rating": 4.9,
                "is_eco": True,
                "type": HotelType.RESORT.value,
                "rating": 4.9,
                "reviews": 1567,
                "distance": 3.0,
                "eco_score": 95
            },
            {
                "name": f"Budget Inn {destination}",
                "base_price": 65.0,
                "safety_rating": 3.8,
                "is_eco": False,
                "type": HotelType.BUDGET.value,
                "rating": 3.9,
                "reviews": 4321,
                "distance": 2.5,
                "eco_score": 45
            },
            {
                "name": f"Design Boutique Hotel {destination}",
                "base_price": 160.0,
                "safety_rating": 4.4,
                "is_eco": False,
                "type": HotelType.BOUTIQUE.value,
                "rating": 4.3,
                "reviews": 654,
                "distance": 0.9,
                "eco_score": 60
            }
        ]
        
        # Filter by type if specified
        if hotel_type:
            hotel_templates = [h for h in hotel_templates if h["type"] == hotel_type]
        
        # Generate options with dynamic pricing
        options = []
        for template in hotel_templates:
            # Dynamic pricing
            has_discount = random.choice([True, False]) and random.random() > 0.4
            discount_pct = random.choice([0.10, 0.15, 0.20, 0.25]) if has_discount else 0.0
            
            # Price variation by room type
            room_factor = 1.0 + (guests / 2) * 0.15
            original_price = template["base_price"] * room_factor
            optimized_price = original_price * (1 - discount_pct)
            
            # Add some randomness to ratings
            rating_variation = random.uniform(-0.1, 0.1)
            safety_rating = min(5.0, max(3.0, template["safety_rating"] + rating_variation))
            
            # Generate amenities based on hotel type
            amenities = self.amenity_map.get(template["type"], ["wifi"])
            
            # Add eco amenities if applicable
            if template["is_eco"]:
                amenities.append("eco_certified")
                amenities.append("renewable_energy")
            
            # Randomly select 3-6 amenities
            if len(amenities) > 6:
                amenities = random.sample(amenities, random.randint(3, 6))
            
            option = HotelOption(
                name=template["name"],
                original_rate=round(original_price, 2),
                rate_per_night=round(optimized_price, 2),
                is_eco_friendly=template["is_eco"],
                safety_rating=round(safety_rating, 1),
                smart_saving_alert=(
                    f"💰 {int(discount_pct*100)}% discount available! "
                    f"Book now to save ${round(original_price - optimized_price, 2)}"
                    if has_discount else "✓ Best available rate - no current promotions"
                ),
                hotel_type=template["type"],
                address=f"{random.randint(1, 999)} Main St, {destination}",
                phone=f"+{random.randint(1, 9)}{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                website=f"https://{template['name'].replace(' ', '').lower()}.example.com",
                rating=template["rating"],
                total_reviews=template["reviews"],
                amenities=amenities,
                distance_to_center=template["distance"],
                check_in_time=f"{random.randint(13, 16)}:00",
                check_out_time=f"{random.randint(10, 12)}:00",
                cancellation_policy=random.choice([
                    "Free cancellation 24h before check-in",
                    "Free cancellation 48h before check-in",
                    "Non-refundable",
                    "Free cancellation 72h before check-in"
                ]),
                images=[f"https://example.com/hotel_{i}.jpg" for i in range(3)],
                eco_score=template["eco_score"],
                available_rooms=random.randint(0, 20)
            )
            
            options.append(option.to_dict())
        
        return options
    
    def _fetch_hotels_from_api(
        self,
        destination: str,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 2,
        rooms: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch real hotels from external API"""
        # This is a placeholder for actual API integration
        # You can integrate with:
        # - Booking.com API
        # - Expedia API
        # - Hotels.com API
        # - Google Hotels API
        return self._generate_mock_hotels(destination, None, guests, rooms)
    
    def _filter_and_sort_options(
        self,
        options: List[Dict],
        budget: float,
        eco_only: bool = False,
        min_rating: Optional[float] = None
    ) -> List[Dict]:
        """Filter options by criteria and sort"""
        
        filtered = options.copy()
        
        # Filter by budget
        filtered = [
            opt for opt in filtered 
            if opt.get("rate_per_night", float('inf')) <= budget
        ]
        
        # Filter eco-only
        if eco_only:
            filtered = [opt for opt in filtered if opt.get("is_eco_friendly", False)]
        
        # Filter by minimum rating
        if min_rating:
            filtered = [
                opt for opt in filtered 
                if opt.get("safety_rating", 0) >= min_rating
            ]
        
        # Sort by safety rating (highest first)
        return sorted(
            filtered, 
            key=lambda x: (x.get("safety_rating", 0), -x.get("rate_per_night", float('inf'))),
            reverse=True
        )
    
    def _get_hotel_recommendation(self, hotel: Dict[str, Any]) -> str:
        """Generate recommendation text"""
        if hotel.get("is_eco_friendly", False):
            return "🌿 Highly recommended eco-friendly option!"
        elif hotel.get("safety_rating", 0) >= 4.5:
            return "⭐ Excellent safety rating - highly recommended!"
        elif hotel.get("rate_per_night", 0) < 100:
            return "💰 Great budget option with good value!"
        else:
            return "👍 Solid choice with good amenities"
    
    def _find_best_value(self, hotels: List[Dict]) -> Optional[Dict]:
        """Find the best value hotel"""
        if not hotels:
            return None
        
        scored = []
        for hotel in hotels:
            # Value = rating / price
            value = hotel.get("safety_rating", 0) / hotel.get("rate_per_night", 1)
            scored.append((value, hotel))
        
        return max(scored, key=lambda x: x[0])[1]
    
    def _find_most_eco(self, hotels: List[Dict]) -> Optional[Dict]:
        """Find the most eco-friendly hotel"""
        eco_hotels = [h for h in hotels if h.get("is_eco_friendly", False)]
        if eco_hotels:
            return max(eco_hotels, key=lambda x: x.get("eco_score", 0))
        return None
    
    def _calculate_nights(self, check_in: str, check_out: str) -> int:
        """Calculate number of nights between dates"""
        try:
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            return (check_out_date - check_in_date).days
        except:
            return 1


# ============= Additional Utility Functions =============

def format_hotel_details(hotel: Dict[str, Any]) -> str:
    """Format hotel details for display"""
    return (
        f"🏨 {hotel.get('hotel_name', 'Unknown')}\n"
        f"📍 {hotel.get('address', 'No address')}\n"
        f"⭐ Rating: {hotel.get('safety_rating', 0)}/5\n"
        f"💰 Price: ${hotel.get('rate_per_night', 0):.2f}/night\n"
        f"🌿 Eco-friendly: {'✅' if hotel.get('is_eco_friendly', False) else '❌'}\n"
        f"🏷️ Type: {hotel.get('hotel_type', 'Unknown')}\n"
        f"📞 {hotel.get('phone', 'No phone')}"
    )


def get_amenity_emoji(amenity: str) -> str:
    """Get emoji for amenity"""
    emoji_map = {
        "wifi": "📶",
        "pool": "🏊",
        "spa": "💆",
        "gym": "💪",
        "restaurant": "🍽️",
        "bar": "🍸",
        "parking": "🅿️",
        "airport_shuttle": "🚌",
        "pet_friendly": "🐾",
        "family_friendly": "👨‍👩‍👧‍👦",
        "eco_certified": "🌿",
        "room_service": "🛎️",
        "breakfast": "🍳",
        "air_conditioning": "❄️",
        "renewable_energy": "☀️"
    }
    return emoji_map.get(amenity, "✅")


# ============= Test Function =============

if __name__ == "__main__":
    print("🏨 Testing Hotel Service...")
    
    # Initialize service
    service = HotelService()
    
    # Test 1: Search hotels
    print("\n" + "="*50)
    print("📊 Searching Hotels")
    print("="*50)
    
    hotels = service._fetch_available_hotels(
        destination="Paris",
        budget=200,
        guests=2
    )
    
    for i, hotel in enumerate(hotels[:5], 1):
        print(f"\n{i}. {hotel['hotel_name']}")
        print(f"   Price: ${hotel['rate_per_night']}/night (was ${hotel['original_rate']})")
        print(f"   Rating: {hotel['safety_rating']}/5")
        print(f"   Eco: {'✅' if hotel['is_eco_friendly'] else '❌'}")
        print(f"   Alert: {hotel['smart_saving_alert']}")
    
    # Test 2: Find best hotel
    print("\n" + "="*50)
    print("🏆 Best Hotel")
    print("="*50)
    
    best = service.search_best_hotel("Paris", 200, prefer_eco=True)
    if "best_option" in best:
        print(f"\nBest Option: {best['best_option']['hotel_name']}")
        print(f"Score: {best['score']:.2f}")
        print(f"Recommendation: {best['recommendation']}")
    
    # Test 3: Check availability
    print("\n" + "="*50)
    print("📅 Availability Check")
    print("="*50)
    
    availability = service.get_availability(
        "Paris",
        check_in="2026-07-15",
        check_out="2026-07-20",
        guests=2
    )
    
    print(f"\nTotal Hotels: {availability['total_hotels']}")
    print(f"Available: {availability['available_hotels']}")
    
    # Test 4: Compare hotels
    print("\n" + "="*50)
    print("📊 Hotel Comparison")
    print("="*50)
    
    comparison = service.compare_hotels(
        "Paris", 200,
        ["Grand", "Eco-Lodge"]
    )
    
    for name, details in comparison.get("comparison", {}).items():
        print(f"\n{name}:")
        print(f"  Price: ${details['rate_per_night']:.2f}")
        print(f"  Rating: {details['safety_rating']}/5")
        print(f"  Eco: {'✅' if details['is_eco_friendly'] else '❌'}")
    
    print("\n✅ Hotel Service tests complete!")