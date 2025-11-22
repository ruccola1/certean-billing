# Certean Billing Backend Service

Separate backend service for Stripe billing and subscription management.

## Purpose

This service handles all Stripe-related functionality, separated from the main `certean-ai` compliance analysis backend:

- Stripe checkout session creation
- Stripe customer portal
- Webhook handling
- Billing information retrieval
- Subscription management

## Architecture

- **FastAPI** backend
- **MongoDB** for subscription/invoice storage (uses `c_monitor_shared` database)
- **Stripe API** integration
- Runs on port **8001** (different from certean-ai which runs on 8000)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=c_monitor_shared

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxx
FRONTEND_URL=https://your-frontend-url.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001

# Authentication (Optional)
API_KEY=your-api-key-here
```

### 3. Run Locally

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

Or:

```bash
python backend/main.py
```

## API Endpoints

All endpoints are under `/api/stripe`:

- `POST /api/stripe/create-checkout-session` - Create Stripe checkout session
- `POST /api/stripe/create-portal-session` - Create customer portal session
- `GET /api/stripe/billing/{client_id}` - Get billing information
- `POST /api/stripe/webhooks/stripe` - Stripe webhook handler

## Health Check

```bash
curl http://localhost:8001/health
```

## Deployment

### AWS App Runner

1. Create new App Runner service
2. Connect to GitHub repository
3. Set environment variables in App Runner configuration
4. Deploy

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Frontend Configuration

Update frontend `.env`:

```env
VITE_BILLING_API_URL=http://localhost:8001  # or your deployed URL
```

Then update API service to use `VITE_BILLING_API_URL` for Stripe endpoints.

## Why Separate?

- **Separation of Concerns**: Compliance analysis (certean-ai) vs Billing (certean-billing)
- **Independent Scaling**: Scale billing service separately
- **Security**: Isolate payment processing
- **Deployment**: Deploy billing updates without affecting compliance analysis
