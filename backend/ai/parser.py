# backend/ai/parser.py

import json
import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime

# ============= Pydantic Models =============

class OptimizedHotelSelection(BaseModel):
    """Model for hotel selection with optimization details"""
    hotel_name: str = Field(description="Name of the sustainable or budget-optimized hotel match.")
    rate_per_night: float = Field(ge=0, description="The calculated price per night after dynamic engine filters.")
    smart_saving_alert: str = Field(description="Dynamic pricing tip, e.g., 'Booking 2 days later saves 25%'.")
    eco_rating: Optional[int] = Field(default=None, ge=0, le=100, description="Eco-friendliness rating 0-100")
    location: Optional[str] = Field(default=None, description="Hotel location/area")
    total_estimate: Optional[float] = Field(default=None, ge=0, description="Total estimated cost for stay")

    class Config:
        json_schema_extra = {
            "example": {
                "hotel_name": "Green Paradise Resort",
                "rate_per_night": 150.00,
                "smart_saving_alert": "Book 3 days early to save 20%",
                "eco_rating": 85,
                "location": "City Center",
                "total_estimate": 750.00
            }
        }

class DaySchedule(BaseModel):
    """Model for daily activity schedule"""
    activities: List[str] = Field(description="Sequence of daily events including cafes, museums, hidden spots, and transport shifts.")
    eco_friendly_note: str = Field(description="Summary of carbon tracking, green transport, or eco choices made for this day.")
    safety_reminder: Optional[str] = Field(default=None, description="Active alerts if passing through high-risk night zones.")
    meals: Optional[List[str]] = Field(default=None, description="Recommended meal spots for the day")
    transport_tips: Optional[List[str]] = Field(default=None, description="Transportation recommendations")
    time_allocation: Optional[Dict[str, str]] = Field(default=None, description="Time slots for activities")

    class Config:
        json_schema_extra = {
            "example": {
                "activities": ["Morning walk in park", "Visit museum", "Lunch at local cafe", "Evening market"],
                "eco_friendly_note": "Used public transport and visited eco-friendly venues",
                "safety_reminder": "Avoid the eastern district after 9 PM",
                "meals": ["Breakfast: Hotel", "Lunch: Green Cafe"],
                "transport_tips": ["Use metro line 2", "Walking distance to attractions"],
                "time_allocation": {"09:00": "Park visit", "14:00": "Museum tour"}
            }
        }

class StructuredTravelPlan(BaseModel):
    """Complete travel plan model"""
    target_destination: str = Field(description="The parsed name of the destination city or region.")
    total_estimated_cost: float = Field(ge=0, description="The sum total cost optimized against the user's upper budget bound.")
    safety_summary: str = Field(description="Overall regional security index or active scam warning overview.")
    eco_score: int = Field(ge=0, le=100, description="Overall sustainability score from 1 to 100 based on UN SDG criteria.")
    chosen_accommodation: OptimizedHotelSelection = Field(description="The selected hotel matching user profiling constraints.")
    daily_itinerary: Dict[str, DaySchedule] = Field(description="Day-by-day mapping schema (e.g., 'DAY 1', 'DAY 2').")
    
    # Optional fields
    currency: Optional[str] = Field(default="USD", description="Currency for all prices")
    total_days: Optional[int] = Field(default=None, ge=1, description="Total number of days in itinerary")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences applied")
    created_date: Optional[str] = Field(default=None, description="Plan creation date")
    version: Optional[str] = Field(default="1.0", description="Plan version")

    class Config:
        json_schema_extra = {
            "example": {
                "target_destination": "Paris",
                "total_estimated_cost": 1200.50,
                "safety_summary": "Overall safe, watch for pickpockets in tourist areas",
                "eco_score": 78,
                "currency": "EUR",
                "total_days": 3,
                "chosen_accommodation": {
                    "hotel_name": "Green Paradise Resort",
                    "rate_per_night": 150.00,
                    "smart_saving_alert": "Book 3 days early to save 20%"
                },
                "daily_itinerary": {
                    "DAY 1": {
                        "activities": ["Eiffel Tower visit", "Lunch near Louvre", "Seine River cruise"],
                        "eco_friendly_note": "Used electric boat tour",
                        "safety_reminder": "Avoid dark alleys at night"
                    }
                }
            }
        }


# ============= Parser Class =============

