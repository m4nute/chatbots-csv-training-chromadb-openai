# Train your Chatbots dynamically with CSV files!

## Introduction

This is an API built with ChromaDB and OpenAI API (GPT 3.5).
You can:

- Create a user
- Create chatbots for that user
- Train chatbots individually with CSV files, and persist their training
- Chat with the chatbots

## How to use

1. Clone the repo in your local machine
2. Cd into the project folder
3. Make an .env file and fill the variables like in the .env.example file. The superuser_token can be any random string, that you will later use to authenticate.
4. Run docker compose up --build
5. Start testing! Follow the guide below.

# API Documentation

This README provides an overview of the endpoints available in the FastAPI application and demonstrates how to use them.

## Table of Contents

- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Clear Database](#clear-database)
  - [Heartbeat](#heartbeat)
  - [Create Client](#create-client)
  - [Get Bots](#get-bots)
  - [Get Clients](#get-clients)
  - [Get Client](#get-client)
  - [Create Bot](#create-bot)
  - [Upload File (Bot Ingest)](#upload-file-bot-ingest)
  - [Bot Query](#bot-query)

## Authentication

To access all /client endpoints, you need to include an `Authorization` header with a bearer token. The token is the same you use in your .env file, and should be included as follows:

Authorization: Bearer <superuser_token>

## Endpoints

### Clear Database

Clear the Chroma database.

- **Endpoint:** `/clear`
- **HTTP Method:** GET
- **Usage:** Clears the Chroma database.

### Heartbeat

Check the heartbeat of the Chroma service.

- **Endpoint:** `/heartbeat`
- **HTTP Method:** GET
- **Usage:** Checks the heartbeat of the Chroma service.

### Create Client

Create a new client.

- **Endpoint:** `/client/create`
- **HTTP Method:** POST
- **Usage:** Create a new client with the specified name and the maximum number of allowed bots.

**Parameters**:

- `name` (Form Parameter): The name of the client.
- `max_bots_allowed` (Form Parameter): The maximum number of bots allowed for the client.

### Get Bots

Retrieve a list of bots for an authorized client.

- **Endpoint:** `/bots`
- **HTTP Method:** GET
- **Usage:** Retrieves a list of bots associated with an authorized client.

### Get Clients

Retrieve a paginated list of clients.

- **Endpoint:** `/clients`
- **HTTP Method:** GET
- **Usage:** Retrieves a paginated list of clients.

**Parameters**:

- `page` (Query Parameter, Default: 1): The page number for pagination.
- `perPage` (Query Parameter, Default: 10, Max: 100): The number of clients per page.

### Get Client

Retrieve client details by client ID.

- **Endpoint:** `/client/{clientId}`
- **HTTP Method:** GET
- **Usage:** Retrieves details of a client by client ID.

**Parameters**:

- `clientId` (Path Parameter): The unique identifier of the client.

### Create Bot

Create a new bot for an authorized client.

- **Endpoint:** `/bot/create`
- **HTTP Method:** POST
- **Usage:** Create a new bot for an authorized client with the specified name.

**Parameters**:

- `name` (Form Parameter): The name of the bot.

### Upload File (Bot Ingest)

Ingest data from an uploaded CSV file into the Chroma database for a specific bot.

- **Endpoint:** `/bot/ingest`
- **HTTP Method:** POST
- **Usage:** Ingest data from an uploaded CSV file into the Chroma database for a specific bot.

**Parameters**:

- `token` (Form Parameter): The bot's token.
- `source_id` (Form Parameter): The source ID for the data.
- `file` (File Upload): The CSV file to be ingested.

### Bot Query

Query a bot for responses.

- **Endpoint:** `/bot/query`
- **HTTP Method:** POST
- **Usage:** Query a bot for responses based on user input.

**Parameters**:

- `body` (JSON Body Parameter): The user's query.
- `bot_token` (JSON Body Parameter, Optional): The bot's token.
- `auth_token` (JSON Body Parameter, Optional): The authentication token.
