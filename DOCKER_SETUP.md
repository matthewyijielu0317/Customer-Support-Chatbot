# Docker Setup Guide

This guide will help you run the complete Customer Support Chatbot application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Environment variables configured (see below)

## Environment Setup

1. **Create a `.env` file** in the root directory with your API keys:

```bash
# Required for OpenAI integration
OPENAI_API_KEY=your_openai_api_key_here

# Required for vector search and semantic caching
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional: Additional configuration
ENVIRONMENT=prod
```

2. **Create the Pinecone index** (if not already created):
   - Log into your Pinecone console
   - Create an index named `ecomm-policies-v1`
   - Use dimensions: `1536` (for OpenAI text-embedding-3-small)
   - Use metric: `cosine`

## Quick Start

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Wait for all services to start** (this may take a few minutes on first run)

3. **Load sample data:**
   ```bash
   # In a new terminal, load customer data
   curl -X POST "http://localhost:8000/v1/ingest/csv" \
     -H "Content-Type: application/json" \
     -d '{
       "dsn": "postgresql+psycopg://user:password@localhost:5433/ecomm",
       "customers_csv_path": "/app/data/fake_customers.csv",
       "orders_csv_path": "/app/data/fake_orders.csv",
       "products_csv_path": "/app/data/fake_products.csv"
     }'
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Services Overview

The application runs the following services:

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | React/TypeScript UI |
| api | 8000 | FastAPI backend |
| postgres | 5433 | Customer/order database |
| redis | 6379 | Session storage |
| mongo | 27017 | Chat history |

## Demo Login

Use any email from the customer dataset with passcode `12345`:

**Example credentials:**
- Email: `dmadocjones0@oracle.com`
- Passcode: `12345`

## Useful Commands

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f api
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild after changes:**
```bash
docker-compose up --build
```

**Check service health:**
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Services won't start
- Check that required ports (3000, 8000, 5433, 6379, 27017) are available
- Verify your `.env` file has the required API keys
- Check Docker logs: `docker-compose logs`

### Database connection errors
- Ensure PostgreSQL is fully started before the API service
- Check the database DSN in docker-compose.yaml

### Frontend can't reach API
- The nginx proxy should handle this automatically
- Check that both frontend and api services are running

### Vector search not working
- Verify your Pinecone API key is correct
- Check that the index name matches in settings
- Ensure you've ingested documents into Pinecone

## Development

For development with hot-reload:

1. **Backend development:**
   ```bash
   # Start only the databases
   docker-compose up postgres redis mongo -d
   
   # Run API locally
   cd /path/to/project
   pip install -r requirements.txt
   uvicorn app.api.main:app --reload
   ```

2. **Frontend development:**
   ```bash
   # Start backend services
   docker-compose up api postgres redis mongo -d
   
   # Run frontend locally
   cd frontend
   npm install
   npm run dev
   ```

This setup gives you the best of both worlds: containerized dependencies with fast development iteration.

