# backend/services/weather.py

import os
import random
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class WeatherService:
    """
    Service for gathering live climate metrics and checking atmospheric conditions.
    """
    
    def __init__(self):
        """Initialize the Weather Service"""
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.use_mock_data = not self.api_key
        self._cache = {}
        
        if self.use_mock_data:
            print("⚠️ No OPENWEATHER_API_KEY found. Using mock weather data.")
    
    @staticmethod
    def get_destination_weather(destination: str) -> dict:
        """
        Gathers live climate metrics and checks for atmospheric conditions
        requiring immediate route or activity shifts.
        
        Args:
            destination: City name
            
        Returns:
            dict: Weather profile with conditions and warnings
        """
        service = WeatherService()
        return service._get_destination_weather(destination)
    
    def _get_destination_weather(self, destination: str) -> dict:
        """Internal weather retrieval"""
        
        destination_lower = destination.lower()
        
        # Check cache (5 minutes)
        cache_key = f"weather_{destination_lower}"
        if cache_key in self._cache:
            cache_time, data = self._cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5 minutes
                return data
        
        # Try to fetch from real API
        if not self.use_mock_data:
            try:
                weather = self._fetch_weather_from_api(destination)
                if weather:
                    self._cache[cache_key] = (datetime.now(), weather)
                    return weather
            except Exception as e:
                print(f"Weather API error: {e}")
        
        # Generate mock weather
        weather = self._generate_mock_weather(destination)
        self._cache[cache_key] = (datetime.now(), weather)
        return weather
    
    def get_forecast(self, destination: str, days: int = 5) -> list:
        """
        Get weather forecast for multiple days.
        
        Args:
            destination: City name
            days: Number of days forecast (default: 5)
            
        Returns:
            list: Daily forecast
        """
        # Get current weather
        current = self._get_destination_weather(destination)
        
        # Generate forecast
        forecast = []
        for i in range(days):
            day = datetime.now() + timedelta(days=i + 1)
            
            # Random variations
            temp_variation = random.randint(-5, 5)
            conditions = random.choice([
                "Sunny", "Cloudy", "Partly Cloudy", 
                "Light Rain", "Heavy Rain", "Clear"
            ])
            
            forecast.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": day.strftime("%A"),
                "temperature": f"{int(current.get('temperature', 20)) + temp_variation}°C",
                "condition": conditions,
                "precipitation": random.randint(0, 80),
                "humidity": random.randint(40, 90)
            })
        
        return forecast
    
    def get_best_time_to_visit(self, destination: str) -> dict:
        """
        Get best time to visit recommendation.
        
        Args:
            destination: City name
            
        Returns:
            dict: Best time recommendations
        """
        # Destination-specific recommendations
        recommendations = {
            "paris": {
                "best_months": "April to June and September to October",
                "avoid_months": "July and August (crowded)",
                "reason": "Mild weather, fewer crowds, beautiful spring blooms"
            },
            "london": {
                "best_months": "May to September",
                "avoid_months": "November to February",
                "reason": "Warm weather, longer days, outdoor events"
            },
            "rome": {
                "best_months": "April to June and September to October",
                "avoid_months": "July and August (too hot)",
                "reason": "Pleasant temperatures, fewer tourists"
            },
            "barcelona": {
                "best_months": "May to June and September to October",
                "avoid_months": "July and August (too hot)",
                "reason": "Perfect beach weather without extreme heat"
            }
        }
        
        dest_lower = destination.lower()
        for key, rec in recommendations.items():
            if key in dest_lower:
                return rec
        
        # Default recommendation
        return {
            "best_months": "Spring and Fall",
            "avoid_months": "Peak summer and winter",
            "reason": "Mild weather and fewer crowds"
        }
    
    def check_activity_viability(self, destination: str, activity_type: str) -> dict:
        """
        Check if weather is suitable for specific activities.
        
        Args:
            destination: City name
            activity_type: outdoor, indoor, swimming, hiking, etc.
            
        Returns:
            dict: Viability assessment
        """
        weather = self._get_destination_weather(destination)
        condition = weather.get("condition", "Sunny").lower()
        temperature = weather.get("temperature", 20)
        
        # Activity viability logic
        viability = {
            "outdoor": True,
            "indoor": True,
            "swimming": False,
            "hiking": False,
            "sightseeing": True,
            "beach": False
        }
        
        # Rain check
        if "rain" in condition or weather.get("precipitation", 0) > 60:
            viability["outdoor"] = False
            viability["hiking"] = False
            viability["sightseeing"] = False
            viability["beach"] = False
        
        # Temperature check
        if temperature < 15:
            viability["swimming"] = False
            viability["beach"] = False
        elif temperature > 30:
            viability["hiking"] = False
        
        # Specific checks
        if activity_type == "swimming":
            return {
                "viable": viability["swimming"],
                "reason": "Weather too cold for swimming" if not viability["swimming"] else "Good swimming conditions"
            }
        elif activity_type == "hiking":
            return {
                "viable": viability["hiking"],
                "reason": "Weather conditions not suitable for hiking" if not viability["hiking"] else "Good hiking conditions"
            }
        elif activity_type == "outdoor":
            return {
                "viable": viability["outdoor"],
                "reason": "Rain expected - consider indoor alternatives" if not viability["outdoor"] else "Perfect for outdoor activities"
            }
        
        return {
            "viable": viability.get(activity_type, True),
            "message": "Activity viability checked successfully"
        }
    
    def get_clothing_recommendations(self, destination: str) -> list:
        """
        Get clothing recommendations based on weather.
        
        Args:
            destination: City name
            
        Returns:
            list: Clothing recommendations
        """
        weather = self._get_destination_weather(destination)
        temp_str = weather.get("temperature", "20°C")
        temp = int(temp_str.replace("°C", ""))
        
        recommendations = []
        
        if temp > 25:
            recommendations = [
                "Lightweight t-shirts and shorts",
                "Sunscreen and sunglasses",
                "Hat for sun protection",
                "Comfortable walking shoes",
                "Light jacket for evenings"
            ]
        elif temp > 15:
            recommendations = [
                "Light layers (t-shirt + light jacket)",
                "Jeans or comfortable pants",
                "Comfortable walking shoes",
                "Light rain jacket (just in case)",
                "Sunglasses"
            ]
        elif temp > 5:
            recommendations = [
                "Warm layers (sweater + jacket)",
                "Jeans or warm pants",
                "Comfortable closed-toe shoes",
                "Warm scarf and hat",
                "Umbrella if rain is expected"
            ]
        else:
            recommendations = [
                "Heavy winter coat",
                "Warm sweaters and thermal layers",
                "Warm pants and boots",
                "Scarf, hat, and gloves",
                "Multiple layers for warmth"
            ]
        
        # Add weather-specific items
        condition = weather.get("condition", "Sunny").lower()
        if "rain" in condition:
            recommendations.append("Umbrella or raincoat")
        if "wind" in condition:
            recommendations.append("Wind-resistant jacket")
        
        return recommendations
    
    # ============= Private Helper Methods =============
    
    def _generate_mock_weather(self, destination: str) -> dict:
        """Generate mock weather data"""
        
        destination_lower = destination.lower()
        
        # Destination-specific weather
        weather_data = {
            "paris": {
                "temperature": "16°C",
                "condition": "Heavy Rain",
                "precipitation": 85,
                "humidity": 78,
                "wind_speed": 15,
                "reroute_needed": True,
                "warning": "Rain expected - outdoor activities should be swapped for indoor alternatives."
            },
            "london": {
                "temperature": "14°C",
                "condition": "Dense Fog",
                "precipitation": 40,
                "humidity": 82,
                "wind_speed": 12,
                "reroute_needed": False,
                "warning": "Low visibility conditions. Check scenic overlook timings."
            },
            "rome": {
                "temperature": "28°C",
                "condition": "Sunny",
                "precipitation": 5,
                "humidity": 55,
                "wind_speed": 8,
                "reroute_needed": False,
                "warning": "Beautiful weather! Great for exploring."
            },
            "barcelona": {
                "temperature": "26°C",
                "condition": "Partly Cloudy",
                "precipitation": 15,
                "humidity": 60,
                "wind_speed": 10,
                "reroute_needed": False,
                "warning": "Nice weather for beach or city exploration."
            },
            "amsterdam": {
                "temperature": "18°C",
                "condition": "Light Rain",
                "precipitation": 65,
                "humidity": 75,
                "wind_speed": 18,
                "reroute_needed": True,
                "warning": "Rain expected. Consider indoor museums and cafes."
            },
            "berlin": {
                "temperature": "20°C",
                "condition": "Cloudy",
                "precipitation": 30,
                "humidity": 65,
                "wind_speed": 14,
                "reroute_needed": False,
                "warning": "Mild weather. Good for exploring."
            }
        }
        
        # Get weather for destination or generate random
        for city, data in weather_data.items():
            if city in destination_lower:
                return {
                    "destination": destination,
                    "temperature": data["temperature"],
                    "condition": data["condition"],
                    "precipitation": data["precipitation"],
                    "humidity": data["humidity"],
                    "wind_speed": data["wind_speed"],
                    "reroute_needed": data["reroute_needed"],
                    "warning": data["warning"],
                    "feels_like": f"{int(data['temperature'].replace('°C', '')) - 2}°C"
                }
        
        # Random weather for unknown destinations
        conditions = ["Sunny", "Clear", "Cloudy", "Light Rain", "Partly Cloudy"]
        temp = random.randint(15, 28)
        
        return {
            "destination": destination,
            "temperature": f"{temp}°C",
            "condition": random.choice(conditions),
            "precipitation": random.randint(0, 70),
            "humidity": random.randint(40, 80),
            "wind_speed": random.randint(5, 20),
            "reroute_needed": False,
            "warning": "Weather conditions are stable. Enjoy your trip!",
            "feels_like": f"{temp - 2}°C"
        }
    
    def _fetch_weather_from_api(self, destination: str) -> Optional[dict]:
        """Fetch real weather from OpenWeatherMap API"""
        
        if not self.api_key:
            return None
        
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": destination,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]
            precipitation = data.get("rain", {}).get("1h", 0)
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            
            # Determine if reroute needed
            reroute_needed = "rain" in condition.lower() or precipitation > 50
            
            return {
                "destination": destination,
                "temperature": f"{temp:.0f}°C",
                "condition": condition.capitalize(),
                "precipitation": int(precipitation * 10),  # Convert to percentage
                "humidity": humidity,
                "wind_speed": int(wind_speed),
                "reroute_needed": reroute_needed,
                "warning": "Rain expected - consider indoor alternatives" if reroute_needed else "Weather looks good!",
                "feels_like": f"{data['main']['feels_like']:.0f}°C"
            }
            
        except Exception as e:
            print(f"OpenWeatherMap API error: {e}")
            return None


