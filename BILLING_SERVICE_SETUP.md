# Billing Service Setup Complete

## What Was Done

1. ✅ Removed Stripe routes from `certean-ai` backend
2. ✅ Created new `certean-billing` service
3. ✅ Updated frontend to use billing service

## Next Steps

### 1. Deploy Billing Service

Deploy `certean-billing` to AWS App Runner:

1. Create new App Runner service
2. Connect to GitHub (or create new repo for certean-billing)
3. Set environment variables:
   - `MONGODB_URI`
   - `MONGODB_DB_NAME=c_monitor_shared`
   - `STRIPE_SECRET_KEY`
   - `FRONTEND_URL`
   - `API_KEY` (optional)

### 2. Update Frontend Environment Variables

Add to Amplify environment variables:

```env
VITE_BILLING_API_URL=https://your-billing-service.apprunner.com
```

If not set, it will fall back to `VITE_API_BASE_URL` or `http://localhost:8001`

### 3. Test

1. Start billing service locally: `python backend/main.py`
2. Test health: `curl http://localhost:8001/health`
3. Test billing endpoint: `curl http://localhost:8001/api/stripe/billing/test123`

## Architecture

```
Frontend (certean-monitor)
  ├─> certean-ai (port 8000) - Compliance analysis steps
  └─> certean-billing (port 8001) - Stripe billing
```

Both services share the same MongoDB (`c_monitor_shared` for billing data).
