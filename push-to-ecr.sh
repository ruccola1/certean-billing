#!/bin/bash
set -e

echo "🚀 Building and pushing certean-billing to ECR..."
echo ""

# Get AWS account ID and region
echo "📋 Getting AWS account info..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=eu-west-1

echo "✅ AWS Account: ${AWS_ACCOUNT_ID}"
echo "✅ Region: ${AWS_REGION}"
echo ""

# ECR repository name
REPO_NAME="certean-billing"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t ${REPO_NAME}:latest .

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository (if needed)..."
aws ecr create-repository --repository-name ${REPO_NAME} --region ${AWS_REGION} 2>/dev/null || echo "Repository already exists"

# Tag image
echo "🏷️  Tagging image..."
docker tag ${REPO_NAME}:latest ${ECR_URI}:latest

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Push to ECR
echo "📤 Pushing to ECR..."
docker push ${ECR_URI}:latest

echo ""
echo "✅ Success! Image pushed to ECR"
echo "📍 ECR URI: ${ECR_URI}:latest"
echo ""
echo "You can now select this image in App Runner:"
echo "  Repository: ${REPO_NAME}"
echo "  Tag: latest"

