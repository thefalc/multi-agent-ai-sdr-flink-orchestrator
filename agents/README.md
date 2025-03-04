# Meal Planner Multi-Agent and HTTP Sink APIs

This folder contains a Python app that supports given API endpoints. 

* `/api/lead-ingestion-agent`: A ReAct agent enriches lead data and assigns a lead score.
* `/api/lead-routing-agent`: A ReAct agent that determines the next step based on lead quality.
* `/api/active-outreach-agent`: A ReAct agent that that creates a personalized outreach email.
* `/api/nurture-campaign-agent`: A ReAct agent that creates a personalized sequence of emails.

Refer to the main README.md for detailed instructions in how to setup and configure this application.

## Configuring the application

You need to create a `.env` file with the following values:
* ANTHROPIC_API_KEY
* LANGCHAIN_TRACING_V2
* LANGCHAIN_API_KEY

As well as a `client.properties` file that contains properties to connect to Confluent.

## Running the application

From the your terminal, navigate to the `/agents` directory and enter the following command:

```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```