# ============= Global Function (for backward compatibility) =============

def get_destination_weather(destination: str) -> dict:
    """
    Global shortcut function for simple imports.
    Used by assistant.py and planner.py
    """
    return WeatherService.get_destination_weather(destination)


# ============= Test Function =============

if __name__ == "__main__":
    print("🌤️ Testing Weather Service...")
    
    service = WeatherService()
    
    # Test 1: Get weather for different cities
    print("\n📊 Current Weather:")
    
    for city in ["Paris", "London", "Rome", "Barcelona", "Unknown"]:
        weather = service.get_destination_weather(city)
        print(f"\n{city}:")
        print(f"  Temperature: {weather.get('temperature', 'N/A')}")
        print(f"  Condition: {weather.get('condition', 'N/A')}")
        print(f"  Precipitation: {weather.get('precipitation', 0)}%")
        print(f"  Reroute Needed: {weather.get('reroute_needed', False)}")
        print(f"  Warning: {weather.get('warning', 'No warnings')[:50]}...")
    
    # Test 2: Get forecast
    print("\n📅 5-Day Forecast (Paris):")
    forecast = service.get_forecast("Paris", 5)
    for day in forecast:
        print(f"  {day['day']} {day['date']}: {day['condition']}, {day['temperature']}")
    
    # Test 3: Check activity viability
    print("\n🏊 Activity Check (Paris):")
    activities = ["outdoor", "swimming", "hiking", "sightseeing"]
    for activity in activities:
        result = service.check_activity_viability("Paris", activity)
        print(f"  {activity}: {'✅' if result['viable'] else '❌'} - {result.get('reason', '')}")
    
    # Test 4: Clothing recommendations
    print("\n👕 Clothing Recommendations (Paris):")
    recommendations = service.get_clothing_recommendations("Paris")
    for rec in recommendations:
        print(f"  • {rec}")
    
    # Test 5: Best time to visit
    print("\n🗓️ Best Time to Visit:")
    for city in ["Paris", "Rome", "Barcelona"]:
        best = service.get_best_time_to_visit(city)
        print(f"  {city}: {best['best_months']}")
    
    print("\n✅ Weather Service tests complete!")