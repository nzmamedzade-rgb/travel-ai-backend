# backend/services/flight.py

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

class FlightClass(Enum):
    """Flight classes"""
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business"
    FIRST = "First Class"

class TransitType(Enum):
    """Types of transit"""
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    FERRY = "ferry"


# ============= Data Classes =============

@dataclass
class FlightOption:
    """Flight option data structure"""
    carrier: str
    transit_type: str
    duration: str
    original_price: float
    optimized_price: float
    price_alert: str
    flight_number: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    stops: int = 0
    stop_locations: List[str] = None
    carbon_emissions: Optional[float] = None
    eco_score: Optional[int] = None
    cancellation_policy: Optional[str] = None
    baggage_allowance: Optional[str] = None
    
    def __post_init__(self):
        if self.stop_locations is None:
            self.stop_locations = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "carrier": self.carrier,
            "transit_type": self.transit_type,
            "duration": self.duration,
            "original_price": self.original_price,
            "optimized_price": self.optimized_price,
            "price_alert": self.price_alert,
            "flight_number": self.flight_number,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "origin": self.origin,
            "destination": self.destination,
            "stops": self.stops,
            "stop_locations": self.stop_locations,
            "carbon_emissions": self.carbon_emissions,
            "eco_score": self.eco_score,
            "cancellation_policy": self.cancellation_policy,
            "baggage_allowance": self.baggage_allowance
        }


# ============= Main Service Class =============

