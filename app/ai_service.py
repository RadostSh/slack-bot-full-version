"""
Gemini AI service for generating incident communication messages.
Handles prompt engineering and AI response parsing.
"""

import json
from typing import Dict, Optional
from google import genai
from google.genai import types
from app.config import get_settings


class AIService:
    """Service for generating incident messages using Gemini AI."""
    
    def __init__(self):
        """Initialize AI service with Gemini API."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-2.5-flash"
    
    def generate_incident_messages(self, incident_description: str) -> Optional[Dict[str, str]]:
        """
        Generate customer-facing and internal messages for an incident.
        
        Args:
            incident_description: Description of the incident from the user
            
        Returns:
            Dictionary with 'customer_message' and 'internal_message' keys,
            or None on failure
        """
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=incident_description),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    required=["customerMessage", "internalMessage"],
                    properties={
                        "customerMessage": types.Schema(
                            type=types.Type.STRING,
                            description="A clear, calm, and professional message for the public status page.",
                        ),
                        "internalMessage": types.Schema(
                            type=types.Type.STRING,
                            description="A short, concise, and technical message for the internal support team.",
                        ),
                    },
                ),
                system_instruction=[
                    types.Part.from_text(text="""You are an assistant helping DevOps teams write clear, calm, professional messages to customers during incidents.

Your only task is to read the incident description and generate two outputs:

1. A clear, calm, and professional customer-facing message for a public status page.

2. A short, concise, and technical internal message for the support team.

Always return the result as a single JSON object with keys 'customerMessage' and 'internalMessage'. Do not include any introductory or explanatory text outside the JSON object."""),
                ],
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            return self._parse_response(response.text)
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """Parse the AI response into structured format."""
        try:
            parsed = json.loads(response_text.strip())
            
            # Map from API response keys to our expected keys
            if 'customerMessage' in parsed and 'internalMessage' in parsed:
                return {
                    'customer_message': parsed['customerMessage'],
                    'internal_message': parsed['internalMessage']
                }
            else:
                print("Response missing required fields")
                return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None


# Global AI service instance
ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service