class ItineraryParser:
    """
    Parser for validating and processing LLM-generated travel itineraries.
    Handles various input formats and provides robust error handling.
    """
    
    @staticmethod
    def validate_and_parse_json(raw_llm_text: str) -> dict:
        """
        Takes raw string text from an LLM response, validates it against 
        the StructuredTravelPlan Pydantic model, and returns a clean Python dictionary.
        
        Args:
            raw_llm_text: Raw JSON string from LLM response
            
        Returns:
            dict: Validated and parsed travel plan
            
        Raises:
            ValueError: If parsing fails
        """
        try:
            # Clean the input text
            cleaned_text = ItineraryParser._clean_json_response(raw_llm_text)
            
            # Try to parse as JSON first
            try:
                json_data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from text
                extracted_json = ItineraryParser._extract_json_from_text(cleaned_text)
                if extracted_json:
                    json_data = json.loads(extracted_json)
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            
            # Validate against Pydantic model
            validated_data = StructuredTravelPlan.model_validate(json_data)
            
            # Add metadata
            result = validated_data.model_dump()
            result["_parsed"] = True
            result["_timestamp"] = datetime.now().isoformat()
            
            return result
            
        except ValidationError as e:
            # Handle Pydantic validation errors
            error_details = ItineraryParser._format_validation_errors(e)
            raise ValueError(f"Validation failed: {error_details}")
            
        except Exception as e:
            raise ValueError(f"Failed to parse itinerary: {str(e)}")

    @staticmethod
    def validate_and_parse_dict(raw_data: dict) -> dict:
        """
        Validates a dictionary against the StructuredTravelPlan model.
        
        Args:
            raw_data: Dictionary to validate
            
        Returns:
            dict: Validated travel plan
        """
        try:
            validated_data = StructuredTravelPlan.model_validate(raw_data)
            result = validated_data.model_dump()
            result["_parsed"] = True
            result["_timestamp"] = datetime.now().isoformat()
            return result
            
        except ValidationError as e:
            error_details = ItineraryParser._format_validation_errors(e)
            raise ValueError(f"Validation failed: {error_details}")

    @staticmethod
    def parse_individual_components(data: dict) -> dict:
        """
        Parses and validates individual components separately.
        Useful when you have partial data or want to validate step by step.
        
        Args:
            data: Dictionary with travel plan components
            
        Returns:
            dict: Parsed components with validation results
        """
        result = {}
        errors = []
        
        # Validate hotel selection if present
        if "chosen_accommodation" in data:
            try:
                hotel = OptimizedHotelSelection.model_validate(data["chosen_accommodation"])
                result["chosen_accommodation"] = hotel.model_dump()
                result["chosen_accommodation_valid"] = True
            except ValidationError as e:
                errors.append(f"Hotel validation failed: {e}")
                result["chosen_accommodation_valid"] = False
                result["chosen_accommodation"] = data["chosen_accommodation"]
        
        # Validate daily itinerary if present
        if "daily_itinerary" in data:
            validated_days = {}
            for day, schedule in data["daily_itinerary"].items():
                try:
                    day_schedule = DaySchedule.model_validate(schedule)
                    validated_days[day] = day_schedule.model_dump()
                except ValidationError as e:
                    errors.append(f"{day} validation failed: {e}")
                    validated_days[day] = schedule
            result["daily_itinerary"] = validated_days
        
        # Validate full plan if possible
        try:
            full_plan = StructuredTravelPlan.model_validate(data)
            result["full_plan_valid"] = True
            result["full_plan"] = full_plan.model_dump()
        except ValidationError as e:
            errors.append(f"Full plan validation failed: {e}")
            result["full_plan_valid"] = False
            result["full_plan"] = data
        
        result["errors"] = errors if errors else []
        result["has_errors"] = bool(errors)
        
        return result

    @staticmethod
    def create_empty_plan(destination: str) -> dict:
        """
        Creates an empty but valid travel plan structure.
        
        Args:
            destination: Destination city
            
        Returns:
            dict: Empty travel plan template
        """
        empty_plan = StructuredTravelPlan(
            target_destination=destination,
            total_estimated_cost=0.0,
            safety_summary="Safety information pending",
            eco_score=50,
            chosen_accommodation=OptimizedHotelSelection(
                hotel_name="Pending selection",
                rate_per_night=0.0,
                smart_saving_alert="No savings available"
            ),
            daily_itinerary={
                "DAY 1": DaySchedule(
                    activities=["Plan your day"],
                    eco_friendly_note="Eco-friendly options pending",
                    safety_reminder="Standard precautions recommended"
                )
            }
        )
        result = empty_plan.model_dump()
        result["_parsed"] = True
        result["_is_template"] = True
        return result

    @staticmethod
    def calculate_summary_stats(plan: dict) -> dict:
        """
        Calculates summary statistics from a parsed travel plan.
        
        Args:
            plan: Parsed travel plan dictionary
            
        Returns:
            dict: Summary statistics
        """
        stats = {
            "total_days": len(plan.get("daily_itinerary", {})),
            "total_activities": 0,
            "total_cost": plan.get("total_estimated_cost", 0),
            "eco_score": plan.get("eco_score", 0),
            "avg_cost_per_day": 0,
            "safe_zones": 0,
            "total_zones": 0
        }
        
        # Count activities
        for day, schedule in plan.get("daily_itinerary", {}).items():
            if isinstance(schedule, dict):
                activities = schedule.get("activities", [])
                stats["total_activities"] += len(activities)
                
                # Check safety reminders
                if schedule.get("safety_reminder"):
                    stats["total_zones"] += 1
                    if "avoid" not in schedule["safety_reminder"].lower():
                        stats["safe_zones"] += 1
        
        # Calculate average cost per day
        if stats["total_days"] > 0:
            stats["avg_cost_per_day"] = stats["total_cost"] / stats["total_days"]
        
        return stats

    # ============= Helper Methods =============

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """
        Clean and prepare JSON response from LLM.
        """
        # Remove code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*', '', text)
        
        # Clean whitespace
        text = text.strip()
        
        return text

    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[str]:
        """
        Extract JSON from a text that might contain other content.
        """
        # Try to find JSON between curly braces
        matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if matches:
            # Find the largest JSON object
            return max(matches, key=len)
        
        # Try to find JSON between square brackets
        matches = re.findall(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text)
        if matches:
            return max(matches, key=len)
        
        return None

    @staticmethod
    def _format_validation_errors(errors: ValidationError) -> str:
        """
        Format Pydantic validation errors for user display.
        """
        error_messages = []
        for error in errors.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        return "; ".join(error_messages)

    @staticmethod
    def merge_plans(plan1: dict, plan2: dict) -> dict:
        """
        Merge two travel plans, with plan2 taking precedence.
        
        Args:
            plan1: Base travel plan
            plan2: Override travel plan
            
        Returns:
            dict: Merged travel plan
        """
        merged = plan1.copy()
        
        # Merge top-level fields
        for key, value in plan2.items():
            if key.startswith("_"):  # Skip metadata
                continue
            if key == "daily_itinerary" and key in merged:
                # Merge daily itinerary
                merged_days = merged["daily_itinerary"].copy()
                for day, schedule in value.items():
                    if isinstance(schedule, dict):
                        # Merge day schedules
                        if day in merged_days:
                            merged_days[day].update(schedule)
                        else:
                            merged_days[day] = schedule
                merged["daily_itinerary"] = merged_days
            elif isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Recursively merge nested dictionaries
                merged[key] = ItineraryParser.merge_plans(merged[key], value)
            else:
                merged[key] = value
        
        return merged


