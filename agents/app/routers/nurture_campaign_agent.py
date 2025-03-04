"""
Active Outreach Agent

This agent is responsible for generating highly  personalized and engaging email outreach
to prospects. The agent leverages information about the lead 
and multiple data sources to craft tailored messages that increase engagement and conversion rates.

Key Functionalities:
- Uses LLM-based content generation to craft compelling and relevant outreach emails.
- Scrapes company website content to extract key business information.
- Retrieves CRM data from Salesforce to understand past interactions. This is currently mocked via an LLM call.
- Enriches lead data using external services like Clearbit. This is currently mocked via an LLM call.
- Gets recent LinkedIn data from the prospect. This is currently mocked via an LLM call.
- Handles email generation while ensuring compliance with structured JSON output.
- Uses an event-driven architecture for seamless integration with email outreach process.

API Endpoint:
- `/activate-outreach-agent`: Accepts lead information and lead evaluation data and triggers the
  agent to generate a personalized outreach email.
"""

from fastapi import APIRouter, Response, Request
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import logging
import json
import re
import asyncio
from ..utils.agent_tools import get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts, find_relevant_content
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC, PRODUCT_DESCRIPTION

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7)

# Define tools to be used by the agent
tools = [get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts, find_relevant_content]

SYSTEM_PROMPT = """
    You're the AI Nurture Campaign Specialist at StratusDB, a cloud-native, AI-powered data
    warehouse built for B2B enterprises that need fast, scalable, and intelligent data
    infrastructure. StratusDB simplifies complex data pipelines, enabling companies to store,
    query, and operationalize their data in real time.

    You design multi-step nurture campaigns that educate prospects and drive engagement over time. 
    Your emails are personalized, strategically sequenced, and content-driven, ensuring relevance at every stage.
    """

graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

async def start_agent_flow(lead_details, lead_evaluation):
    example_output = {
      "emails": [
        {
          "to": "[Lead's Email Address]",
          "subject": "[Subject Line for Email 1]",
          "body": "[Email Body for Email 1]"
        },
        {
          "to": "[Lead's Email Address]",
          "subject": "[Subject Line for Email 2]",
          "body": "[Email Body for Email 2]"
        },
        {
          "to": "[Lead's Email Address]",
          "subject": "[Subject Line for Email 3]",
          "body": "[Email Body for Email 3]"
        }
      ]
    }

    inputs = {"messages": [("user", f"""
      Using the lead input and evaluation data, craft a 3-email nurture campaign designed to warm up the
      prospect and gradually build engagement over time. Each email should be sequenced strategically,
      introducing relevant insights, addressing pain points, and progressively guiding the lead toward a conversation.
      Link to additional marketing assets when it makes sense.

      Key Responsibilities:
      - Personalize each email based on lead insights from Company Website, LinkedIn, Salesforce, and Clearbit.
      - Structure a 3-email sequence, ensuring each email builds upon the previous one and provides increasing value.
      - Align messaging with the prospect's industry, role, and pain points, demonstrating how StratusAI Warehouse can address their challenges.
      - Link to relevant content assets (case studies, blog posts, whitepapers, webinars, etc.) by leveraging a Content Search Tool to find the most valuable follow-up materials.
      
      Tools & Data Sources:
      - Company Website Lookup Tool - Extracts company details, news, and strategic initiatives.
      - Salesforce Data Access - Retrieves CRM insights on past interactions, engagement status, and previous outreach.
      - Clearbit Enrichment API - Provides firmographic and contact-level data, including company size, funding, tech stack, and key decision-makers.
      - LinkedIn Profile API - Gathers professional history, recent activity, and mutual connections for better personalization.
      - Content Search Tool - Identifies the most relevant blog posts, case studies, and whitepapers for follow-ups.
      
      Lead Data:
      - Lead Form Responses: {lead_details}
      - Lead Evaluation: {lead_evaluation}

      {PRODUCT_DESCRIPTION}

      Expected Output - 5-Email Nurture Campaign:
      Each email should be concise, engaging, and sequenced effectively, containing:
      1. Personalized Opening - Address the lead by name and reference a relevant insight from their company, role, or industry trends.
      2. Key Challenge & Value Proposition - Identify a pain point or opportunity based on lead data and explain how StratusAI Warehouse solves it.
      3. Relevant Content Asset - Include a blog post, case study, or whitepaper that aligns with the lead's interests.
      4. Clear Call to Action (CTA) - Encourage engagement with a low-friction action (e.g., reading content, replying, scheduling a chat).
      5. Progressive Value Addition - Ensure each email builds upon the last, gradually increasing lead engagement and urgency.
      
      Output Format
      - The output must be strictly formatted as JSON, with no additional text, commentary, or explanation.
      - Make sure the JSON format is valid. If not, regenerate with valid JSON.
      - The JSON must strictly follow this structure:
      {json.dumps(example_output)}

      Failure to strictly follow this format will result in incorrect output.
      """)]} 
    response = await graph.ainvoke(inputs)

    last_message_content = response["messages"][-1]
    content = last_message_content.pretty_repr()

    json_match = re.search(r"\{.*\}", content, re.DOTALL)

    if json_match:
        json_str = json_match.group()
        logger.info(json_str)

        json_object = json.loads(json_str)

        nurture_sequence = json_object["emails"]

        logger.info(nurture_sequence)
        logger.info(lead_evaluation)

        logger.info('lead_evaluation')
        logger.info(type(lead_evaluation))

        campaign_type = lead_evaluation.get("next_step", None)

        produce(AGENT_OUTPUT_TOPIC, { "context": json.dumps({ "emails": nurture_sequence, "campaign_type": campaign_type }), "lead_data": lead_details})
    else:
        logger.info("No JSON found in the string.")

@router.api_route("/nurture-campaign-agent", methods=["GET", "POST"])
async def nurture_campaign_agent(request: Request):
    logger.info("nurture-campaign-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)

            lead_details = item.get('lead_data', "")
            context = item.get('context', "")

            lead_evaluation = json.loads(context) 

            logger.info(f"Here are the lead details: {lead_details}")
            logger.info(f"Here is the lead evaluation: {lead_evaluation}")

            asyncio.create_task(start_agent_flow(lead_details, lead_evaluation))

        return Response(content="Nurture Campaign Agent Started", media_type="text/plain", status_code=200)
    else: # For local testing
        item = {
          "lead_data": {
            "company_name": "Rich Table",
            "company_website": "https://www.richtablesf.com/",
            "email": "sean.smith@gmail.com",
            "job_title": "Chef",
            "lead_source": "Webinar Attendance - Real-Time Analytics & AI: The Future of Data Infrastructure",
            "name": "Sean Smith",
            "project_description": "Not sure"
          },
          "lead_evaluation": {
            "next_step": "Nurture",
            "score": "45",
            "talking_points": [
              "Explore how real-time data analytics can optimize restaurant reservation and inventory management",
              "Demonstrate ROI potential for tracking customer preferences and dining patterns across Rich Table and RT Rotisserie",
              "Share case studies of how similar fine dining establishments have leveraged data infrastructure to improve operational efficiency",
              "Highlight low-cost, scalable data solutions tailored for restaurant industry challenges"
            ]
          }
        }

        lead_details = item.get('lead_data', "")
        lead_evaluation = item.get('lead_evaluation', "")

        asyncio.create_task(start_agent_flow(lead_details, lead_evaluation))

        return Response(content="Nurture Campaign Agent Started", media_type="text/plain", status_code=200)