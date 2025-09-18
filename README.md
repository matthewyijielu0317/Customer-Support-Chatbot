# Customer Support Chatbot

This project prototypes a customer-support Retrieval-Augmented Generation (RAG) pipeline with per-user session memory, semantic caching, SQL grounding, and REST APIs. It is designed for local experimentation and can be adapted for production use.

## Getting Started

1. **Clone & install:** use Python 3.12, create a virtualenv, run `pip install -r requirements.txt`.
2. **Environment variables:** copy `.env.example` to `.env`, provide your own API keys/connection strings. The real `.env` should stay out of version control.
3. **Bootstrap data:** synthetic CSV fixtures live under `data/` (`fake_customers.csv`, `fake_orders.csv`, etc.). Load them into Postgres via `python scripts/ingest_tabular.py --dsn ... --customers data/fake_customers.csv ...`. The app assumes those tables exist at runtime.
4. **Run services:** start Redis, MongoDB, and Postgres locally (or via `docker compose -f deploy/docker/compose.yaml up`). Then launch the FastAPI app (`uvicorn app.api.main:app --reload`).
5. **(Optional) Launch the demo UI:** `streamlit run app/streamlit/main.py` opens a simple console for browsing sessions and chatting with the API.

## Open-Source Notes

- The CSV fixtures contain only synthetic data to keep the repo self-contained; no real PII is stored here.
- `.env.example` enumerates required settings; you must supply your own secrets and never commit them.
- A bootstrap script (see `scripts/ingest_tabular.py`) demonstrates how to load the sample dataset. For production, point the DSN at your managed database and ingest real data through your own pipeline.

## Features

- Session-aware chat endpoint with Redis recent-memory and Mongo history/summaries.
- Pinecone semantic cache for policy questions, Postgres SQL retrieval for customer/order lookups.
- Streamlined data ingestion scripts and integration tests with lightweight fakes.

Refer to inline docs and tests for deeper architecture details.
