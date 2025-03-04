"""
Lead Scoring Agent

This FastAPI-based microservice automates lead scoring by analyzing lead data and lead research report.
It evaluates lead quality, assigns a score, determines the next steps, and identifies relevant talking points.

Key Features:
- Parses incoming lead data from form submissions, CRM records, and AI-generated research reports.
- Uses Claude 3.5 Haiku via LangChain to score leads and determine engagement strategy.
- Implements a structured scoring system based on industry relevance, company size, and readiness to buy.
- Publishes structured lead evaluation data to a Kafka topic for downstream processing.
- Exposes an API endpoint (`/lead-scoring-agent`) to handle lead evaluation requests.

API Endpoint:
- `POST /lead-scoring-agent`: Accepts lead data, processes it asynchronously, and publishes the scored lead.
"""
from fastapi import APIRouter, Response, Request
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import logging
import json
import re
import asyncio
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7)

# Define tools to be used by the agent
tools = []

SYSTEM_PROMPT = """
    You're the Lead Scoring and Strategic Planner at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.
    
    You combine insights from lead analysis and research to score leads accurately and align them with the
    optimal offering. Your strategic vision and scoring expertise ensure that
    potential leads are matched with solutions that meet their specific needs.

    You role is to utilize analyzed data and research findings to score leads, suggest next steps, and identify talking points.
    """

graph = create_react_agent(model, tools=tools, state_modifier=SYSTEM_PROMPT)

async def start_agent_flow(lead_details, context):
    example_output = {
             "score": "80",
             "next_step": "Nurture | Actively Engage",
             "talking_points": "Here are the talking points to engage the lead"
         }
    
    inputs = {"messages": [("user", f"""
      Utilize the provided context and the lead's form response to score the lead.

      - Consider factors such as industry relevance, company size, StratusAI Warehouse use case potential, and buying readiness.
      - Evaluate the wording and length of the response—short answers are a yellow flag.
      - Take into account he role of the lead. Only prioritize leads that fit our core buyer persona. Nurture low quality.
      - Be pessimistic: focus high scores on leads with clear potential to close.
      - Smaller companies typically have lower budgets.
      - Avoid spending too much time on leads that are not a good fit.
      
      Lead Data
      - Lead Form Responses: {lead_details}
      - Additional Context: {context}
      
      Output Format
      - The output must be strictly formatted as JSON, with no additional text, commentary, or explanation.
      - The JSON should exactly match the following structure:
         {json.dumps(example_output)}

      Formatting Rules
        1. score: An integer between 0 and 100.
        2. next_step: Either "Nurture" or "Actively Engage" (no variations).
        3. talking_points: A list of at least three specific talking points, personalized for the lead.
        4. No extra text, no explanations, no additional formatting—output must be pure JSON.
        
        Failure to strictly follow this format will result in incorrect output.
      """)]}
    
    response = await graph.ainvoke(inputs)

    last_message_content = response["messages"][-1]
    content = last_message_content.pretty_repr()

    json_match = re.search(r"\{.*\}", content, re.DOTALL)

    if json_match:
        json_str = json_match.group()  # Extract JSON part
        lead_evaluation = json.loads(json_str)  # Convert to Python dictionary

        print(lead_evaluation)
        
        produce(AGENT_OUTPUT_TOPIC, { "context": json.dumps(lead_evaluation), "lead_data": lead_details })
    else:
        logger.info("No JSON found in the string.")

@router.api_route("/lead-scoring-agent", methods=["GET", "POST"])
async def lead_scoring_agent(request: Request):
    print("lead-scoring-agent")
    if request.method == "POST":
        data = await request.json()

        print(data)

        for item in data:
            print(item)

            lead_details = item.get('lead_data', {})
            context = item.get('context', "")

            print(lead_details)
            print(context)

            asyncio.create_task(start_agent_flow(lead_details, context))

        return Response(content="Lead Scoring Agent Started", media_type="text/plain", status_code=200)
    else: # For local testing
        item = {
            "content": "================================== Ai Message ==================================\n\nResearch Report for Target Lead\n\n1. Industry Overview:\n- Retail Industry Trends:\n  - Increasing digital transformation and e-commerce integration\n  - Growing emphasis on data-driven decision making\n  - Rising importance of personalized customer experiences\n  - AI and machine learning adoption for inventory management, customer insights, and operational efficiency\n\n2. Company Insights:\n- Company: Target Corporation\n- Industry: Retail (Multi-channel Retail and Department Store)\n- Key Characteristics:\n  - Fortune 500 company\n  - Major national retailer in the United States\n  - Operates over 1,900 stores and a robust e-commerce platform\n  - Known for innovative retail strategies and digital transformation\n\n3. Potential Use Cases for StratusAI Warehouse:\na) Real-time Analytics:\n- Inventory management optimization\n- Customer behavior analysis\n- Dynamic pricing strategies\n- Supply chain intelligence\n\nb) Data Management Challenges:\n- Managing massive volumes of transactional and customer data\n- Need for cross-platform data integration (in-store and online channels)\n- Requirement for fast, scalable data processing\n\nc) AI-Driven Opportunities:\n- Predictive demand forecasting\n- Personalized marketing recommendations\n- Fraud detection and prevention\n- Customer segmentation and targeting\n\n4. Lead Quality Assessment:\n- Positive Signals:\n  - Lead from a large enterprise company\n  - Came through a demo request\n  - Account Executive role suggests potential decision-making influence\n\n- Potential Concerns:\n  - Limited project description (\"Test\")\n  - Personal email used instead of corporate email\n  - Minimal initial context provided\n\n5. Additional Insights:\n- Target is known for technological innovation in retail\n- Likely has complex data infrastructure requiring advanced data management solutions\n- Potential interest in:\n  - Multi-cloud deployment\n  - Real-time analytics capabilities\n  - AI-driven optimization\n  - Compliance and governance features\n\nRecommended Next Steps:\n1. Conduct a more in-depth discovery call to understand:\n   - Current data infrastructure challenges\n   - Specific analytics and AI initiatives\n   - Pain points in existing data management processes\n\n2. Prepare a tailored presentation highlighting:\n   - StratusAI Warehouse's multi-cloud capabilities\n   - Real-time analytics for retail use cases\n   - AI-driven query optimization\n   - Compliance and security features\n\n3. Provide targeted use case demonstrations specific to retail data management\n\nConfidence Level: Medium\n- Requires further qualification\n- Strong potential fit based on company profile\n- Need more detailed information about specific data needs\n\nLimitations of Current Research:\n- Enrichment and Salesforce tools did not provide additional context\n- Recommend manual follow-up to gather more detailed information\n\nThis research provides a strategic framework for approaching Target as a potential StratusAI Warehouse client, highlighting the alignment between our product capabilities and their likely data management challenges.",
            "lead_data": {
                "name": "Sean Falconer",
                "email": "falconer.sean@gmail.com",
                "company_name": "Target",
                "company_website": "https://www.target.com",
                "lead_source": "Demo Request",
                "job_title": "Account Exec",
                "project_description": "Test"
            }
        }

        lead_details = item.get('lead_data', {})
        content = item.get('content', "")

        print(lead_details)

        # asyncio.create_task(start_agent_flow(lead_details, content))

        return Response(content="Lead Scoring Agent Started", media_type="text/plain", status_code=200)

