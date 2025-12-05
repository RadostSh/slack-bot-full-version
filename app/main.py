"""
FastAPI main application entry point.
Initializes the Slack bot and provides API endpoints.
"""

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi import SlackRequestHandler
from app.config import get_settings
from app.slack_handler import create_slack_app


# Create Slack app instance
slack_app = create_slack_app()

# Create handler for FastAPI
slack_handler = SlackRequestHandler(slack_app)

# Create FastAPI app
app = FastAPI(
    title="Slack Incident Communication Bot",
    description="AI-powered bot for generating incident communication messages",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Slack Incident Communication Bot",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "slack_bot": "running"
    }


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle incoming Slack events.
    This endpoint receives events from Slack's Event API.
    """
    return await slack_handler.handle(request)


@app.post("/slack/commands")
async def slack_commands(request: Request):
    """
    Handle incoming Slack slash commands.
    This endpoint receives slash command requests from Slack.
    """
    return await slack_handler.handle(request)


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )

