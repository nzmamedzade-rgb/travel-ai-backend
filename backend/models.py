# backend/models.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class ItineraryQueryRequest(BaseModel):
    """
    Data validation schema for parsing inbound raw text requests 
    passed to the primary travel planner engine endpoint.
    """
    user_id: str = Field(
        ..., 
        description="The unique identifier string belonging to the active traveling profile user."
    )
    prompt: str = Field(
        ..., 
        min_length=10,
        description="The raw itinerary generation text request (e.g., '3 days in Paris under $500')."
    )
    budget: float = Field(
        ..., 
        gt=0.0, 
        description="The upper boundary allocation caps for transport, tickets, and lodging pricing validation."
    )
    
    # Optional fields
    destination: Optional[str] = Field(
        None, 
        description="Specific destination if already known"
    )
    start_date: Optional[str] = Field(
        None, 
        description="Start date of the trip (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None, 
        description="End date of the trip (YYYY-MM-DD)"
    )
    travelers: int = Field(
        2, 
        ge=1, 
        description="Number of travelers"
    )


class ActivityItem(BaseModel):
    """
    Structured model for specific timed agenda points inside a day breakdown.
    """
    time_slot: str = Field(
        ..., 
        description="The planned execution timeframe slot (e.g., '09:00 - 11:30')."
    )
    activity_name: str = Field(
        ..., 
        description="Name of the venue, route destination, or monument visit."
    )
    cost: float = Field(
        default=0.0, 
        ge=0.0,
        description="Estimated local dynamic expense associated with this item."
    )
    eco_friendly: bool = Field(
        default=False, 
        description="Flag indicating if the venue passes local sustainability metrics."
    )
    safety_note: Optional[str] = Field(
        None, 
        description="Defensive copilot warnings or pickpocket advisory tips for the zone."
    )
    location: Optional[str] = Field(
        None, 
        description="Address or location of the activity"
    )
    duration_minutes: Optional[int] = Field(
        None, 
        ge=0,
        description="Estimated duration in minutes"
    )
    
    @validator('time_slot')
    def validate_time_slot(cls, v):
        """Validate time slot format"""
        import re
        if not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$', v):
            # Allow simpler format like "09:00" or "Morning"
            pass
        return v


class DailySchedule(BaseModel):
    """
    Aggregates targeted sequential events inside an isolated singular travel date.
    """
    day_number: int = Field(
        ..., 
        ge=1,
        description="The sequence day marker index (e.g., Day 1, Day 2)."
    )
    date_label: Optional[str] = Field(
        None, 
        description="Formatted target calendar stamp string."
    )
    activities: List[ActivityItem] = Field(
        default_factory=list, 
        description="Ordered list of structured venue itineraries."
    )
    total_cost: float = Field(
        default=0.0, 
        ge=0.0,
        description="Total cost for this day"
    )
    eco_tip: Optional[str] = Field(
        None, 
        description="Eco-friendly tip for this day"
    )
    safety_reminder: Optional[str] = Field(
        None, 
        description="Safety reminder for this day"
    )
    
    @validator('total_cost', always=True)
    def calculate_total_cost(cls, v, values):
        """Auto-calculate total cost from activities"""
        if 'activities' in values:
            total = sum(activity.cost for activity in values['activities'])
            return total
        return v


class TripItineraryResponse(BaseModel):
    """
    The ultimate multi-agent structural engine response object payload layout returned to frontend systems.
    """
    target_destination: str = Field(
        ..., 
        description="The parsed geographical city or area destination."
    )
    total_estimated_cost: float = Field(
        ..., 
        ge=0.0,
        description="Aggregated calculated expenses across flights, hotels, and sights."
    )
    sustainability_rating: int = Field(
        ..., 
        ge=0, 
        le=100,
        description="Calculated metric scoring structural eco weights."
    )
    itinerary_days: List[DailySchedule] = Field(
        ..., 
        description="The chronologically organized multi-day itinerary array breakdown."
    )
    
    # Optional additional fields
    currency: str = Field(
        default="USD", 
        description="Currency code for all prices"
    )
    total_days: int = Field(
        default=1, 
        ge=1,
        description="Total number of days in the itinerary"
    )
    flight_cost: float = Field(
        default=0.0, 
        ge=0.0,
        description="Estimated flight cost"
    )
    hotel_cost: float = Field(
        default=0.0, 
        ge=0.0,
        description="Estimated hotel cost"
    )
    activities_cost: float = Field(
        default=0.0, 
        ge=0.0,
        description="Estimated activities cost"
    )
    copilot_tips: List[str] = Field(
        default_factory=list, 
        description="Tips from the AI copilot"
    )
    
    @validator('total_days', always=True)
    def calculate_total_days(cls, v, values):
        """Auto-calculate total days from itinerary_days"""
        if 'itinerary_days' in values and values['itinerary_days']:
            return len(values['itinerary_days'])
        return v
    
    @validator('total_estimated_cost', always=True)
    def calculate_total_cost(cls, v, values):
        """Auto-calculate total cost from components"""
        if 'flight_cost' in values and 'hotel_cost' in values and 'activities_cost' in values:
            total = values['flight_cost'] + values['hotel_cost'] + values['activities_cost']
            return total
        return v


