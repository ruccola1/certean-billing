#!/bin/bash
set -e

echo "🔨 Building certean-billing Docker image..."

# Build the image
docker build -t certean-billing:latest .

echo "✅ Build complete!"
echo ""
echo "📦 Next steps - run these commands:"
echo ""
echo "# Get AWS account ID"
echo "AWS_ACCOUNT_ID=\$(aws sts get-caller-identity --query Account --output text)"
echo "AWS_REGION=eu-west-1"
echo ""
echo "# Create ECR repo (if needed)"
echo "aws ecr create-repository --repository-name certean-billing --region eu-west-1 || true"
echo ""
echo "# Tag image"
echo "docker tag certean-billing:latest \${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com/certean-billing:latest"
echo ""
echo "# Login to ECR"
echo "aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin \${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com"
echo ""
echo "# Push to ECR"
echo "docker push \${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com/certean-billing:latest"
