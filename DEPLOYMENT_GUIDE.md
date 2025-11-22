# AWS App Runner Deployment Guide

## Prerequisites
- AWS Account with App Runner access
- GitHub repository for certean-billing (or use existing repo)
- MongoDB URI and Stripe keys ready

## Step 1: Push to GitHub

```bash
cd certean-billing
git init
git add .
git commit -m "Initial billing service"
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Step 2: Create App Runner Service

1. Go to AWS Console → App Runner
2. Click "Create service"
3. Choose "Source code repository"
4. Connect to GitHub and select your `certean-billing` repository
5. Select branch: `main`

## Step 3: Configure Build

- **Build type**: Docker
- **Dockerfile path**: `Dockerfile` (in root)
- **Port**: `8001`

## Step 4: Set Environment Variables

In App Runner configuration, add:

```
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=c_monitor_shared
STRIPE_SECRET_KEY=sk_test_...
FRONTEND_URL=https://main.d2uoumf6pfk145.amplifyapp.com
API_KEY=cbebae12ccf204ca7239bedc5df2dd69
```

## Step 5: Deploy

1. Review configuration
2. Click "Create & deploy"
3. Wait for deployment (2-3 minutes)
4. Note the service URL (e.g., `https://xxxxx.eu-west-1.awsapprunner.com`)

## Step 6: Update Frontend

Add to Amplify environment variables:

```
VITE_BILLING_API_URL=https://xxxxx.eu-west-1.awsapprunner.com
```

## Step 7: Test

```bash
# Health check
curl https://xxxxx.eu-west-1.awsapprunner.com/health

# Billing endpoint (with auth)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://xxxxx.eu-west-1.awsapprunner.com/api/stripe/billing/test123
```

## Troubleshooting

- Check App Runner logs if deployment fails
- Verify environment variables are set correctly
- Ensure MongoDB URI is accessible from App Runner
- Check Stripe key is valid
