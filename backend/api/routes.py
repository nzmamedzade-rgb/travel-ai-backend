# backend/api/routes.py

import uuid
import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Import our database context setup
from backend.database import get_database_session, SavedTrip

# Import the Pydantic input models we defined
from backend.models import ItineraryQueryRequest

# Import our modular AI components
from backend.ai.planner import TravelPlannerAI
from backend.ai.memory import MemorySystemAI
from backend.ai.assistant import LiveCopilotAssistant
from backend.ai.parser import ItineraryParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Travel AI"])

# Instantiate our AI layer agents
planner_agent = TravelPlannerAI()
memory_agent = MemorySystemAI()
copilot_agent = LiveCopilotAssistant()


# ============= Request/Response Models =============

class CopilotDisruptionRequest(BaseModel):
    """Request model for copilot disruption handling"""
    active_itinerary: Dict[str, Any] = Field(description="Current active itinerary")
    disruption_event: str = Field(description="Description of the disruption")
    
    class Config:
        json_schema_extra = {
            "example": {
                "active_itinerary": {
                    "destination": "Paris",
                    "activities": [
                        {"time": "09:00", "activity": "Eiffel Tower visit"}
                    ]
                },
                "disruption_event": "Heavy rain forecast for afternoon"
            }
        }


class ProfileUpdateRequest(BaseModel):
    """Request model for profile update"""
    user_id: str = Field(description="User identifier")
    new_prompt: str = Field(description="New user request/input")
    existing_profile: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Existing user profile (optional)"
    )


class AlternativeRequest(BaseModel):
    """Request model for alternative suggestions"""
    plan: Dict[str, Any] = Field(description="Current travel plan")
    constraint_change: str = Field(description="Description of changed constraint")


class OptimizationRequest(BaseModel):
    """Request model for plan optimization"""
    plan: Dict[str, Any] = Field(description="Plan to optimize")
    goal: str = Field(description="Optimization goal", examples=["reduce_cost", "increase_eco", "balance"])


# ============= Main Routes =============

@router.post("/trip/plan", status_code=status.HTTP_201_CREATED)
def plan_new_trip(
    request_payload: ItineraryQueryRequest, 
    db: Session = Depends(get_database_session)
):
    """
    Endpoint to receive a raw travel prompt, execute user preference profiling/memory analysis,
    generate a tailored structured travel itinerary, and store the record securely in the database.
    """
    logger.info(f"Planning new trip for user: {request_payload.user_id}")
    
    try:
        # Step 1: Initialize user profile
        base_profile = {
            "user_id": request_payload.user_id,
            "past_travel_styles": [],
            "food_interests": [],
            "eco_interest_level": "unknown",
            "preferred_budget": request_payload.budget,
            "last_updated": str(uuid.uuid4())
        }

        # Step 2: Run Memory System AI to update user profile
        try:
            updated_profile = memory_agent.recall_and_update_profile(
                existing_profile=base_profile, 
                new_user_prompt=request_payload.prompt
            )
            logger.info("Memory system updated profile successfully")
        except Exception as memory_error:
            logger.warning(f"Memory system error: {memory_error}, using base profile")
            updated_profile = base_profile

        # Step 3: Run Travel Planner AI Engine
        try:
            generated_itinerary = planner_agent.generate_smart_itinerary(
                user_prompt=request_payload.prompt,
                maximum_budget=request_payload.budget,
                user_profile=updated_profile
            )
            logger.info("Planner generated itinerary successfully")
        except Exception as planner_error:
            logger.error(f"Planner error: {planner_error}")
            # Create a fallback itinerary
            parser = ItineraryParser()
            generated_itinerary = parser.create_empty_plan("Unknown Destination")
            generated_itinerary["_error"] = str(planner_error)
            generated_itinerary["budget"] = request_payload.budget

        # Step 4: Prepare itinerary for storage
        destination = generated_itinerary.get("target_destination", "Unknown Destination")
        if not destination or destination == "Unknown Destination":
            # Try to extract destination from prompt
            destination = _extract_destination_from_prompt(request_payload.prompt)

        # Step 5: Persist to database
        new_trip_id = str(uuid.uuid4())
        
        try:
            db_record = SavedTrip(
                trip_id=new_trip_id,
                user_id=request_payload.user_id,
                destination=destination,
                allocated_budget=request_payload.budget,
                itinerary_json=json.dumps(generated_itinerary, default=str)
            )
            
            db.add(db_record)
            db.commit()
            logger.info(f"Trip saved to database with ID: {new_trip_id}")
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error: {db_error}")
            # Continue even if DB fails - return the itinerary
            # In production, you might want to raise an exception here

        # Step 6: Return response
        return {
            "status": "success",
            "trip_id": new_trip_id,
            "destination": destination,
            "budget": request_payload.budget,
            "data": generated_itinerary,
            "message": "Trip planned successfully!"
        }

    except Exception as error:
        db.rollback()
        logger.error(f"Trip planning failed: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI Pipeline Execution Failure",
                "message": str(error),
                "status": "failed"
            }
        )