# ============= Example Usage =============

if __name__ == "__main__":
    # Example 1: Parse a valid JSON
    valid_json = """
    {
        "target_destination": "Paris",
        "total_estimated_cost": 1200.50,
        "safety_summary": "Generally safe, watch for pickpockets",
        "eco_score": 78,
        "chosen_accommodation": {
            "hotel_name": "Green Paradise Resort",
            "rate_per_night": 150.00,
            "smart_saving_alert": "Book 3 days early to save 20%"
        },
        "daily_itinerary": {
            "DAY 1": {
                "activities": ["Eiffel Tower visit", "Lunch near Louvre"],
                "eco_friendly_note": "Used electric boat tour",
                "safety_reminder": "Avoid dark alleys at night"
            }
        }
    }
    """
    
    try:
        parsed = ItineraryParser.validate_and_parse_json(valid_json)
        print("✅ Successfully parsed JSON:")
        print(json.dumps(parsed, indent=2))
    except ValueError as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Create an empty plan
    empty_plan = ItineraryParser.create_empty_plan("Rome")
    print("\n📋 Empty Plan Template:")
    print(json.dumps(empty_plan, indent=2))
    
    # Example 3: Calculate summary stats
    stats = ItineraryParser.calculate_summary_stats(parsed)
    print(f"\n📊 Summary Statistics:")
    print(json.dumps(stats, indent=2))