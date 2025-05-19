"""
Send email Agent

This FastAPI-based microservice takes in the email campaigns and prints the JSON to the terminal. This should be extended to actually send the email as desired.

API Endpoint:
- `POST /send-email-agent`: Accepts email data and prints it to the terminal.
"""
from fastapi import APIRouter, Response, Request
from dotenv import load_dotenv
import json
import logging
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.api_route("/send-email-agent", methods=["GET", "POST"])
async def send_email_agent(request: Request):
    logger.info("send-email-agent")
    if request.method == "POST":
        data = await request.json()

        for item in data:
            context = item.get("context", {})
            context = json.loads(context)
            pprint(context)

        return Response(content="Send Email Started", media_type="text/plain", status_code=200)
    else: # For local testing
        return Response(content="Send Email Agent Started", media_type="text/plain", status_code=200)