# backend/ai/assistant.py

import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import NEW Google GenAI SDK
from google import genai

# Import services
from backend.services.weather import get_destination_weather
from backend.services.safe import SafetyService

# Load environment variables
load_dotenv()

class LiveCopilotAssistant:
    def __init__(self):
        """
        Initialize the AI Copilot Assistant with Gemini API
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

    def handle_live_disruption(self, current_itinerary: dict, disruption_event: str) -> dict:
        """
        Monitors live events and rewrites the active itinerary sections dynamically.
        
        Args:
            current_itinerary: dict containing the user's current itinerary
            disruption_event: string describing the disruption (e.g., "Heavy rain expected")
        
        Returns:
            dict: Updated itinerary with AI suggestions
        """
        try:
            destination = current_itinerary.get("destination", "Unknown")
            
            # Fetch real-time data from services
            weather_info = get_destination_weather(destination)
            safety_info = SafetyService.evaluate_zone_security(destination)

            # System instruction for the AI
            system_instruction = self._build_system_instruction(weather_info, safety_info)
            
            # User prompt with itinerary and disruption
            user_prompt = self._build_user_prompt(current_itinerary, disruption_event)

            # Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                ),
                system_instruction=system_instruction
            )
            
            # Parse and return the response
            result = json.loads(response.text)
            
            # Validate the response structure
            if "copilot_alert_message" not in result:
                result["copilot_alert_message"] = "Your itinerary has been optimized."
            
            if "updated_itinerary" not in result:
                result["updated_itinerary"] = current_itinerary
                
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return self._error_response("Failed to parse AI response", current_itinerary)
            
        except Exception as e:
            print(f"Error in AI assistant: {str(e)}")
            return self._error_response("AI service temporarily unavailable", current_itinerary)

    def _build_system_instruction(self, weather_info: dict, safety_info: dict) -> str:
        """Build system instruction for the AI"""
        return (
            "You are the Live AI Copilot layer of an intelligent travel platform.\n"
            "Your job is to handle real-time disruptions dynamically during a trip.\n"
            "Modify the user's current itinerary safely based on the disruption event provided.\n\n"
            f"Live Weather Data: {json.dumps(weather_info)}\n"
            f"Live Safety Status: {json.dumps(safety_info)}\n\n"
            "Guidelines:\n"
            "- If it rains, swap outdoor activities for indoor alternatives\n"
            "- If an area is flagged as high risk at night, suggest safer alternatives\n"
            "- Always provide clear explanations for changes\n"
            "- Maintain the original structure of the itinerary\n"
            "- Keep the updated schedule realistic (times, locations, etc.)"
        )

    def _build_user_prompt(self, itinerary: dict, disruption: str) -> str:
        """Build user prompt with itinerary and disruption"""
        return (
            f"Current Active Itinerary JSON:\n{json.dumps(itinerary, indent=2)}\n\n"
            f"Alert / Disruption Received: '{disruption}'\n\n"
            "Please optimize the itinerary based on this disruption.\n\n"
            "Return a clean JSON with:\n"
            "1. 'updated_itinerary' - the modified itinerary\n"
            "2. 'copilot_alert_message' - clear explanation for the user\n"
            "3. 'changes_made' - list of what was changed\n"
        )

    def _error_response(self, message: str, itinerary: dict) -> dict:
        """Return a graceful error response"""
        return {
            "success": False,
            "copilot_alert_message": message,
            "updated_itinerary": itinerary,
            "error": message
        }