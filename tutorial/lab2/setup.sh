#!/bin/bash
# Lab 2 Setup Script
# Adds Textract support and creates an S3 bucket

set -e

echo "=== Lab 2: PDF Extraction with Textract ==="
echo ""

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="resume-agent-dev-${ACCOUNT_ID}"
REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "Account: ${ACCOUNT_ID}"
echo "Region: ${REGION}"
echo "Bucket: ${BUCKET_NAME}"
echo ""

# Create S3 bucket if it doesn't exist
if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo "✓ S3 bucket already exists: ${BUCKET_NAME}"
else
    echo "Creating S3 bucket..."
    aws s3 mb "s3://${BUCKET_NAME}" --region "${REGION}"
    echo "✓ S3 bucket created: ${BUCKET_NAME}"
fi

# Export for use in scripts
echo ""
echo "Set this environment variable before running the steps:"
echo ""
echo "  export RESUME_S3_BUCKET=${BUCKET_NAME}"
echo ""
echo "Then run: uv run python step1_textract_basics.py"