# ============= Additional Models =============

class CopilotDisruptionRequest(BaseModel):
    """
    Request model for copilot disruption handling.
    """
    active_itinerary: Dict[str, Any] = Field(
        ..., 
        description="Current active itinerary"
    )
    disruption_event: str = Field(
        ..., 
        min_length=3,
        description="Description of the disruption (e.g., 'Heavy rain forecast')"
    )
    user_id: Optional[str] = Field(
        None, 
        description="Optional user ID for personalized response"
    )


class CopilotDisruptionResponse(BaseModel):
    """
    Response model for copilot disruption handling.
    """
    status: str = Field(
        ..., 
        description="Status of the disruption handling"
    )
    updated_itinerary: Dict[str, Any] = Field(
        ..., 
        description="Updated itinerary after disruption"
    )
    copilot_message: str = Field(
        ..., 
        description="Message from the copilot explaining changes"
    )
    changes_summary: List[str] = Field(
        default_factory=list, 
        description="Summary of changes made"
    )


class HotelSearchRequest(BaseModel):
    """
    Request model for hotel search.
    """
    destination: str = Field(
        ..., 
        min_length=2,
        description="Destination city"
    )
    budget: float = Field(
        ..., 
        gt=0.0,
        description="Maximum budget per night"
    )
    check_in: Optional[str] = Field(
        None, 
        description="Check-in date (YYYY-MM-DD)"
    )
    check_out: Optional[str] = Field(
        None, 
        description="Check-out date (YYYY-MM-DD)"
    )
    guests: int = Field(
        2, 
        ge=1,
        description="Number of guests"
    )
    eco_only: bool = Field(
        False, 
        description="Only show eco-friendly hotels"
    )
    min_rating: Optional[float] = Field(
        None, 
        ge=0, 
        le=5,
        description="Minimum rating (0-5)"
    )


class FlightSearchRequest(BaseModel):
    """
    Request model for flight search.
    """
    destination: str = Field(
        ..., 
        min_length=2,
        description="Destination city"
    )
    origin: Optional[str] = Field(
        None, 
        description="Origin city"
    )
    budget: float = Field(
        ..., 
        gt=0.0,
        description="Maximum budget"
    )
    departure_date: Optional[str] = Field(
        None, 
        description="Departure date (YYYY-MM-DD)"
    )
    return_date: Optional[str] = Field(
        None, 
        description="Return date (YYYY-MM-DD)"
    )
    passengers: int = Field(
        1, 
        ge=1,
        description="Number of passengers"
    )


class UserProfileUpdateRequest(BaseModel):
    """
    Request model for updating user profile.
    """
    user_id: str = Field(
        ..., 
        description="User identifier"
    )
    new_prompt: str = Field(
        ..., 
        min_length=3,
        description="New user input to extract preferences from"
    )
    existing_profile: Optional[Dict[str, Any]] = Field(
        None, 
        description="Existing user profile (optional)"
    )


class MemorySuggestionResponse(BaseModel):
    """
    Response model for memory system suggestions.
    """
    suggestion: str = Field(
        ..., 
        description="The suggestion message"
    )
    reasoning: str = Field(
        ..., 
        description="Reasoning behind the suggestion"
    )
    confidence_score: float = Field(
        ..., 
        ge=0, 
        le=1,
        description="Confidence score (0-1)"
    )
    message: str = Field(
        ..., 
        description="Friendly message for the user"
    )
    success: bool = Field(
        True, 
        description="Whether the suggestion was generated successfully"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if any"
    )


class HealthCheckResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(
        ..., 
        description="Health status (healthy/unhealthy)"
    )
    engine_status: str = Field(
        ..., 
        description="Engine status"
    )
    database_connectivity: str = Field(
        ..., 
        description="Database connectivity status"
    )
    active_version: str = Field(
        ..., 
        description="API version"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of health check"
    )


# ============= Type Aliases =============

# For simple responses
TripPlanResponse = Dict[str, Any]
ServiceResponse = Dict[str, Any]


# ============= Test =============

if __name__ == "__main__":
    print("📝 Testing Models...")
    
    # Test ItineraryQueryRequest
    try:
        req = ItineraryQueryRequest(
            user_id="user123",
            prompt="3 days in Paris under $500",
            budget=500.0
        )
        print("✅ ItineraryQueryRequest validated")
        print(f"   User: {req.user_id}, Budget: ${req.budget}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test ActivityItem
    activity = ActivityItem(
        time_slot="09:00 - 11:00",
        activity_name="Eiffel Tower Visit",
        cost=25.0,
        eco_friendly=True
    )
    print(f"✅ ActivityItem: {activity.activity_name} (${activity.cost})")
    
    # Test DailySchedule
    day = DailySchedule(
        day_number=1,
        activities=[activity],
        date_label="Day 1"
    )
    print(f"✅ DailySchedule: Day {day.day_number}, {len(day.activities)} activities")
    print(f"   Total cost: ${day.total_cost}")
    
    print("\n✅ Models test complete!")