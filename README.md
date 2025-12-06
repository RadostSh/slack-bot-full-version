# **Incident Communication Helper with Saved History**

An AI-powered Slack bot that helps DevOps teams generate professional incident communication messages. During production incidents, teams need to communicate effectively with both customers and internal stakeholders. The bot uses Google's Gemini AI to generate both customer-facing and internal team messages for incidents and stores all communication history in a SashiDo database for future reference.

------

## Project Features

- **AI-Powered Message Generation:** Uses **Google Gemini AI** to process raw incident descriptions and instantly generate two distinct, professional outputs: a customer-facing status message and a technical internal note for support teams.

- Dual Input Modes:

   Supports two ways to trigger the bot, catering to different team workflows:

  - **App Mention:** `@ops-bot`
  - **Slash Command:** `/incident-message`

- **Database Integration:** Automatically saves incident communication records (incident text, customer message, and internal message) to a **Parse Server database (SashiDo)** for historical tracking.

- Error Handling:

   Implements error handling across the service layer:

  - **Configuration Validation:** Validates all required environment variables on startup
  - **Input Validation:** Validates request data before processing
  - **AI Service Errors:** Catches and logs AI service failures
  - **Database Errors:** Handles database save failures (returns messages even if save fails)

------

## API Flow:

1. **Slack API** → Sends incident reports via app mentions or slash commands
2. **FastAPI** → Receives and routes Slack events, orchestrates the workflow
3. **Gemini AI API** → Processes incident descriptions and generates professional messages
4. **SashiDo API** → Stores incident history with generated messages for future reference
5. **Slack API** ← Receives formatted response and displays to user

------

## **Project Structure**

```
slack-bot-full-version/
│
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application & endpoints
│   ├── slack_handler.py         # Slack Bolt app & event handlers
│   ├── ai_service.py            # Gemini AI integration
│   ├── database.py              # SashiDo database service
│   └── config.py                # Configuration management
│
├── manifest.json                # Slack App manifest
├── requirements.txt             # Python dependencies
└── runtime.txt                  # Python runtime version
```

------

## Technical Stack

| Category             | Technology                  | Details                                                |
| -------------------- | --------------------------- | ------------------------------------------------------ |
| **Backend Language** | **Python**                  | Primary development language.                          |
| **Web Framework**    | **FastAPI/Uvicorn**         | Used for the application structure and routing.        |
| **AI Model**         | **Google Gemini 2.5 Flash** | Used via the Google Gemini API for message generation. |
| **Database**         | **SashiDo (Parse Server)**  | Used to store incident records.                        |
| **Hosting**          | **Railway**                 | Cloud platform for deployment.                         |
| **Slack framework**  | **Slack Bolt**              | Framework for building Slack apps in Python            |

------

## Future Improvements

The next major feature would be to implement **Slack Block Kit** for interactive messages.

- **Current:** The bot replies with a static message containing two text drafts.

- Future (Block Kit):

   The bot replies with an interactive message allowing the user to:

  - [Approve Button] Send the **Customer Message** directly to the Status Channel.
  - [Edit Button] Open a simple modal to **tweak the wording** before publishing.
