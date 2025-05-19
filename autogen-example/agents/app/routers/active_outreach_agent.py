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
from dotenv import load_dotenv
import logging
import json
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from ..utils.agent_tools import get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC, PRODUCT_DESCRIPTION

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1",
    model="gpt-4.1",
    api_version="2024-06-01",
    azure_endpoint="https://bhein-m9rcaw1p-eastus2.openai.azure.com/",
)

SYSTEM_PROMPT = """
    You're the AI Email Engagement Specialist at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.

    You craft engaging, high-converting emails that capture attention, drive conversations, and move leads forward.
    Your messaging is personalized, data-driven, and aligned with industry pain points to ensure relevance and impact.

    Your role is to write compelling outreach emails, optimize engagement through A/B testing and behavioral insights,
    and ensure messaging resonates with each prospect's needs and challenges.
    """
    
agent = AssistantAgent(
    name="Lead_Ingestion_Agent",
    model_client=model_client,
    tools=[get_company_website_information, get_salesforce_data, get_enriched_lead_data, get_recent_linkedin_posts],
    system_message=SYSTEM_PROMPT
)

termination_condition = TextMessageTermination("Lead_Ingestion_Agent")

# Create a team with the looped assistant agent and the termination condition.
team = RoundRobinGroupChat(
    [agent],
    termination_condition=termination_condition,
)

async def start_agent_flow(lead_details, lead_evaluation):
    example_output = {
        "to": "Lead's Email Address",
        "subject": "Example Subject Line",
        "body": "Example Email Body"
    }

    prompt = f"""
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
      """
      
    result = await team.run(task=prompt)
    
    content = result.messages[-1].content

    logger.info(f"Response from agent: {content}")
    
    email_details = json.loads(content)
    campaign_type = lead_evaluation.get("next_step", None)

    logger.info(f"Response from agent: {email_details}")
    logger.info(f"Response from agent: {campaign_type}")
    
    produce(AGENT_OUTPUT_TOPIC, { "context": json.dumps({ "emails": [ email_details ], "campaign_type": campaign_type }), "lead_data": lead_details})

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