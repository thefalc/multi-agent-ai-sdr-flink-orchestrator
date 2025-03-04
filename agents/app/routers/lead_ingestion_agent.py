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
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import asyncio
import logging
from ..utils.agent_tools import get_company_website_information, get_salesforce_data, get_enriched_lead_data
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC, PRODUCT_DESCRIPTION

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7)

# Define tools to be used by the agent
tools = [get_company_website_information, get_salesforce_data, get_enriched_lead_data]

SYSTEM_PROMPT = """
    You're an Industry Research Specialist at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.

    Your role is to conduct research on potential leads to assess their fit for StratusAI Warehouse and provide key
    insights for scoring and outreach planning. Your research will focus on industry trends, company background,
    and AI adoption potential to ensure a tailored and strategic approach.
    """

graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

async def start_agent_flow(lead_details):
    inputs = {"messages": [("user", f"""
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
      Additional Insights - Any relevant information that can aid in outreach planning or lead prioritization.""")]}
    
    response = await graph.ainvoke(inputs)

    last_message_content = response["messages"][-1]
    content = last_message_content.pretty_repr()

    logger.info(f"Response from agent: {content}")

    produce(AGENT_OUTPUT_TOPIC, { "context": content, "lead_data": lead_details })

@router.api_route("/lead-ingestion-agent", methods=["GET", "POST"])
async def lead_ingestion_agent(request: Request):
    print("lead-ingestion-agent")
    if request.method == "POST":
        data = await request.json()

        print(data)

        for item in data:
            print(item)
            lead_details = item.get("lead_data", {})
            agent_name = item.get("agent_name", {})
                        
            print(lead_details)
        
            asyncio.create_task(start_agent_flow(lead_details))

        return Response(content="Lead Ingestion Agent Started", media_type="text/plain", status_code=200)
    else: # For local testing
        full_document = {'createdAt': 1740674891490, 'leadSource': 'Demo Request', 'jobTitle': 'Account Exec', 'name': 'Sean Falconer', 'projectDescription': 'Test', 'company': 'Target', '_id': '{"$oid": "67c0974cef1e1dad39a75168"}', 'companyWebsite': 'https://www.target.com', 'email': 'falconer.sean@gmail.com'}

        lead_details = {
          "name": full_document.get("name"),
          "email": full_document.get("email"),
          "company_name": full_document.get("company"),
          "company_website": full_document.get("companyWebsite"),
          "lead_source": full_document.get("leadSource"),
          "job_title": full_document.get("jobTitle"),
          "project_description": full_document.get("projectDescription"),
        }

        asyncio.create_task(start_agent_flow(lead_details))

        return Response(content="Lead Ingestion Agent Started", media_type="text/plain", status_code=200)