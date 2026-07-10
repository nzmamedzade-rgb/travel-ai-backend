# backend/ai/planner.py

import json
import os
import sys
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import NEW Google GenAI SDK
from google import genai

# Import services
from backend.services.hotels import HotelService
from backend.services.safe import SafetyService
from backend.services.eco import calculate_eco_score
from backend.services.weather import get_destination_weather

# Import parser models
from backend.ai.parser import StructuredTravelPlan, ItineraryParser

# Load environment variables
load_dotenv()

class TravelPlannerAI:
    """
    Core AI Travel Planner that generates optimized multi-day itineraries
    using Google's Gemini AI with real-time data integration.
    """
    
    def __init__(self):
        """
        Initialize the Travel Planner AI with Gemini API
        """
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables!\n"
                "Please create a .env file with your API key."
            )
        
        # Initialize the NEW GenAI client
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-1.5-flash"
        
        # Initialize services
        self.hotel_service = HotelService()
        self.safety_service = SafetyService()
        
        # Cache for service calls
        self._cache = {}

    def generate_smart_itinerary(
        self, 
        user_prompt: str, 
        maximum_budget: float, 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a highly optimized multi-day travel schedule.
        
        Args:
            user_prompt: User's travel request in natural language
            maximum_budget: Maximum budget for the trip
            user_profile: User's profile with preferences
            
        Returns:
            dict: Complete structured travel plan
        """
        try:
            # Step 1: Detect destination from user prompt
            destination = self._detect_destination(user_prompt)
            
            # Step 2: Fetch real-time data from services
            service_data = self._fetch_service_data(destination)
            
            # Step 3: Build system instruction with all data
            system_instruction = self._build_system_instruction(
                destination, 
                service_data,
                maximum_budget
            )
            
            # Step 4: Build user prompt
            user_context_query = self._build_user_prompt(
                user_prompt,
                user_profile,
                maximum_budget
            )
            
            # Step 5: Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_context_query,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            # Step 6: Parse and validate the response
            try:
                # Try to parse as JSON first
                raw_data = json.loads(response.text)
                
                # Validate against our model
                validated = StructuredTravelPlan.model_validate(raw_data)
                result = validated.model_dump()
                
            except (json.JSONDecodeError, ValueError) as e:
                # If validation fails, try using the parser
                print(f"Validation error, attempting to parse: {e}")
                parser = ItineraryParser()
                result = parser.validate_and_parse_json(response.text)
            
            # Step 7: Add metadata and statistics
            result = self._enrich_plan(result, destination, maximum_budget, service_data)
            
            return result
            
        except Exception as e:
            print(f"Error generating itinerary: {str(e)}")
            # Return a fallback plan
            return self._create_fallback_plan("Unknown", maximum_budget, str(e))

    def generate_alternative_suggestions(
        self, 
        original_plan: Dict[str, Any],
        constraint_change: str
    ) -> Dict[str, Any]:
        """
        Generates alternative suggestions based on changed constraints.
        """
        try:
            system_instruction = (
                "You are an AI that generates alternative travel suggestions.\n"
                "Based on the original plan and new constraints, provide alternatives.\n"
                "Return a JSON with 'alternatives' array and 'recommendations' object."
            )
            
            user_prompt = (
                f"Original Plan: {json.dumps(original_plan, indent=2)}\n\n"
                f"Constraint Change: '{constraint_change}'\n\n"
                "Provide 3 alternative options with reasoning."
            )
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            return {
                "error": str(e),
                "alternatives": [],
                "recommendations": "Unable to generate alternatives at this time"
            }

    def optimize_existing_plan(
        self, 
        plan: Dict[str, Any],
        optimization_goal: str
    ) -> Dict[str, Any]:
        """
        Optimizes an existing travel plan for a specific goal.
        """
        try:
            system_instruction = (
                f"You are an AI that optimizes travel plans.\n"
                f"Optimization Goal: {optimization_goal}\n"
                "Return the optimized plan with explanations of changes."
            )
            
            user_prompt = f"Plan to optimize: {json.dumps(plan, indent=2)}"
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            return {
                "error": str(e),
                "plan": plan,
                "message": "Optimization failed"
            }

    # ============= Private Helper Methods =============

    def _detect_destination(self, user_prompt: str) -> str:
        """Detect destination from user prompt using AI"""
        try:
            system_instruction = (
                "Extract the destination city from the user's travel request.\n"
                "Return only the city name as a string."
            )
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"Extract destination from: '{user_prompt}'",
                config=genai.types.GenerateContentConfig(
                    temperature=0.1
                ),
                system_instruction=system_instruction
            )
            
            destination = response.text.strip()
            
            # Clean up the response
            destination = destination.replace('"', '').strip()
            
            return destination if destination else "Paris"
            
        except Exception:
            # Fallback to simple detection
            cities = ["Paris", "London", "Rome", "Barcelona", "Amsterdam", "Berlin"]
            for city in cities:
                if city.lower() in user_prompt.lower():
                    return city
            return "Paris"  # Default

    def _fetch_service_data(self, destination: str) -> Dict[str, Any]:
        """Fetch data from all services with caching"""
        cache_key = f"{destination}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            data = {
                "weather": get_destination_weather(destination),
                "safety": SafetyService.evaluate_zone_security(destination),
                "hotels": HotelService.fetch_available_hotels(destination, 1000),
                "eco_metrics": calculate_eco_score("train"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache for 5 minutes
            self._cache[cache_key] = data
            
            return data
            
        except Exception as e:
            print(f"Error fetching service data: {e}")
            return {
                "weather": {"conditions": "Unknown", "temperature": 20},
                "safety": {"risk_level": "Low", "safe_at_night": True},
                "hotels": [{"name": "Default Hotel", "price": 150}],
                "eco_metrics": {"score": 70},
                "timestamp": datetime.now().isoformat()
            }

    def _build_system_instruction(
        self, 
        destination: str, 
        service_data: Dict[str, Any],
        budget: float
    ) -> str:
        """Build comprehensive system instruction"""
        return (
            "You are the Core AI Recommendation and Optimization Engine of a travel platform.\n"
            "Your job is to generate a comprehensive, highly optimized multi-day travel plan.\n"
            "You must strictly respect the user's maximum budget and match their personal profile.\n\n"
            f"--- GROUND TRUTH DATA ---\n"
            f"Target Destination: {destination}\n"
            f"Live Weather Status: {json.dumps(service_data.get('weather', {}))}\n"
            f"Safety Alerts: {json.dumps(service_data.get('safety', {}))}\n"
            f"Available Hotel Options: {json.dumps(service_data.get('hotels', []))}\n"
            f"Eco Sustainability: {json.dumps(service_data.get('eco_metrics', {}))}\n"
            f"Budget Limit: ${budget}\n\n"
            "--- OPTIMIZATION RULES ---\n"
            "1. Budget Optimization: Maximize value without exceeding budget.\n"
            "2. Weather Optimization: If rain is forecast, suggest indoor activities.\n"
            "3. Safety Optimization: Avoid high-risk zones, especially at night.\n"
            "4. Eco Optimization: Highlight green transport and eco-friendly options.\n\n"
            "Return a structured JSON following the specified schema."
        )

    def _build_user_prompt(
        self, 
        user_prompt: str, 
        user_profile: Dict[str, Any],
        budget: float
    ) -> str:
        """Build user prompt with all constraints"""
        return (
            f"User Request: '{user_prompt}'\n\n"
            f"User Profile: {json.dumps(user_profile, indent=2)}\n\n"
            f"Maximum Budget: ${budget}\n\n"
            "Generate a complete travel itinerary with daily activities, "
            "accommodation, transportation, and cost breakdown. "
            "Ensure all activities are realistic and available at the destination."
        )

    def _enrich_plan(
        self, 
        plan: Dict[str, Any], 
        destination: str,
        budget: float,
        service_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add metadata and calculated fields to the plan"""
        enriched = plan.copy()
        
        # Add metadata
        enriched["_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "destination": destination,
            "budget_limit": budget,
            "model_used": self.model_id,
            "weather_at_generation": service_data.get("weather", {}),
            "safety_at_generation": service_data.get("safety", {})
        }
        
        # Calculate statistics
        parser = ItineraryParser()
        stats = parser.calculate_summary_stats(enriched)
        enriched["_stats"] = stats
        
        return enriched

    def _create_fallback_plan(self, destination: str, budget: float, error: str) -> Dict[str, Any]:
        """Create a fallback plan when generation fails"""
        parser = ItineraryParser()
        fallback = parser.create_empty_plan(destination)
        
        fallback["_error"] = error
        fallback["_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "destination": destination,
            "budget_limit": budget,
            "is_fallback": True,
            "error_message": error
        }
        
        return fallback