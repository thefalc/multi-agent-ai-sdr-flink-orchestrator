from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
import os
import requests
import logging
from ..utils.constants import PRODUCT_DESCRIPTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

model = ChatAnthropic(model='claude-3-5-haiku-20241022', temperature=0.7, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

def remove_empty_lines(text):
    return "\n".join([line for line in text.split("\n") if line.strip()])

@tool
def find_relevant_content(search_query):
    """
    Finds and returns the five most relevant marketing assets based on the given search query.
    
    This is synthetically generated via an LLM API call.

    This function:
    - Constructs a prompt using the search query to generate relevant marketing assets.
    - Uses an AI model to retrieve a structured list of content, including:
      - Titles
      - Descriptions
      - URLs
      - Asset types (e.g., case studies, blog posts, whitepapers, webinars)

    Args:
        search_query (str): The search query used to find relevant content.

    Returns:
        dict: A structured JSON response containing the top relevant marketing assets.
    """

    logger.info(f"Finds relevant content for {search_query}")

    example_output = {
      "marketing_assets": [
        {
          "title": "[Title of Asset #1]",
          "description": "[Short Description of Asset #1]",
          "url": "[URL location of Asset #1]",
          "type": "[Case Study or Blog Post or Whitepaper or Webinar of Asset #1]",
        },
        {
          "title": "[Title of Asset #2]",
          "description": "[Short Description of Asset #2]",
          "url": "[URL location of Asset #2]",
          "type": "[Case Study or Blog Post or Whitepaper or Webinar of Asset #2]",
        }
      ]
    }

    prompt = f"""
      Take the search query and generate a list of related marketing assets such as
      case studies, blog posts, whitepapers, webinars that are related to the query.

      Search query
      {search_query}

      These content should be believably created by this company:
      {PRODUCT_DESCRIPTION}

      The fake output should look like this:
      {json.dumps(example_output)}
    """

    data = model.invoke([{ "role": "user", "content": prompt }])

    return response

@tool
def get_recent_linkedin_posts(lead_details):
    """
    Fetches and extracts recent LinkedIn posts by the prospect.

    This is synthetically generated via an LLM API call.

    This function:
    - Uses AI to generate plausible LinkedIn activity for a given lead.
    - Creates a prompt based on the lead's details to infer recent LinkedIn discussions.
    - Simulates posts that align with the lead's industry, interests, and engagement history.

    Args:
        lead_details (str): Information about the lead (e.g., name, job title, company).

    Returns:
        str: AI-generated LinkedIn activity representing the lead's recent posts.
    """

    logger.info(f"Gets recent LinkedIn posts by the lead {lead_details}")

    prompt = f"""
      Using the lead details, create some fake data that represents what the
      lead has recently been talking about on LinkedIn. Keep this short. This
      is to inform the email campaign to the lead.

      Lead details:
      {lead_details}
    """

    data = model.invoke([{ "role": "user", "content": prompt }])

    return response

@tool
def get_company_website_information(company_website_url):
    """
    Fetches and extracts readable text content from a company's website.

    This function:
    - Sends an HTTP GET request to the specified company website URL.
    - Parses the HTML response while removing non-visible elements like 
      <style>, <script>, <head>, and <title> tags.
    - Extracts and cleans visible text content.
    - Removes empty lines for better readability.

    Args:
        company_website_url (str): The URL of the company's website.

    Returns:
        str: The cleaned visible text from the website if successful.
        None: If the request fails or the website is inaccessible.

    Raises:
        requests.RequestException: If an error occurs during the HTTP request.
    """
    logger.info(f"Fetching company website information for: {company_website_url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        }
        response = requests.get(company_website_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
            visible_text = soup.getText()

            response = remove_empty_lines(visible_text)

            return response
        else:
            logger.info(f"Failed to fetch the website. Status code: {response.status_code}")
        
            return None
    except requests.RequestException as e:
        logger.info(f"Error fetching website: {e}")
        return None

@tool
def get_salesforce_data(lead_details):
    """
    Generates synthetic Salesforce data for a given lead.

    This function:
    - Takes the provided lead details as input.
    - Constructs a prompt to generate realistic Salesforce data, including:
      - Contact information
      - Company details
      - Lead status and attributes
      - Historical interactions
    - Invokes an AI model to generate the synthetic Salesforce response.
    - Returns the generated data in JSON format.

    Args:
        lead_details (str): A string containing relevant lead information.

    Returns:
        dict: A JSON object representing the synthetic Salesforce data.

    Note:
        - This function does not query a real Salesforce instance; it generates 
          plausible Salesforce-like data using an AI model.
    """

    logger.info(f"Fetching Salesforce data for: {lead_details}")

    prompt = f"""
      Take the lead details and generate realistic Salesforce data to represent the contact,
      company, lead information, and any historical interactions we've had with the lead.

      Take into account the product details when generating the history. If there's not a good
      match between the lead and product, reflect that in the Salesforce data.

      It's also ok to return no information to simulate that there's no history with this lead.

      Return only the fake Salesforce data as JSON. Do not wrap the message in any additional text.

      Lead details:
      {lead_details}

      Product details:
      {PRODUCT_DESCRIPTION}
    """

    data = model.invoke([{ "role": "user", "content": prompt }])

    return response

@tool
def get_enriched_lead_data(lead_details):
    """
    Generates synthetic enriched lead data, including both person and company details.

    This function:
    - Takes raw lead details as input.
    - Constructs a prompt to generate realistic enriched data using an AI model.
    - Simulates Clearbit-like enrichment, including:
      - Personal details (name, job title, email, social profiles, etc.).
      - Employment history.
      - Company details (industry, size, funding, technologies used, etc.).
      - Key decision-makers and hiring trends.
    - Returns the generated enrichment data in JSON format.

    Args:
        lead_details (str): A string containing relevant lead information.

    Returns:
        dict: A JSON object representing the enriched lead data.

    Note:
        - This function does not query a real enrichment service like Clearbit.
        - The output is AI-generated and structured based on a predefined example.
    """

    logger.info(f"Fetching Clearbit data for: {lead_details}")

    clear_bit_sample_payload = {
        "person": {
            "full_name": "Jane Doe",
            "job_title": "Director of Data Engineering",
            "company_name": "Acme Analytics",
            "company_domain": "acmeanalytics.com",
            "work_email": "jane.doe@acmeanalytics.com",
            "linkedin_url": "https://www.linkedin.com/in/janedoe",
            "twitter_handle": "@janedoe",
            "location": {
                "city": "San Francisco",
                "state": "California",
                "country": "United States"
            },
            "work_phone": "+1 415-555-1234",
            "employment_history": [
                {
                    "company": "DataCorp",
                    "job_title": "Senior Data Engineer",
                    "years": "2018-2022"
                },
                {
                    "company": "Tech Solutions",
                    "job_title": "Data Analyst",
                    "years": "2015-2018"
                }
            ]
        },
        "company": {
            "name": "Acme Analytics",
            "domain": "acmeanalytics.com",
            "industry": "Data & Analytics",
            "sector": "Software & IT Services",
            "employee_count": 500,
            "annual_revenue": "$50M-$100M",
            "company_type": "Private",
            "headquarters": {
                "city": "San Francisco",
                "state": "California",
                "country": "United States"
            },
            "linkedin_url": "https://www.linkedin.com/company/acme-analytics",
            "twitter_handle": "@acmeanalytics",
            "facebook_url": "https://www.facebook.com/acmeanalytics",
            "technologies_used": [
                "AWS",
                "Snowflake",
                "Apache Kafka",
                "Flink",
                "Looker",
                "Salesforce"
            ],
            "funding_info": {
                "total_funding": "$75M",
                "last_round": "Series B",
                "last_round_date": "2023-08-15",
                "investors": ["Sequoia Capital", "Andreessen Horowitz"]
            },
            "key_decision_makers": [
                {
                    "name": "John Smith",
                    "title": "CEO",
                    "linkedin_url": "https://www.linkedin.com/in/johnsmith"
                },
                {
                    "name": "Emily Johnson",
                    "title": "VP of Engineering",
                    "linkedin_url": "https://www.linkedin.com/in/emilyjohnson"
                }
            ],
            "hiring_trends": {
                "open_positions": 12,
                "growth_rate": "15% YoY",
                "top_hiring_departments": ["Engineering", "Data Science", "Sales"]
            }
        }
    }

    # Convert JSON to a properly escaped string
    clearbit_sample_as_string = json.dumps(clear_bit_sample_payload, indent=4) 

    prompt = f"""
      Take the lead details and generate realistic Clearbit data to represent the enriched lead.
      Return only the fake Clearbit data as JSON. Do not wrap the message in any additional text.

      Lead details:
      {lead_details}

      The fake output should look like this:
      {clearbit_sample_as_string}
    """

    data = model.invoke([{ "role": "user", "content": prompt }])

    return response