class FlightService:
    """
    Service for searching and optimizing flight options.
    Integrates with real flight APIs and provides dynamic pricing logic.
    """
    
    def __init__(self):
        """Initialize the Flight Service"""
        self.api_key = os.getenv("FLIGHT_API_KEY")
        self.use_mock_data = not self.api_key
        self._cache = {}
        
        # Common airline codes for mock data
        self.airlines = {
            "AA": "American Airlines",
            "DL": "Delta Air Lines",
            "UA": "United Airlines",
            "BA": "British Airways",
            "AF": "Air France",
            "LH": "Lufthansa",
            "EK": "Emirates",
            "SQ": "Singapore Airlines",
            "QF": "Qantas",
            "NZ": "Air New Zealand"
        }
        
        if self.use_mock_data:
            print("⚠️  No FLIGHT_API_KEY found. Using mock flight data.")
    
    @staticmethod
    def search_flights(
        destination: str, 
        max_budget: float,
        origin: Optional[str] = None,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1,
        transit_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries flight aggregators and applies dynamic pricing logic
        to find the cheapest and most optimal transit options.
        
        Args:
            destination: Destination city or airport code
            max_budget: Maximum budget for the trip
            origin: Origin city or airport code (optional)
            departure_date: Departure date (optional)
            return_date: Return date for round trips (optional)
            passengers: Number of passengers (default: 1)
            transit_type: Type of transit (flight, train, etc.)
            
        Returns:
            List[Dict]: Available transit options with pricing
        """
        # Create service instance
        service = FlightService()
        return service._search_flights(
            destination, 
            max_budget, 
            origin, 
            departure_date, 
            return_date, 
            passengers, 
            transit_type
        )
    
    def _search_flights(
        self,
        destination: str,
        max_budget: float,
        origin: Optional[str] = None,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1,
        transit_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Internal search implementation"""
        
        # Build cache key
        cache_key = f"{destination}_{origin}_{departure_date}_{return_date}_{passengers}_{transit_type}"
        
        # Check cache
        if cache_key in self._cache:
            options = self._cache[cache_key]
            return self._filter_and_sort_options(options, max_budget)
        
        # Try to fetch from real API
        if not self.use_mock_data:
            try:
                options = self._fetch_flights_from_api(
                    destination, origin, departure_date, return_date, passengers
                )
                if options:
                    self._cache[cache_key] = options
                    return self._filter_and_sort_options(options, max_budget)
            except Exception as e:
                print(f"⚠️ Error fetching flights from API: {e}")
                print("Falling back to mock data...")
        
        # Fallback to mock data
        options = self._generate_mock_flights(
            destination, origin, transit_type, passengers
        )
        self._cache[cache_key] = options
        return self._filter_and_sort_options(options, max_budget)
    
    def search_best_deal(
        self,
        destination: str,
        max_budget: float,
        origin: Optional[str] = None,
        flexible_dates: bool = True
    ) -> Dict[str, Any]:
        """
        Find the best deal with flexible date options.
        
        Args:
            destination: Destination city
            max_budget: Maximum budget
            origin: Origin city (optional)
            flexible_dates: Whether dates are flexible
            
        Returns:
            Dict: Best deal with details
        """
        # Try multiple date ranges if flexible
        if flexible_dates:
            date_options = self._generate_date_options()
            best_deal = None
            best_price = float('inf')
            
            for dates in date_options:
                options = self._search_flights(
                    destination, max_budget, origin, dates["departure"], dates["return"]
                )
                if options and options[0]["optimized_price"] < best_price:
                    best_price = options[0]["optimized_price"]
                    best_deal = {
                        "option": options[0],
                        "departure_date": dates["departure"],
                        "return_date": dates["return"],
                        "savings": dates.get("savings", 0)
                    }
            
            return best_deal or {"message": "No deals found in your budget range"}
        else:
            options = self._search_flights(destination, max_budget, origin)
            if options:
                return {
                    "option": options[0],
                    "departure_date": datetime.now().strftime("%Y-%m-%d"),
                    "message": "Best available option"
                }
            return {"message": "No options found in your budget range"}
    
    def compare_transit_options(
        self,
        destination: str,
        max_budget: float,
        origin: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Compare different transit options (flight, train, bus) for a route.
        
        Args:
            destination: Destination
            max_budget: Maximum budget
            origin: Origin (optional)
            
        Returns:
            Dict: Comparison by transit type
        """
        result = {}
        transit_types = ["flight", "train", "bus", "ferry"]
        
        for t_type in transit_types:
            options = self._search_flights(
                destination, max_budget, origin, transit_type=t_type
            )
            if options:
                result[t_type] = options[:3]  # Top 3 options
        
        return result
    
    def get_price_prediction(
        self,
        destination: str,
        origin: Optional[str] = None,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Predict price trends for a route.
        
        Args:
            destination: Destination
            origin: Origin
            days_ahead: Number of days to look ahead
            
        Returns:
            Dict: Price prediction data
        """
        # Mock price prediction based on historical patterns
        current_price = self._get_current_price(destination, origin)
        
        # Simulate price predictions
        predictions = []
        for day in range(1, days_ahead + 1):
            # Random price fluctuation within +/- 20%
            fluctuation = random.uniform(-0.20, 0.20)
            predicted_price = current_price * (1 + fluctuation)
            
            predictions.append({
                "day": day,
                "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                "predicted_price": round(predicted_price, 2),
                "trend": "up" if fluctuation > 0 else "down"
            })
        
        # Find best day to book
        best_day = min(predictions, key=lambda x: x["predicted_price"])
        
        return {
            "current_price": current_price,
            "best_price": best_day["predicted_price"],
            "best_day_to_book": best_day["date"],
            "savings_if_wait": round(current_price - best_day["predicted_price"], 2),
            "predictions": predictions[:10],  # First 10 days
            "confidence": random.randint(70, 95),
            "recommendation": self._get_price_recommendation(predictions)
        }
    
    def book_flight(
        self,
        flight_option: Dict[str, Any],
        passenger_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Book a flight with the given option and passenger details.
        
        Args:
            flight_option: Selected flight option
            passenger_details: Passenger information
            
        Returns:
            Dict: Booking confirmation
        """
        booking_reference = f"BK{random.randint(100000, 999999)}"
        
        return {
            "booking_reference": booking_reference,
            "status": "confirmed",
            "carrier": flight_option.get("carrier"),
            "price": flight_option.get("optimized_price"),
            "passengers": passenger_details.get("passengers", 1),
            "confirmation_sent": True,
            "booking_time": datetime.now().isoformat(),
            "message": "Booking confirmed! Check your email for details."
        }
    
    # ============= Private Helper Methods =============
    
    def _generate_mock_flights(
        self,
        destination: str,
        origin: Optional[str],
        transit_type: Optional[str],
        passengers: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate mock flight data"""
        
        # Base prices by destination
        base_prices = {
            "Paris": 180.0,
            "London": 200.0,
            "Rome": 220.0,
            "Barcelona": 190.0,
            "Amsterdam": 210.0,
            "Berlin": 195.0,
            "Tokyo": 800.0,
            "New York": 350.0,
            "Sydney": 900.0,
            "Dubai": 450.0
        }
        
        base_price = base_prices.get(destination, 250.0)
        
        # Generate multiple flight options
        options = []
        airlines = list(self.airlines.values())
        
        # Transit types with their characteristics
        transit_configs = {
            "flight": {"durations": ["2h 45m", "3h 20m", "4h 10m"], "stops": [0, 1, 1]},
            "train": {"durations": ["5h 30m", "6h 15m", "7h 00m"], "stops": [0, 1, 2]},
            "bus": {"durations": ["8h 00m", "9h 30m", "11h 00m"], "stops": [2, 3, 4]},
            "ferry": {"durations": ["10h 00m", "12h 00m"], "stops": [1, 2]}
        }
        
        # Determine transit types to include
        transit_types = [transit_type] if transit_type else ["flight", "train"]
        
        for transit in transit_types:
            config = transit_configs.get(transit, transit_configs["flight"])
            
            for i in range(3):  # 3 options per transit type
                # Apply dynamic pricing
                has_discount = random.choice([True, False]) and random.random() > 0.3
                discount_pct = random.choice([0.10, 0.15, 0.20, 0.25]) if has_discount else 0.0
                
                # Base price varies by airline
                airline = random.choice(airlines)
                price_variation = random.uniform(0.90, 1.20)
                original_price = base_price * price_variation
                optimized_price = original_price * (1 - discount_pct)
                
                # Duration and stops
                duration_index = i % len(config["durations"])
                stops_index = i % len(config["stops"])
                
                option = FlightOption(
                    carrier=airline,
                    transit_type=transit,
                    duration=config["durations"][duration_index],
                    original_price=round(original_price, 2),
                    optimized_price=round(optimized_price, 2),
                    price_alert=(
                        f"🎯 {discount_pct*100}% discount predicted! "
                        if has_discount else "Stable price - book now for best rate"
                    ),
                    flight_number=f"{random.choice(list(self.airlines.keys()))}{random.randint(100, 999)}",
                    departure_time=self._generate_time(),
                    arrival_time=self._generate_time(),
                    origin=origin or "JFK",
                    destination=destination,
                    stops=config["stops"][stops_index],
                    stop_locations=self._generate_stop_locations(config["stops"][stops_index]),
                    carbon_emissions=round(random.uniform(50, 400), 1),
                    eco_score=random.randint(50, 95),
                    cancellation_policy="Free cancellation within 24 hours",
                    baggage_allowance=f"{random.choice([1, 2])} bags included"
                )
                
                options.append(option.to_dict())
        
        return options
    
    def _fetch_flights_from_api(
        self,
        destination: str,
        origin: Optional[str] = None,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch real flights from external API"""
        # This is a placeholder for actual API integration
        # You can integrate with:
        # - Amadeus API
        # - Skyscanner API
        # - Google Flights API
        # - Aviationstack API
        
        # For now, return mock data
        return self._generate_mock_flights(destination, origin, "flight", passengers)
    
    def _filter_and_sort_options(
        self, 
        options: List[Dict], 
        max_budget: float
    ) -> List[Dict]:
        """Filter options by budget and sort by price"""
        filtered = [
            opt for opt in options 
            if opt.get("optimized_price", float('inf')) <= max_budget
        ]
        
        # Sort by optimized price (lowest first)
        return sorted(filtered, key=lambda x: x.get("optimized_price", float('inf')))
    
    def _generate_date_options(self) -> List[Dict]:
        """Generate date options for flexible searching"""
        options = []
        today = datetime.now()
        
        for i in range(7):  # 7 days of options
            departure = today + timedelta(days=i * 2 + 1)
            return_date = departure + timedelta(days=random.randint(3, 7))
            
            # Random discount for some dates
            savings = random.randint(0, 30)
            
            options.append({
                "departure": departure.strftime("%Y-%m-%d"),
                "return": return_date.strftime("%Y-%m-%d"),
                "savings": savings,
                "savings_label": f"Save {savings}% on this date" if savings > 0 else "Standard pricing"
            })
        
        return options
    
    def _get_current_price(self, destination: str, origin: Optional[str] = None) -> float:
        """Get current price for a route"""
        base_prices = {
            "Paris": 250.0,
            "London": 280.0,
            "Rome": 300.0,
            "Barcelona": 270.0
        }
        return base_prices.get(destination, 300.0)
    
    def _get_price_recommendation(self, predictions: List[Dict]) -> str:
        """Generate price recommendation"""
        if not predictions:
            return "Book now for the best rate"
        
        # Find trend
        recent_prices = [p["predicted_price"] for p in predictions[:5]]
        if len(recent_prices) > 1 and recent_prices[-1] < recent_prices[0]:
            return "Prices are decreasing - you might save by waiting"
        elif len(recent_prices) > 1 and recent_prices[-1] > recent_prices[0]:
            return "Prices are increasing - book now to secure the current rate"
        else:
            return "Prices are stable - book when convenient"
    
    def _generate_time(self) -> str:
        """Generate a random time"""
        hour = random.randint(5, 23)
        minute = random.choice([0, 15, 30, 45])
        return f"{hour:02d}:{minute:02d}"
    
    def _generate_stop_locations(self, num_stops: int) -> List[str]:
        """Generate stop locations for flights"""
        possible_stops = ["LHR", "CDG", "AMS", "FRA", "JFK", "DXB", "SIN"]
        if num_stops > 0:
            return random.sample(possible_stops, min(num_stops, len(possible_stops)))
        return []


# ============= Additional Utility Functions =============

def format_flight_details(flight: Dict[str, Any]) -> str:
    """Format flight details for display"""
    return (
        f"{flight.get('carrier', 'Unknown')} - {flight.get('flight_number', 'N/A')}\n"
        f"Duration: {flight.get('duration', 'N/A')}\n"
        f"Stops: {flight.get('stops', 0)}\n"
        f"Price: ${flight.get('optimized_price', 0):.2f}\n"
        f"Alert: {flight.get('price_alert', 'No alert')}"
    )


def get_best_eco_option(options: List[Dict]) -> Optional[Dict]:
    """Get the most eco-friendly option from a list"""
    eco_options = [opt for opt in options if opt.get("eco_score", 0) >= 70]
    if eco_options:
        return max(eco_options, key=lambda x: x.get("eco_score", 0))
    return None


def get_cheapest_option(options: List[Dict]) -> Optional[Dict]:
    """Get the cheapest option from a list"""
    if options:
        return min(options, key=lambda x: x.get("optimized_price", float('inf')))
    return None


# ============= Test Function =============

if __name__ == "__main__":
    print("✈️ Testing Flight Service...")
    
    # Initialize service
    service = FlightService()
    
    # Test 1: Search flights
    print("\n" + "="*50)
    print("📊 Searching Flights")
    print("="*50)
    
    flights = service._search_flights(
        destination="Paris",
        max_budget=500,
        origin="London"
    )
    
    for i, flight in enumerate(flights[:5], 1):
        print(f"\n{i}. {flight['carrier']} - {flight['transit_type']}")
        print(f"   Price: ${flight['optimized_price']} (was ${flight['original_price']})")
        print(f"   Duration: {flight['duration']}")
        print(f"   Stops: {flight['stops']}")
        print(f"   Alert: {flight['price_alert']}")
    
    # Test 2: Get price prediction
    print("\n" + "="*50)
    print("📈 Price Prediction")
    print("="*50)
    
    prediction = service.get_price_prediction("Paris", "London", 30)
    print(f"\nCurrent Price: ${prediction['current_price']:.2f}")
    print(f"Best Price: ${prediction['best_price']:.2f}")
    print(f"Best Day: {prediction['best_day_to_book']}")
    print(f"Savings: ${prediction['savings_if_wait']:.2f}")
    print(f"Recommendation: {prediction['recommendation']}")
    
    # Test 3: Compare transit options
    print("\n" + "="*50)
    print("🚗 Transit Comparison")
    print("="*50)
    
    comparison = service.compare_transit_options("Paris", 500, "London")
    for transit_type, options in comparison.items():
        print(f"\n{transit_type.upper()}:")
        for opt in options[:2]:
            print(f"  - {opt['carrier']}: ${opt['optimized_price']:.2f}")
    
    # Test 4: Best deal search
    print("\n" + "="*50)
    print("💎 Best Deal")
    print("="*50)
    
    best_deal = service.search_best_deal("Paris", 400, "London", flexible_dates=True)
    if "option" in best_deal:
        print(f"\nBest Option: {best_deal['option']['carrier']}")
        print(f"Price: ${best_deal['option']['optimized_price']:.2f}")
        print(f"Departure: {best_deal['departure_date']}")
        print(f"Return: {best_deal['return_date']}")
        if best_deal.get('savings', 0) > 0:
            print(f"💡 Savings: {best_deal['savings']}%")
    
    print("\n✅ Flight Service tests complete!")