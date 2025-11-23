#!/bin/bash
# Build and push certean-billing to ECR

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "eu-west-1")

# ECR repository name
REPO_NAME="certean-billing"

# Full ECR URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "Building Docker image..."
docker build -t ${REPO_NAME}:latest .

echo "Tagging for ECR..."
docker tag ${REPO_NAME}:latest ${ECR_URI}:latest

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo "Creating ECR repository if it doesn't exist..."
aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${AWS_REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${REPO_NAME} --region ${AWS_REGION}

echo "Pushing to ECR..."
docker push ${ECR_URI}:latest

echo ""
echo "✅ Image pushed successfully!"
echo "ECR URI: ${ECR_URI}:latest"
echo ""
echo "You can now select this image in App Runner."
