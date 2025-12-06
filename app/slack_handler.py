"""
Slack bot event handlers using Bolt framework.
Handles app mentions and message formatting.
"""

from typing import Dict, Optional, Any, Callable
import logging
from slack_bolt import App, Say, Ack, Respond
from app.config import get_settings
from app.ai_service import get_ai_service
from app.database import get_db_service


class IncidentProcessor:
    """Handles incident message processing logic."""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.db_service = get_db_service()
    
    def extract_incident_description(self, text: str, remove_mention: bool = True) -> str:
        """
        Extract incident description from text.
        
        Args:
            text: Raw text from Slack event
            remove_mention: If True, removes the first word (bot mention)
            
        Returns:
            Cleaned incident description
        """
        if not text:
            return ""
        
        text = text.strip()
        
        if remove_mention:
            # Split only at the first space, keeping the rest intact
            parts = text.split(maxsplit=1)
            return parts[1] if len(parts) > 1 else ""
        
        return text
    
    def validate_description(self, description: str) -> bool:
        """Check if incident description is valid."""
        return bool(description and len(description.strip()) > 0)
    
    def generate_messages(self, incident_description: str) -> Optional[Dict[str, str]]:
        """
        Generate AI messages for the incident.
        
        Args:
            incident_description: The incident description
            
        Returns:
            Dictionary with customer_message and internal_message, or None on failure
        """
        try:
            return self.ai_service.generate_incident_messages(incident_description)
        except Exception as e:
            logging.error(f"AI service error: {e}")
            return None
    
    def save_incident(
        self,
        incident_text: str,
        customer_message: str,
        internal_message: str,
        slack_user_id: str,
        slack_channel_id: str,
    ) -> bool:
        """
        Save incident to database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.db_service.save_incident_message(
                incident_text=incident_text,
                customer_message=customer_message,
                internal_message=internal_message,
                slack_user_id=slack_user_id,
                slack_channel_id=slack_channel_id,
            )
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            return False
    
    def process_incident(
        self,
        incident_description: str,
        user_id: str,
        channel_id: str,
        logger: logging.Logger,
        send_message: Callable[[str], Any],
        update_message: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """
        Process an incident: validate, generate messages, format, and save.
        
        Args:
            incident_description: The incident description
            user_id: Slack user ID
            channel_id: Slack channel ID
            logger: Logger instance
            send_message: Callback function to send messages (returns response with 'ts')
            update_message: Optional callback function to update existing messages
            
        Returns:
            True if successful, False otherwise
        """
        # Validate description
        if not self.validate_description(incident_description):
            send_message("Please provide an incident description.")
            return False
        
        # Show processing indicator
        response = send_message("Generating incident communication messages...")
        processing_ts = response.get("ts") if response else None
        
        # Generate messages using AI
        messages = self.generate_messages(incident_description)
        
        if not messages or not messages.get("customer_message") or not messages.get("internal_message"):
            error_msg = "Sorry, I encountered an error generating the messages. Please try again."
            if update_message and processing_ts:
                update_message(processing_ts, error_msg)
            else:
                send_message(error_msg)
            logger.warning(f"Failed to generate messages for user {user_id}")
            return False
        
        # Format and send response
        response_text = format_response(
            messages["customer_message"],
            messages["internal_message"]
        )
        
        # Update the processing message with the final response
        if update_message and processing_ts:
            update_message(processing_ts, response_text)
        else:
            send_message(response_text)
        
        # Save to database
        save_success = self.save_incident(
            incident_text=incident_description,
            customer_message=messages["customer_message"],
            internal_message=messages["internal_message"],
            slack_user_id=user_id,
            slack_channel_id=channel_id,
        )
        
        if save_success:
            logger.info(
                f"Successfully processed incident from user {user_id} in channel {channel_id}"
            )
        else:
            logger.warning(
                f"Incident processed but failed to save to database for user {user_id}"
            )
        
        return True


def create_slack_app() -> App:
    """Create and configure the Slack Bolt app."""
    settings = get_settings()
    
    app = App(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret,
    )
    
    processor = IncidentProcessor()
    
    @app.event("app_mention")
    def handle_app_mention(event: Dict[str, Any], say: Say, logger: logging.Logger, client):
        """
        Handle when the bot is mentioned in a channel.
        Extracts incident description, generates messages, and responds in thread.
        
        Args:
            event: Slack event payload
            say: Function to send messages to Slack
            logger: Logger instance
            client: Slack client for API calls
        """
        thread_ts = event.get("ts")
        user_id = event.get("user")
        channel_id = event.get("channel")
        
        try:
            # Extract incident description (remove bot mention)
            text = event.get("text", "")
            incident_description = processor.extract_incident_description(text, remove_mention=True)
            
            # Create a closure to send messages in thread
            def send_message(message: str):
                return say(text=message, thread_ts=thread_ts)
            
            # Create a closure to update messages
            def update_message(message_ts: str, new_text: str):
                client.chat_update(
                    channel=channel_id,
                    ts=message_ts,
                    text=new_text
                )
            
            # Process the incident
            processor.process_incident(
                incident_description=incident_description,
                user_id=user_id,
                channel_id=channel_id,
                logger=logger,
                send_message=send_message,
                update_message=update_message,
            )
            
        except Exception as e:
            logger.error(f"Error handling app mention: {e}", exc_info=True)
            say(
                text="An error occurred while processing your request. Please try again.",
                thread_ts=thread_ts
            )
    
    @app.command("/incident-message")
    def handle_incident_command(
        ack: Ack,
        command: Dict[str, Any],
        respond: Respond,
        logger: logging.Logger
    ):
        """
        Handle /incident-message slash command.
        Generates incident communication messages from the command text.
        
        Args:
            ack: Function to acknowledge the command
            command: Command payload from Slack
            respond: Function to send response
            logger: Logger instance
        """
        # Acknowledge the command immediately (required within 3 seconds)
        ack()
        
        user_id = command.get("user_id")
        channel_id = command.get("channel_id")
        
        try:
            # Extract incident description from command text
            text = command.get("text", "")
            incident_description = processor.extract_incident_description(text, remove_mention=False)
            
            # Create a closure to send messages via respond
            def send_message(message: str):
                respond(text=message, response_type="ephemeral")
            
            # Process the incident
            processor.process_incident(
                incident_description=incident_description,
                user_id=user_id,
                channel_id=channel_id,
                logger=logger,
                send_message=send_message,
            )
            
        except Exception as e:
            logger.error(f"Error handling slash command: {e}", exc_info=True)
            respond(
                text="An error occurred while processing your request. Please try again.",
                response_type="ephemeral"
            )
    
    return app


def format_response(customer_msg: str, internal_msg: str) -> str:
    """
    Format the AI-generated messages for Slack with proper markdown.
    
    Args:
        customer_msg: Customer-facing message
        internal_msg: Internal team message
        
    Returns:
        Formatted string with Slack markdown
    """
    return f"""*Incident Communication Messages Generated*

*Customer-Facing Message:*
{customer_msg}

---

*Internal Team Message:*
{internal_msg}

---
_Messages saved to database for future reference._
"""

