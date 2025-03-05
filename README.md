# Multi-Agent AI SDR for Lead Processing
This application uses LangChain, Anthropic's Claude, and Confluent to create an AI-based SDR.

The multi-agent system automates the SDR workflow. Apache Flink and external model inference is used to orchestrate communication with a series of AI agents, each responsible for a specific task in the lead management and outreach process.

The system is event-driven, leveraging [Confluent Cloud's](https://www.confluent.io/) as the backbone for real-time communication, orchestration, and data flow between agents. 

At a high level, the initial system consists of the following key agents:

* Lead Ingestion Agent: Captures incoming leads from web forms, enriches them with external data (e.g., company website, Salesforce), and generates a research report that can be used for scoring
* Lead Scoring Agent: Uses the enriched lead information to score the lead and generate a short summary for how to best engage the lead. Determines the appropriate next step based on lead quality, either triggering the nurture agent sequence designer or triggering an active outreach campaign.
* Active Outreach Agent: Creates personalized outreach emails using AI-driven content generation, incorporating insights from the lead’s online presence, trying to book a meeting
* Nurture Campaign Agent: Dynamically creates a sequence of emails based on where the lead originated and what their interest was.
* Send Email Agent: Currently just prints the email to send to a terminal, but in a real application would send via email relay or email service.

Each agent is designed to run as a microservice with a brain that communicates via event streams in Confluent Cloud, allowing for real-time processing and asynchronous handoffs between agents.

The diagram below illustrates how these agents interact through event-driven messaging.

<p align="center">
  <img src="/images/ai-sdr-architecture-diagram.png" />
</p>

## How it works
As a user, you can enter a lead into a web form. Once you submit the lead form, it's saved to MongoDB. A source connector
in Confluent takes data from MongoDB and adds it into a Kafka topic. New leads are copied into a topic called `agent_messages`. 
This topic will contain all messages to and from agents. When a new lead is added as a message, the Flink orchestration job
routes it to the lead ingestion agent. 

This starts the multi-agent process.

# Project overview

The project is split into two applications. The `web-application` is a NextJS application that uses a standard three tier stack consisting of a frontend written in React, a backend in Node, and a MongoDB application database.

For the purposes of this demo, I'm using MongoDB to store the leads, but in a real world scenario, these would likely go
into a marketing automation platform or CRM.

Kafka and Flink, running on Confluent Cloud, are used to move data around between services. The web application doesn't know anything about LLMs, Kafka, or Flink.

The `agents` application is a Python app that includes routes to the different agents and API endpoints called by Confluent to consume messages from Kafka topics. These API endpoints take care of all the AI magic to generate an lead engagement plan.

# What you'll need
In order to set up and run the application, you need the following:

* [Node v22.5.1](https://nodejs.org/en) or above
* [Python 3.10](https://www.python.org/downloads/) or above
* A [Confluent Cloud](https://www.confluent.io/) account
* A [Claude](https://www.anthropic.com/claude) API key
* A [LangChain](https://www.langchain.com/) API key
* A [MongoDB](https://www.mongodb.com/) account

## Getting set up

### Get the starter code
In a terminal, clone the sample code to your project's working directory with the following command:

```shell
git clone https://github.com/thefalc/multi-agent-ai-sdr-flink-orchestrator.git
```

### Setting up MongoDB

In MongoDB create a database called `stratusdb` with the following collections:

* `leads` - Stores leads generated from the web application

### Configure and run the lead capture web application

Go into your `web-application` folder and create a `.env` file with your MongoDB connection details.

```bash
MONGODB_URI='mongodb+srv://USER:PASSWORD@CLUSTER_URI/?retryWrites=true&w=majority&appName=REPLACE_ME'
```

Navigate into the `web-application` folder and run the application.

```bash
npm install
npm run dev
```

Go to `http://localhost:3000` and try creating a lead. If everything looks good, then continue with the setup.

### Setting up Confluent Cloud

The AI SDR uses Confluent Cloud to move and operate on data in real-time and handle the heavy lifting for communication between the agents.

### Create the MongoDB request source connector

In order to kick start the agentic workflow, data from MongoDB needs to be published to Kafka. This can be done by creating a MongoDB source connector.

In Confluent Cloud, create a new connector.

<p align="center">
  <img src="/images/confluent-cloud-overview.png" />
</p>

* Search for "mongodb" and select the **MongoDB Atlas Source**
* Enter a topic prefix as `incoming-leads`
* In **Kafka credentials**, select **Service account** and use an existing or create a new one
* In **Authentication,** enter your MongoDB connection details, the database name **stratusdb** and a collection name of **leads**
* Under **Configuration**, select **JSON**
* For **Sizing**, leave the defaults and click **Continue**
* Name the connector `inbound-leads-source-connector` and click **Continue**

### Create the topics for agent communication and routing

In your Confluent Cloud account.

* Go to your Kafka cluster and click on **Topics** in the sidebar.
* Name the topic as `agent_messages`.
* Set other configurations as needed, such as the number of partitions and replication factor, based on your requirements.
* Go to **Schema Registry**
* Click **Add Schema** and select **agent_messages** as the subject
* Choose JSON Schema as the schema type
* Paste the schema from below into the editor

```json
{
  "properties": {
    "context": {
      "connect.index": 1,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    },
    "lead_data": {
      "connect.index": 0,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "properties": {
            "company_name": {
              "type": "string"
            },
            "company_website": {
              "format": "uri",
              "type": "string"
            },
            "email": {
              "format": "email",
              "type": "string"
            },
            "job_title": {
              "type": "string"
            },
            "lead_source": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "project_description": {
              "type": "string"
            }
          },
          "required": [
            "name",
            "email",
            "company_name",
            "lead_source",
            "job_title"
          ],
          "type": "object"
        }
      ]
    }
  },
  "title": "Record",
  "type": "object"
}
```

* Save the schema

Next, we are going to create a topic that will contain the agent messages along with the agent name. This will be used for routing the message to the indicated agent.

* Go to your Kafka cluster and click on **Topics** in the sidebar.
* Name the topic as `agent_predictions`.
* Set other configurations as needed, such as the number of partitions and replication factor, based on your requirements.
* Go to **Schema Registry**
* Click **Add Schema** and select **agent_predictions** as the subject
* Choose JSON Schema as the schema type
* Paste the schema from below into the editor

```json
{
  "properties": {
    "agent_name": {
      "connect.index": 2,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    },
    "context": {
      "connect.index": 1,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "type": "string"
        }
      ]
    },
    "lead_data": {
      "connect.index": 0,
      "oneOf": [
        {
          "type": "null"
        },
        {
          "properties": {
            "company_name": {
              "type": "string"
            },
            "company_website": {
              "format": "uri",
              "type": "string"
            },
            "email": {
              "format": "email",
              "type": "string"
            },
            "job_title": {
              "type": "string"
            },
            "lead_source": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "project_description": {
              "type": "string"
            }
          },
          "required": [
            "name",
            "email",
            "company_name",
            "lead_source",
            "job_title"
          ],
          "type": "object"
        }
      ]
    }
  },
  "title": "Record",
  "type": "object"
}
```

* Save the schema

### Create the HTTP sink connectors for all agents

Next, we have to setup the routing from the `agent_predictions` topic to the agent endpoints. We will do this by creating a new HTTP sink connector for each agent and filter messages using a Single Message Transform to only send messages matching the agent's name to the agent endpoint.

* Under **Connectors**, click **+ Add Connector**
* Search for "http" and select the **HTTP Sink** connector
* Select the **agent_predictions** topic
* In **Kafka credentials**, select **Service account** and use you existing service account and click **Continue**
* Enter the URL for where the `lead-ingestion-agent` endpoint is running under the `agents` folder. This will be
similar to `https://YOUR-PUBLIC-DOMAIN/api/lead-ingestion-agent`. If running locally, you can use [ngrok](https://ngrok.com/)
to create a publicly accessible URL. Click **Continue**
* Under **Configuration**, select **JSON_SR** and click **Continue**
* For **Sizing**, leave the defaults and click **Continue**
* Name the connector `lead-ingestion-agent-sink` and click **Continue**

Once the connector is created, under the **Settings** > **Advanced configuration** make sure the **Request Body Format** is set to **json**.

Additionally, in **Settings**, under **Transforms**, click **Edit**.

* Select **Filter$Value** for **Transform type**
* In **Filter Condition**, enter `$[?(@.agent_name == 'Lead Ingestion Agent')]`
* Select **include** in **Filter Type**
* Click **Save Changes**

Repeat these steps for agents for the Lead Scoring Agent, Active Outreach Agent, Nurture Campaign Agent, and Send Email Agent.

### Flink SQL and LLM setup

Flink SQL is used to copy leads into `agent_messages` and map all `agent_messages` into `agent_predictions` using a LLM to determine where to map messages.

#### Connecting Flink to OpenAI

To extract dynamically map new messages to the agents available, we are going to use external model inference in Flink to call a model to dynamically determine the mapping. The first step is to create a connection between Flink and OpenAI (or whatever model you're using).

In your terminal, execute the following.

```bash
confluent flink connection create openai-connection \
--cloud aws \
--region us-east-1 \
--type openai \
--endpoint https://api.openai.com/v1/chat/completions \
--api-key REPLACE_WITH_YOUR_KEY
```

Make sure the region value matches the region for where you're running Confluent Cloud.

#### Flink SQL setup for copying leads

Flink SQL is used to copy leads into `agent_messages` and map all `agent_messages` into `agent_predictions` using a LLM to determine where to map messages.

First, let's create the Flink job to copy leads into `agent_messages`.

* In your Kafka cluster, go to the **Stream processing** tab
* Click **Create workspace**
* Enter the following SQL

```sql
INSERT INTO agent_messages
SELECT 
    CAST(fullDocument._id AS BYTES) AS key,
    CAST(
        ROW(
            fullDocument.company, 
            fullDocument.companyWebsite, 
            fullDocument.email, 
            fullDocument.jobTitle, 
            fullDocument.leadSource, 
            fullDocument.name, 
            fullDocument.projectDescription
        ) 
        AS ROW<
            company_name STRING, 
            company_website STRING, 
            email STRING, 
            job_title STRING, 
            lead_source STRING, 
            name STRING, 
            project_description STRING
        >
    ) AS lead_data,
    CONCAT(
        'Name: ', fullDocument.name, ' | ',
        'Email: ', fullDocument.email, ' | ',
        'Company: ', fullDocument.company, ' | ',
        'Website: ', fullDocument.companyWebsite, ' | ',
        'Lead Source: ', fullDocument.leadSource, ' | ',
        'Job Title: ', fullDocument.jobTitle, ' | ',
        'Project Description: ', fullDocument.projectDescription
    ) AS context
FROM `incoming-leads.stratusdb.leads`
WHERE fullDocument IS NOT NULL AND operationType = 'insert';
```
* Click **Run**

#### Create the model reference for agent orchestration

Next, let's write the Flink job to create the model.

* In the same workspace, create a model using the connection you created previously

```sql
CREATE MODEL `agent_router`
INPUT (text STRING)
OUTPUT (response STRING)
WITH (
  'openai.connection'='openai-connection-sdr',
  'provider'='openai',
  'task'='text_generation',
  'openai.model_version' = 'gpt-4',
  'openai.system_prompt' = 'Your job is to use the output from an agent to figure out what the next agent to call is. 
   Strictly adhere to the the defined Input: for the agent and try to match that to the prompt.

   The description of the agents are as follows:

   Agent Name: Lead Ingestion Agent
   Description: Captures incoming leads, enriches data, and generates research reports.
   Input: Lead form data, formatted as JSON.
   Output: Generates a research report about a lead.

   Agent Name: Lead Scoring Agent
   Description: Scores leads, summarizes engagement strategies, and determines whether to nurture or actively engage.
   Input: The lead data and research report.
   Output: The lead data and a score for the lead, talking points, and whether to nurture or actively engage the lead.

   Agent Name: Active Outreach Agent
   Description: Creates AI-driven personalized outreach emails to book meetings.
   Input: The lead data and lead score information. The best leads go to this agent.
   Output: The campaign type and a list of emails to actively engage the lead.

   Agent Name: Nurture Campaign Agent
   Description: Designs email sequences based on lead origin and interest.
   Input: The lead data and lead score information. Lower quality leads go to this agent.
   Output: The campaign type and a list of emails to nurture the lead.

   Agent Name: Send Email Agent
   Description: Starts email campaign to lead.
   Input: List of emails to be part of an email campaign.
   Output: A success string.

   Based on the input, output the name of the agent and only the name of the agent.
   If you can not confidently map the input to an agent, respond with NONE.
   Any output other than the name of a defined agent or NONE will result in incorrect output.'
);
```

* Click **Run**

#### Create the Flink job to act as the orchestrator

* In the same workspace, insert the following SQL

```sql
INSERT INTO agent_predictions
SELECT 
    CAST(NULL AS BYTES) AS key,
    lead_data,
    context,
    prediction.response as agent_name
FROM (
    SELECT 
        context, 
        lead_data
    FROM agent_messages
) AS subquery
CROSS JOIN 
    LATERAL TABLE (
        ml_predict('agent_router', context)
    ) AS prediction;
```

* Click **Run**

### Run the application

1. In a terminal, navigate to your project directory. Run the app with the following command:

```shell
python -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
2. From your browser, navigate to http://localhost:3000 and you should see a lead capture form.
3. Enter some fake lead information.
4. Click **Submit**.
4. Wait for the agent flow to complete. If everything goes well, after a few minutes you'll have an email campaign in your terminal printed by the Send Email Agent.
