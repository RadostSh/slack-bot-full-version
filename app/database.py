"""
SashiDo database integration.
Stores each bot response as a record in the SashiDo app database.
Saves conversation history for incident communications.
"""

from typing import Dict, Optional
import httpx
from app.config import get_settings


class DatabaseService:
    """Service for storing bot responses in SashiDo database."""
    
    def __init__(self):
        """Initialize SashiDo app connection with credentials."""
        settings = get_settings()
        self.app_id = settings.sashido_app_id
        self.rest_key = settings.sashido_rest_key
        self.api_url = settings.sashido_api_url.rstrip('/')
        self.headers = {
            'X-Parse-Application-Id': self.app_id,
            'X-Parse-REST-API-Key': self.rest_key,
            'Content-Type': 'application/json'
        }
        # Use httpx client for synchronous requests
        self.client = httpx.Client(timeout=30.0)
    
    def save_incident_message(
        self,
        incident_text: str,
        customer_message: str,
        internal_message: str,
        slack_user_id: str,
        slack_channel_id: str,
        source: str = "slack"
    ) -> Optional[Dict]:
        """
        Save this incident message into the SashiDo app database.
        Stores each incident message as a record.
        
        Args:
            incident_text: The incident description text from user
            customer_message: Customer-facing message (for status page or email)
            internal_message: Internal message for the support team
            slack_user_id: Slack user who requested the bot help
            slack_channel_id: Slack channel where the conversation occurred
            source: Source of the incident (default: "slack")
            
        Returns:
            Dictionary with saved record details or None on failure
        """
        # Create record with incident message data
        record = {
            "incidentText": incident_text,
            "customerMessage": customer_message,
            "internalMessage": internal_message,
            "user": slack_user_id,
            "channel": slack_channel_id,
            "source": source
        }
        
        try:
            # Store record in SashiDo app database
            response = self.client.post(
                f'{self.api_url}/classes/IncidentMessage',
                headers=self.headers,
                json=record
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error saving incident message to SashiDo database: {e}")
            return None
    

# Global database service instance
db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """Get or create SashiDo database service instance."""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service

