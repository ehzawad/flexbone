#!/bin/bash

# OCR API Deployment Script for Google Cloud Run
# Usage: ./scripts/deploy.sh

set -e

# Configuration
PROJECT_ID="ehz-stuff"
REGION="asia-southeast1"
SERVICE_NAME="ocr-api"
REPOSITORY_NAME="ocr-api"
IMAGE_NAME="ocr-api"

echo "=========================================="
echo "OCR API - Cloud Run Deployment Script"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "gcloud CLI found"

# Set project
echo "Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo ""
echo "Enabling required GCP APIs..."
gcloud services enable run.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo "Required APIs enabled"

# Create Artifact Registry repository (if not exists)
echo ""
echo "Checking Artifact Registry repository..."
if ! gcloud artifacts repositories describe $REPOSITORY_NAME --location=$REGION &> /dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create $REPOSITORY_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="OCR API Docker images"
    echo "Repository created"
else
    echo "Repository already exists"
fi

# Build and push image
echo ""
echo "Building and pushing Docker image..."
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:latest"

gcloud builds submit . --tag $IMAGE_TAG

echo "Image built and pushed"

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --timeout 60 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,MAX_FILE_SIZE_MB=10,RATE_LIMIT_PER_MINUTE=60,CACHE_TTL_SECONDS=3600,MAX_CACHE_SIZE=1000"

echo "Deployment complete"

# Get service URL
echo ""
echo "=========================================="
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service deployed successfully!"
echo ""
echo "Service URL: $SERVICE_URL"
echo ""
echo "Test your API with:"
echo "curl -X POST -F \"image=@testimages/simple.jpg\" $SERVICE_URL/extract-text"
echo "=========================================="

