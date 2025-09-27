# Customer Support Chatbot

This project is a sophisticated, full-stack customer support chatbot that leverages a Retrieval-Augmented Generation (RAG) pipeline. It's designed to provide intelligent, context-aware responses by drawing from both unstructured documents and structured databases. The application is fully containerized with Docker for easy setup and deployment.

## Features

- **Conversational AI:** A session-aware chat interface that maintains conversation history.
- **Hybrid RAG Pipeline:**
    - Retrieves information from PDF documents (e.g., policies, guides) using vector search with Pinecone.
    - Queries structured data from a PostgreSQL database (e.g., customer info, order details) using natural language to SQL translation.
- **Semantic Caching:** Reduces latency and API costs by caching similar queries and their responses.
- **Modern Tech Stack:**
    - **Frontend:** React, TypeScript, Vite, and Tailwind CSS.
    - **Backend:** FastAPI, Python 3.12, and LangGraph for building the RAG pipeline.
    - **Databases:** PostgreSQL for structured data, MongoDB for chat history, Redis for session management, and Pinecone for vector storage.
- **Dockerized Environment:** The entire application stack can be spun up with a single `docker-compose` command.
- **Data Ingestion:** REST API endpoints for ingesting both PDF documents and CSV files into the system.
- **Agent Escalation:** A system for flagging conversations for review by a human agent.

## Architecture

The application is composed of several services that work together:

- **Frontend:** A React-based single-page application that provides the user interface for the chatbot.
- **API Backend:** A FastAPI application that exposes REST endpoints for chat, session management, data ingestion, and more.
- **RAG Pipeline:** Built with LangGraph, this is the core of the chatbot's intelligence. It orchestrates a series of nodes to process user queries:
    1.  **Router:** Determines the type of query (e.g., a policy question or a database lookup).
    2.  **Cache Check:** Checks if a semantically similar query has been answered before.
    3.  **SQL Retriever:** If needed, translates the natural language query into SQL, executes it against the PostgreSQL database, and retrieves the results.
    4.  **Document Retriever:** If needed, performs a vector search in Pinecone to find relevant document snippets.
    5.  **Generate:** Uses a large language model (like OpenAI's GPT) to synthesize an answer based on the retrieved context.
    6.  **Groundedness Check:** Verifies that the generated answer is grounded in the retrieved information to prevent hallucinations.
- **Databases:**
    - **PostgreSQL:** Stores structured business data like customers, products, and orders.
    - **MongoDB:** Persists long-term chat history for each session.
    - **Redis:** Manages active user sessions and caches recent messages for quick access.
    - **Pinecone:** Stores vector embeddings of documents for efficient similarity search.

## Project Structure

```
.
├── app/                  # FastAPI application code
│   ├── api/              # API endpoints (routers)
│   └── streamlit/        # (Optional) Streamlit demo UI
├── data/                 # Sample data (PDFs and CSVs)
├── frontend/             # React frontend application
│   └── src/
├── src/                  # Core Python source code
│   ├── graph/            # LangGraph RAG pipeline definition
│   ├── ingestion/        # Data ingestion scripts
│   ├── persistence/      # Database interaction logic
│   ├── retrievers/       # Document and SQL retrievers
│   └── vectorstores/     # Vector store integration
├── tests/                # Automated tests
├── docker-compose.yaml   # Docker services definition
├── Dockerfile            # Dockerfile for the backend API
└── README.md             # This file
```

## Getting Started (Docker Recommended)

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key
- A Pinecone API key

### 1. Environment Setup

Create a `.env` file in the project root by copying the `.env.example` file (if it exists) or creating a new one. Add your API keys:

```bash
OPENAI_API_KEY="your_openai_api_key"
PINECONE_API_KEY="your_pinecone_api_key"
```

You will also need to create a Pinecone index named `ecomm-policies-v1` with `1536` dimensions (for OpenAI's `text-embedding-3-small` model) and a `cosine` metric.

### 2. Build and Run the Application

```bash
docker-compose up --build
```

This will build the Docker images and start all the services. The first time you run this, it may take a few minutes to download the images and build the containers.

### 3. Ingest Data

Once the services are running, you need to load the sample data.

#### Ingest Tabular Data

Run the following `curl` command to load the CSV data into the PostgreSQL database:

```bash
curl -X POST "http://localhost:8000/v1/ingest/csv" \
  -H "Content-Type: application/json" \
  -d '{
    "dsn": "postgresql+psycopg://user:password@postgres:5432/ecomm",
    "customers_csv_path": "/app/data/fake_customers.csv",
    "orders_csv_path": "/app/data/fake_orders.csv",
    "products_csv_path": "/app/data/fake_products.csv"
  }'
```

#### Ingest Documents

To ingest the policy documents into Pinecone, run:

```bash
curl -X POST "http://localhost:8000/v1/ingest/docs" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/app/data"
  }'
```

### 4. Access the Application

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

You can log in with any email from `fake_customers.csv` and the passcode `12345`. For example: `dmadocjones0@oracle.com`.

## Development

For local development with hot-reloading:

### Backend

1.  Start the databases in Docker:
    ```bash
    docker-compose up postgres redis mongo -d
    ```
2.  Install Python dependencies and run the FastAPI server:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.api.main:app --reload
    ```

### Frontend

1.  Start the backend services:
    ```bash
    docker-compose up api postgres redis mongo -d
    ```
2.  Install Node.js dependencies and run the development server:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Testing

The project includes a suite of tests. To run them, first ensure you have the development dependencies installed:

```bash
pip install -r requirements.txt
```

Then, run pytest from the project root:

```bash
pytest
```
