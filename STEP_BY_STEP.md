# Step-by-Step: Push certean-billing to ECR

## Step 1: Open Terminal
Open Terminal on your Mac (Applications → Utilities → Terminal)

## Step 2: Navigate to the billing directory
```bash
cd /Users/nicolaszander/Desktop/certean/dev/certean-billing
```

## Step 3: Verify Docker is running
```bash
docker --version
docker ps
```
If Docker isn't running, start Docker Desktop.

## Step 4: Verify AWS CLI is configured
```bash
aws --version
aws sts get-caller-identity
```
This should show your AWS account ID. If it fails, configure AWS CLI first.

## Step 5: Build the Docker image
```bash
docker build -t certean-billing:latest .
```
This will take a few minutes. Wait for "Successfully built" message.

## Step 6: Get your AWS account ID
```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $AWS_ACCOUNT_ID"
```

## Step 7: Create ECR repository (if it doesn't exist)
```bash
aws ecr create-repository --repository-name certean-billing --region eu-west-1
```
If it says "already exists", that's fine - skip to next step.

## Step 8: Tag the image for ECR
```bash
docker tag certean-billing:latest ${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com/certean-billing:latest
```

## Step 9: Login to ECR
```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com
```
You should see "Login Succeeded".

## Step 10: Push to ECR
```bash
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.eu-west-1.amazonaws.com/certean-billing:latest
```
This will take a few minutes. Wait for "Pushed" message.

## Step 11: Verify in App Runner
1. Go back to AWS App Runner
2. Refresh the ECR repository list
3. Look for "certean-billing"
4. Select it and continue with deployment

## Troubleshooting

**Docker not found:**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Start Docker Desktop and wait for it to be running

**AWS CLI not configured:**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: eu-west-1
# Enter output format: json
```

**Permission denied:**
- Make sure you have ECR permissions in AWS
- Check your IAM user/role has `ecr:*` permissions
