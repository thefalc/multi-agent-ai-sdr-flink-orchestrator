"""
Lead Ingestion Agent - Preliminary Lead Analysis

This agent automates the preliminary analysis of incoming leads by gathering 
and enriching data from various sources. It extracts relevant insights 
and prepare leads for further engagement.

Key Functionalities:
- Fetches and processes lead details submitted via web forms or other sources.
- Scrapes company website content to extract key business information.
- Retrieves CRM data from Salesforce to understand past interactions. This is currently mocked via an LLM call.
- Enriches lead data using external services like Clearbit. This is currently mocked via an LLM call.
- Conducts AI-driven research to assess lead quality, industry trends, and potential fit.
- Publishes the analyzed data to a messaging topic for downstream processing.

Tech Stack:
- FastAPI for API handling and request processing.
- LangChain + Claude 3.5 Haiku for AI-driven research and enrichment.
- BeautifulSoup for web scraping.
- Kafka (via `produce`) for publishing enriched leads.
- Async execution for efficient concurrent processing.

API Endpoint:
- `POST /lead-ingestion-agent`: Processes new lead data and triggers research workflows.

"""
from fastapi import APIRouter, Response, Request
from dotenv import load_dotenv
import asyncio
import logging
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from ..utils.agent_tools import get_company_website_information, get_salesforce_data, get_enriched_lead_data
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
    You're an Industry Research Specialist at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.

    Your role is to conduct research on potential leads to assess their fit for StratusAI Warehouse and provide key
    insights for scoring and outreach planning. Your research will focus on industry trends, company background,
    and AI adoption potential to ensure a tailored and strategic approach.
    """

agent = AssistantAgent(
    name="Lead_Ingestion_Agent",
    model_client=model_client,
    tools=[get_salesforce_data, get_enriched_lead_data, get_company_website_information],
    system_message=SYSTEM_PROMPT
)

termination_condition = TextMessageTermination("Lead_Ingestion_Agent")

# Create a team with the looped assistant agent and the termination condition.
team = RoundRobinGroupChat(
    [agent],
    termination_condition=termination_condition,
)

async def start_agent_flow(lead_details):
    prompt = f"""
      Using the lead input data, conduct preliminary research on the lead. Focus on finding relevant data
      that can aid in scoring the lead and planning a strategy to pitch them. You do not need to score the lead.

      Key Responsibilities:
        - Analyze the lead's industry to identify relevant trends, market challenges, and AI adoption patterns.
        - Gather company-specific insights, including size, market position, recent news, and strategic initiatives.
        - Determine potential use cases for StratusAI Warehouse, focusing on how the company could benefit from real-time analytics, multi-cloud data management, and AI-driven optimization.
        - Assess lead quality based on data completeness and engagement signals. Leads with short or vague form responses should be flagged for review but not immediately discarded.
        - Use dedicated tools to enhance research and minimize manual work:
          - Company Website Lookup Tool - Fetches key details from the company's official website.
          - Salesforce Data Access - Retrieves CRM data about the lead's past interactions, status, and engagement history.
          - Clearbit Enrichment API - Provides firmographic and contact-level data, including company size, funding, tech stack, and key decision-makers.
        - Filter out weak leads or where the lead data doesn't look like a fit, ensuring minimal time is spent on companies unlikely to be a fit for StratusDB's offering.

      Lead Form Responses:
        {lead_details}

      {PRODUCT_DESCRIPTION}
        
      Expected Output - Research Report:
      The research report should be concise and actionable, containing:

      Industry Overview - Key trends, challenges, and AI adoption patterns in the lead's industry.
      Company Insights - Size, market position, strategic direction, and recent news.
      Potential Use Cases - How StratusAI Warehouse could provide value to the lead's company.
      Lead Quality Assessment - Based on available data, engagement signals, and fit for StratusDB's ideal customer profile.
      Additional Insights - Any relevant information that can aid in outreach planning or lead prioritization."""
    
    result = await team.run(task=prompt)
    
    content = result.messages[-1].content

    logger.info(f"Response from agent: {content}")

    produce(AGENT_OUTPUT_TOPIC, { "context": content, "lead_data": lead_details })

@router.api_route("/lead-ingestion-agent", methods=["GET", "POST"])
async def lead_ingestion_agent(request: Request):
    print("lead-ingestion-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)
            lead_details = item.get("lead_data", {})

            logger.info(lead_details)
        
            asyncio.create_task(start_agent_flow(lead_details))

        return Response(content="Lead Ingestion Agent Started", media_type="text/plain", status_code=200)