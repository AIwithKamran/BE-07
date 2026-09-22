# 🚀 Usage Metering & Billing Engine

A robust, idempotent usage metering and billing engine built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. This project was developed as a capstone to demonstrate the core architecture required for metering API usage, calculating AI token costs, and handling subscription upgrades via **Safepay**.

## ✨ Features
- **Idempotency**: Prevents double-billing for the same request using `idempotency_key` checks (Probe 1).
- **Dynamic Quotas**: Tracks monthly limits for API calls and AI tokens, rejecting requests with `429 Too Many Requests` when limits are exceeded (Probe 2).
- **Cost Calculation**: Accurately calculates costs based on different token categories (Input, Output, Thinking tokens) similar to Gemini and OpenAI pricing models.
- **Safepay Integration**: Generates checkout links and securely upgrades user plans via Webhooks using HMAC SHA-256 signature verification (Probe 4).
- **Asynchronous Architecture**: Built using `asyncpg` for high-performance, non-blocking database queries.

## 🛠️ Tech Stack
- **Backend**: Python 3, FastAPI
- **Database**: PostgreSQL 16 (Dockerized)
- **ORM**: SQLAlchemy (Async)
- **Dependency Management**: `uv`
- **Payment Gateway**: Safepay (Sandbox)

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- [Docker & Docker Compose](https://www.docker.com/) (For PostgreSQL)
- [Python 3.10+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) (For ultra-fast package management)

### 2. Environment Setup
Create a `.env` file in the root directory and add the following keys:
```env
DB_URL="postgresql+asyncpg://admin:admin@localhost:5432/capstone"

# Safepay Sandbox Keys
SAFEPAY_KEY="your_safepay_client_key_here"
SAFEPAY_WEBHOOK_SECRET="your_safepay_webhook_secret_here"
```

### 3. Spin up the Database
Start the PostgreSQL container in the background:
```bash
docker compose up -d
```

### 4. Install Dependencies
Using `uv`, sync your dependencies:
```bash
uv pip install -r requirements.txt
# (or just use `uv add <packages>` if managing manually)
```

### 5. Seed the Database
Run the seed script to create the tables and populate dummy plans and tenants:
```bash
python seed.py
```
*Expected output: `Seeded successfully!`*

### 6. Start the API Server
Launch the FastAPI server with live reloading:
```bash
uvicorn main:app --reload
```

---

## 🧪 Testing the API

Once the server is running, navigate to the Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore the endpoints.

### Key Endpoints to Test:
- **`POST /generate`**: Simulates a billable event (AI Token or API Call). Pass an `idempotency_key` to test duplicate rejection, and a `token_type` ("input", "output", "thinking") to test the cost calculator!
- **`GET /usage/{tenant_id}`**: Fetches a rollup of a tenant's current monthly usage and limits.
- **`POST /checkout`**: Generates a Safepay checkout session to upgrade to the Pro plan.
- **`POST /webhooks/safepay`**: Simulates Safepay's success webhook. Requires a valid HMAC SHA-256 signature in the `x-sfpy-signature` header.

## 📜 Capstone Probes Passed
- [x] **Probe 1**: Idempotency checks to prevent double billing.
- [x] **Probe 2**: Enforces Quota limits and returns `429`.
- [x] **Probe 3**: Integration with an external payment gateway (Safepay).
- [x] **Probe 4**: Webhook signature verification prevents forged upgrades.
