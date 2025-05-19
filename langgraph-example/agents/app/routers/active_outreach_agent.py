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
from ..utils.agent_tools import get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC, PRODUCT_DESCRIPTION

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7)

# Define tools to be used by the agent
tools = [get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts]

SYSTEM_PROMPT = """
    You're the AI Email Engagement Specialist at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.

    You craft engaging, high-converting emails that capture attention, drive conversations, and move leads forward.
    Your messaging is personalized, data-driven, and aligned with industry pain points to ensure relevance and impact.

    Your role is to write compelling outreach emails, optimize engagement through A/B testing and behavioral insights,
    and ensure messaging resonates with each prospect's needs and challenges.
    """

graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

async def start_agent_flow(lead_details, lead_evaluation):
    example_output = {
        "to": "Lead's Email Address",
        "subject": "Example Subject Line",
        "body": "Example Email Body"
    }

    inputs = {"messages": [("user", f"""
      Using the lead input and evaluation data to craft a highly personalized and engaging email to initiate a conversation with the prospect.
      The email should be tailored to their industry, role, and business needs, ensuring relevance and increasing the likelihood of a response.

      Key Responsibilities:
      - Personalize outreach based on lead insights from company website, LinkedIn, Salesforce, and Clearbit.
      - Craft a compelling email structure, ensuring clarity, relevance, and engagement.
      - Align messaging with the prospect's pain points and industry trends, showing how StratusAI Warehouse addresses their challenges.
      
      Use dedicated tools to enhance personalization and optimize engagement:
      - Company Website Lookup Tool - Extracts relevant company details, recent news, and strategic initiatives.
      - Salesforce Data Access - Retrieves CRM data about the lead 's past interactions, engagement status, and any prior outreach.
      - Clearbit Enrichment API - Provides firmographic and contact-level data, including company size, funding, tech stack, and key decision-makers.
      - LinkedIn Profile API - Gathers professional history, recent activity, and mutual connections to inform messaging.
      
      Ensure a clear and actionable CTA, encouraging the lead to engage without high friction.
     
      Lead Data
      - Lead Form Responses: {lead_details}
      - Lead Evaluation: {lead_evaluation}

      {PRODUCT_DESCRIPTION}
      
      Expected Output - Personalized Prospect Email:
      The email should be concise, engaging, and structured to drive a response, containing:

      - Personalized Opening - Address the lead by name and reference a relevant insight from their company, role, or industry trends.
      - Key Challenge & Value Proposition - Identify a pain point or opportunity based on lead data and explain how StratusAI Warehouse solves it.
      - Clear Call to Action (CTA) - Encourage a response with a low-friction action, such as scheduling a quick chat or sharing feedback.
      - Engagement-Oriented Tone - Maintain a conversational yet professional approach, keeping the message brief and impactful.

      Output Format
      - The output must be strictly formatted as JSON, with no additional text, commentary, or explanation.
      - The JSON should exactly match the following structure:
         {json.dumps(example_output)}

      Failure to strictly follow this format will result in incorrect output.
      """)]}
    
    response = await graph.ainvoke(inputs)

    last_message_content = response["messages"][-1]
    content = last_message_content.pretty_repr()

    logger.info(content)

    json_match = re.search(r"\{.*\}", content, re.DOTALL)

    if json_match:
        json_str = json_match.group()
        logger.info(json_str)

        email_details = json.loads(json_str)
        campaign_type = lead_evaluation.get("next_step", None)

        produce(AGENT_OUTPUT_TOPIC, { "context": json.dumps({ "emails": [ email_details ], "campaign_type": campaign_type }), "lead_data": lead_details})
    else:
        logger.info("No JSON found in the string.")

@router.api_route("/active-outreach-agent", methods=["GET", "POST"])
async def active_outreach_agent(request: Request):
    logger.info("active-outreach-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)

            lead_details = item.get('lead_data', "")
            context = item.get('context', "")

            logger.info(f"Here are the lead details: {lead_details}")
            logger.info(f"Here is the context: {context}")

            lead_evaluation = json.loads(context)

            logger.info(lead_evaluation)

            asyncio.create_task(start_agent_flow(lead_details, lead_evaluation))

        return Response(content="Actively Engage Agent Started", media_type="text/plain", status_code=200)
    else: # For local testing
        item = {'lead_data': {'project_description': '111 Looking for a scalable data warehouse solution to support real-time analytics and AI-driven insights. Currently using Snowflake but exploring alternatives that better integrate with streaming data.', 'company_name': 'Tiger Analytics', 'company_website': 'https://www.tigeranalytics.com/', 'lead_source': 'Webinar - AI for Real-Time Data', 'name': 'Jane Doe', 'job_title': 'Director of Data Engineering', 'email': 'jane.doe@acmeanalytics.com'}, 'lead_evaluation': {'score': '90', 'next_step': 'Actively Engage', 'talking_points': ['Demonstrate seamless migration path from Snowflake with zero data loss and improved real-time analytics performance', "Highlight StratusDB's native AI/ML integration capabilities that align with Tiger Analytics' multi-industry consulting approach", 'Showcase multi-cloud deployment flexibility and how it complements their existing AWS and cloud technology ecosystem', 'Present technical deep dive on query optimization and cost management specifically tailored to their 350-employee data engineering workflow']}}

        lead_details = item.get('lead_data', "")
        lead_evaluation = item.get('lead_evaluation', "")
        
        asyncio.create_task(start_agent_flow(lead_details, lead_evaluation))

        return Response(content="Actively Engage Agent Started", media_type="text/plain", status_code=200)