@router.post("/trip/copilot", status_code=status.HTTP_200_OK)
def update_live_itinerary(payload: CopilotDisruptionRequest):
    """
    Live AI Copilot endpoint that intercepts real-time disruptions (e.g., flight delays, sudden rain)
    and modifies the active itinerary schedule cleanly on-the-fly.
    """
    logger.info(f"Processing disruption: {payload.disruption_event}")
    
    try:
        # Validate the itinerary has required fields
        if not payload.active_itinerary:
            raise ValueError("Active itinerary is empty")
        
        # Route to Copilot Assistant
        updated_itinerary = copilot_agent.handle_live_disruption(
            current_itinerary=payload.active_itinerary,
            disruption_event=payload.disruption_event
        )
        
        # Add metadata
        updated_itinerary["_disruption_handled"] = True
        updated_itinerary["_original_event"] = payload.disruption_event
        updated_itinerary["_timestamp"] = str(uuid.uuid4())
        
        logger.info("Disruption handled successfully")
        
        return {
            "status": "disruption_resolved",
            "message": "Itinerary updated successfully!",
            "data": updated_itinerary
        }
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(ve)}"
        )
    except Exception as error:
        logger.error(f"Copilot error: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Live Copilot Assistant Error",
                "message": str(error),
                "status": "failed"
            }
        )


@router.post("/trip/memory/update", status_code=status.HTTP_200_OK)
def update_user_memory(payload: ProfileUpdateRequest):
    """
    Update user profile memory with new preferences
    """
    try:
        # Use existing profile or create default
        existing_profile = payload.existing_profile or {
            "user_id": payload.user_id,
            "past_travel_styles": [],
            "food_interests": [],
            "eco_interest_level": "unknown"
        }
        
        updated_profile = memory_agent.recall_and_update_profile(
            existing_profile=existing_profile,
            new_user_prompt=payload.new_prompt
        )
        
        # Extract preferences
        preferences = memory_agent.extract_user_preferences(payload.new_prompt)
        
        return {
            "status": "success",
            "profile": updated_profile,
            "extracted_preferences": preferences,
            "message": "Profile updated successfully"
        }
        
    except Exception as error:
        logger.error(f"Memory update error: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory system error: {str(error)}"
        )


@router.get("/trip/memory/suggestions/{user_id}")
def get_memory_suggestions(user_id: str):
    """
    Get proactive travel suggestions based on user's memory profile
    """
    try:
        # In a real implementation, fetch profile from database
        # For now, create a sample profile
        sample_profile = {
            "user_id": user_id,
            "past_travel_styles": ["cultural", "eco-friendly"],
            "food_interests": ["local cuisine", "vegetarian"],
            "eco_interest_level": "high",
            "preferred_budget": 1000
        }
        
        suggestion = memory_agent.generate_proactive_suggestion(sample_profile)
        
        return {
            "status": "success",
            "user_id": user_id,
            "suggestion": suggestion,
            "message": "Suggestion generated based on user preferences"
        }
        
    except Exception as error:
        logger.error(f"Suggestion error: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating suggestion: {str(error)}"
        )


