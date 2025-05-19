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
from dotenv import load_dotenv
import logging
import json
import re
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from ..utils.publish_to_topic import produce
from ..utils.constants import AGENT_OUTPUT_TOPIC

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
    You're the Lead Scoring and Strategic Planner at StratusDB, a cloud-native, AI-powered data warehouse built for B2B
    enterprises that need fast, scalable, and intelligent data infrastructure. StratusDB simplifies complex data
    pipelines, enabling companies to store, query, and operationalize their data in real time.
    
    You combine insights from lead analysis and research to score leads accurately and align them with the
    optimal offering. Your strategic vision and scoring expertise ensure that
    potential leads are matched with solutions that meet their specific needs.

    You role is to utilize analyzed data and research findings to score leads, suggest next steps, and identify talking points.
    """

agent = AssistantAgent(
    name="Lead_Scoring_Agent",
    model_client=model_client,
    system_message=SYSTEM_PROMPT
)

async def start_agent_flow(lead_details, context):
    example_output = {
             "score": "80",
             "next_step": "Nurture | Actively Engage",
             "talking_points": "Here are the talking points to engage the lead"
         }
    
    prompt = f"""
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
      """
    
    result = await agent.run(task=prompt)
    
    last_message_content = result.messages[-1].content
    
    json_match = re.search(r"\{.*\}", last_message_content, re.DOTALL)
    
    if json_match:
        json_str = json_match.group() 
        lead_evaluation = json.loads(json_str)

        logger.info(lead_evaluation)
        
        produce(AGENT_OUTPUT_TOPIC, { "context": json.dumps(lead_evaluation), "lead_data": lead_details })
    else:
        logger.info("No JSON found in the string.")

@router.api_route("/lead-scoring-agent", methods=["GET", "POST"])
async def lead_scoring_agent(request: Request):
    print("lead-scoring-agent")
    if request.method == "POST":
        data = await request.json()

        logger.info(data)

        for item in data:
            logger.info(item)

            lead_details = item.get('lead_data', {})
            context = item.get('context', "")

            logger.info(lead_details)
            logger.info(context)

            asyncio.create_task(start_agent_flow(lead_details, context))

        return Response(content="Lead Scoring Agent Started", media_type="text/plain", status_code=200)

