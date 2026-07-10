# backend/ai/memory.py

import json
import os
import sys
from dotenv import load_dotenv
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

# Load environment variables
load_dotenv()

class MemorySystemAI:
    def __init__(self):
        """
        Initialize the Memory System AI with Gemini API
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

    def recall_and_update_profile(self, existing_profile: dict, new_user_prompt: str) -> dict:
        """
        Analyzes the user's incoming travel prompt against their existing profile history.
        Extracts new insights (food interests, eco preferences, travel style) and returns
        an updated comprehensive profile dictionary.
        
        Args:
            existing_profile: dict containing user's existing profile
            new_user_prompt: string containing the user's new request
            
        Returns:
            dict: Updated user profile with new preferences merged
        """
        try:
            # Build system instruction
            system_instruction = self._build_memory_system_instruction()
            
            # Build user prompt
            user_prompt = self._build_memory_user_prompt(existing_profile, new_user_prompt)

            # Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            # Parse and return the response
            result = json.loads(response.text)
            
            # Ensure required fields exist
            result = self._validate_profile(result, existing_profile)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in memory: {str(e)}")
            return self._error_profile(existing_profile, "Failed to parse memory update")
            
        except Exception as e:
            print(f"Error in Memory System AI: {str(e)}")
            return self._error_profile(existing_profile, "Memory service temporarily unavailable")

    def generate_proactive_suggestion(self, user_profile: dict) -> dict:
        """
        Uses persistent memory records to proactively suggest destinations based on past trends.
        
        Args:
            user_profile: dict containing user's profile
            
        Returns:
            dict: Contains suggestion message and reasoning
        """
        try:
            # Build system instruction
            system_instruction = (
                "You are the AI Memory System companion for a travel platform.\n"
                "Generate a personalized recommendation based on the user's recorded preferences.\n"
                "Analyze their travel history, preferences, and past destinations to suggest new places.\n"
                "Be specific, helpful, and explain why you're making this suggestion."
            )

            # Build user prompt
            user_prompt = (
                f"User Profile: {json.dumps(user_profile, indent=2)}\n\n"
                "Based on this profile, generate a proactive travel suggestion.\n"
                "Return a JSON response with:\n"
                "1. 'suggestion': a specific destination or activity recommendation\n"
                "2. 'reasoning': why this matches their preferences\n"
                "3. 'confidence_score': number between 0-1\n"
                "4. 'message': a friendly, personalized message for the user\n"
            )

            # Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            # Parse and return the response
            result = json.loads(response.text)
            
            # Ensure all required fields
            return {
                "suggestion": result.get("suggestion", "Explore new destinations"),
                "reasoning": result.get("reasoning", "Based on your travel preferences"),
                "confidence_score": result.get("confidence_score", 0.8),
                "message": result.get("message", "We found something you might love!"),
                "success": True
            }
            
        except Exception as e:
            print(f"Error generating suggestion: {str(e)}")
            return {
                "suggestion": None,
                "reasoning": "Unable to generate suggestion at this time",
                "confidence_score": 0,
                "message": "We'll have personalized suggestions ready soon!",
                "success": False,
                "error": str(e)
            }

    def extract_user_preferences(self, user_input: str) -> dict:
        """
        Extract travel preferences from a user's natural language input.
        
        Args:
            user_input: string containing user's travel request
            
        Returns:
            dict: Extracted preferences
        """
        try:
            system_instruction = (
                "You are an AI that extracts travel preferences from natural language.\n"
                "Analyze the user's message and extract structured preferences.\n"
                "Return a JSON with these fields:\n"
                "- budget: low/medium/high/luxury\n"
                "- travel_style: backpacker/leisure/luxury/adventure\n"
                "- interests: list of interests (food, culture, nature, etc.)\n"
                "- eco_interest: low/medium/high\n"
                "- group_size: solo/couple/family/friends\n"
                "- preferred_activities: list of activity types"
            )

            user_prompt = f"Extract travel preferences from: '{user_input}'"

            # Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            print(f"Error extracting preferences: {str(e)}")
            return {
                "budget": "medium",
                "travel_style": "leisure",
                "interests": ["travel"],
                "eco_interest": "medium",
                "group_size": "couple",
                "preferred_activities": ["sightseeing"],
                "error": str(e)
            }

    def _build_memory_system_instruction(self) -> str:
        """Build system instruction for the memory AI"""
        return (
            "You are the AI Memory System layer of an advanced travel platform.\n"
            "Your job is to manage, update, and accumulate long-term user profile characteristics.\n\n"
            "Analyze the incoming user prompt to extract explicit or implicit preferences:\n"
            "- Budget thresholds (low, medium, high, luxury)\n"
            "- Travel style (backpacker, leisure, luxury, adventure)\n"
            "- Food interests (local cuisine, fine dining, street food, etc.)\n"
            "- Activity preferences (cultural, outdoor, relaxation, etc.)\n"
            "- Eco-sustainability interests (low, medium, high)\n"
            "- Group size (solo, couple, family, friends)\n\n"
            "Merge these new observations into the existing profile data structure.\n"
            "Do not overwrite older preferences unless they explicitly contradict the new prompt.\n"
            "Return the complete updated profile in valid JSON format."
        )

    def _build_memory_user_prompt(self, existing_profile: dict, new_prompt: str) -> str:
        """Build user prompt for memory update"""
        return (
            f"Existing User Profile JSON:\n{json.dumps(existing_profile, indent=2)}\n\n"
            f"New Raw User Request: '{new_prompt}'\n\n"
            "Analyze and output a fully updated and unified profile dictionary in valid JSON format.\n"
            "Maintain all existing preferences and add new ones where appropriate."
        )

    def _validate_profile(self, new_profile: dict, existing_profile: dict) -> dict:
        """Validate and ensure all required fields exist in profile"""
        required_fields = [
            "budget", "travel_style", "interests", "eco_interest", 
            "group_size", "preferred_activities", "past_destinations"
        ]
        
        for field in required_fields:
            if field not in new_profile:
                new_profile[field] = existing_profile.get(field, [])
        
        # Ensure lists are lists
        if isinstance(new_profile.get("interests"), str):
            new_profile["interests"] = [new_profile["interests"]]
        if isinstance(new_profile.get("preferred_activities"), str):
            new_profile["preferred_activities"] = [new_profile["preferred_activities"]]
        if isinstance(new_profile.get("past_destinations"), str):
            new_profile["past_destinations"] = [new_profile["past_destinations"]]
        
        return new_profile

    def _error_profile(self, existing_profile: dict, message: str) -> dict:
        """Return a graceful error profile"""
        error_profile = existing_profile.copy()
        error_profile["_error"] = message
        error_profile["_timestamp"] = str(datetime.now())
        return error_profile