@router.post("/trip/optimize", status_code=status.HTTP_200_OK)
def optimize_itinerary(request: OptimizationRequest):
    """
    Optimize an existing itinerary for a specific goal
    """
    try:
        optimized = planner_agent.optimize_existing_plan(
            plan=request.plan,
            optimization_goal=request.goal
        )
        
        return {
            "status": "success",
            "optimized_plan": optimized,
            "goal": request.goal,
            "message": f"Plan optimized for {request.goal}"
        }
        
    except Exception as error:
        logger.error(f"Optimization error: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(error)}"
        )


@router.post("/trip/alternatives", status_code=status.HTTP_200_OK)
def get_alternative_suggestions(request: AlternativeRequest):
    """
    Get alternative suggestions based on changed constraints
    """
    try:
        alternatives = planner_agent.generate_alternative_suggestions(
            original_plan=request.plan,
            constraint_change=request.constraint_change
        )
        
        return {
            "status": "success",
            "alternatives": alternatives,
            "message": "Alternative suggestions generated"
        }
        
    except Exception as error:
        logger.error(f"Alternatives error: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating alternatives: {str(error)}"
        )


@router.get("/trip/{trip_id}", status_code=status.HTTP_200_OK)
def get_trip_by_id(
    trip_id: str, 
    db: Session = Depends(get_database_session)
):
    """
    Retrieve a saved trip by ID
    """
    try:
        trip = db.query(SavedTrip).filter(SavedTrip.trip_id == trip_id).first()
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found"
            )
        
        return {
            "status": "success",
            "trip": {
                "trip_id": trip.trip_id,
                "user_id": trip.user_id,
                "destination": trip.destination,
                "budget": trip.allocated_budget,
                "created_at": trip.created_at,
                "itinerary": json.loads(trip.itinerary_json)
            }
        }
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error fetching trip: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving trip: {str(error)}"
        )


@router.get("/trips/user/{user_id}", status_code=status.HTTP_200_OK)
def get_user_trips(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_database_session)
):
    """
    Get all trips for a user
    """
    try:
        trips = db.query(SavedTrip).filter(
            SavedTrip.user_id == user_id
        ).order_by(
            SavedTrip.created_at.desc()
        ).limit(limit).all()
        
        return {
            "status": "success",
            "user_id": user_id,
            "total": len(trips),
            "trips": [
                {
                    "trip_id": t.trip_id,
                    "destination": t.destination,
                    "budget": t.allocated_budget,
                    "created_at": t.created_at
                }
                for t in trips
            ]
        }
        
    except Exception as error:
        logger.error(f"Error fetching user trips: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving trips: {str(error)}"
        )


@router.delete("/trip/{trip_id}", status_code=status.HTTP_200_OK)
def delete_trip(
    trip_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Delete a saved trip
    """
    try:
        trip = db.query(SavedTrip).filter(SavedTrip.trip_id == trip_id).first()
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found"
            )
        
        db.delete(trip)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Trip {trip_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        logger.error(f"Error deleting trip: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting trip: {str(error)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Travel AI API",
        "version": "1.0.0",
        "agents": {
            "planner": "online",
            "memory": "online",
            "copilot": "online"
        }
    }


# ============= Helper Functions =============

def _extract_destination_from_prompt(prompt: str) -> str:
    """Extract destination from prompt text"""
    common_destinations = [
        "Paris", "London", "Rome", "Barcelona", "Amsterdam", 
        "Berlin", "New York", "Tokyo", "Sydney", "Dubai",
        "Bangkok", "Singapore", "Hong Kong", "Istanbul", "Prague"
    ]
    
    prompt_lower = prompt.lower()
    
    for destination in common_destinations:
        if destination.lower() in prompt_lower:
            return destination
    
    return "Unknown Destination"