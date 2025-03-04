# Lead Capture Web Application

This project is the user-facing web application for capturing a lead.

This application saves that data to MongoDB. Behind the scenes, Kafka kick starts the agentic process, eventually generating and email engagement plan.

Refer to the main `README.md` for detailed instructions in how to setup and configure this application.

## Configuring the application

You need to create a `.env` file with the following values:
* MONGODB_URI

## Running the application

From the your terminal, navigate to the `/web-application` directory and enter the following command:

```shell
npm install
npm run dev
```