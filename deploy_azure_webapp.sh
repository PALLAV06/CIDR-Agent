#!/bin/bash

# Exit on error
set -e

# Prompt for required values
read -p "Azure Resource Group name [cidr-agent-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-cidr-agent-rg}

read -p "Azure region [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

read -p "Azure Container Registry name (must be unique, lowercase, 5-50 chars) [cidragentacr$RANDOM]: " ACR_NAME
ACR_NAME=${ACR_NAME:-cidragentacr$RANDOM}

read -p "Web App name (must be unique) [cidr-agent-webapp-$RANDOM]: " WEBAPP_NAME
WEBAPP_NAME=${WEBAPP_NAME:-cidr-agent-webapp-$RANDOM}

read -p "Docker image name [cidr-agent-app]: " IMAGE_NAME
IMAGE_NAME=${IMAGE_NAME:-cidr-agent-app}

# Step selection for resuming
cat <<EOF
Which step do you want to start from?
1. Create resource group
2. Create Azure Container Registry
3. Login to ACR
4. Build and push Docker image
5. Create App Service plan
6. Create Web App for Containers
7. Configure Web App to use ACR credentials
EOF
read -p "Enter step number to start from [1]: " START_STEP
START_STEP=${START_STEP:-1}

# 1. Create resource group
if [ $START_STEP -le 1 ]; then
  echo "[Step 1] Creating resource group..."
  az group create --name $RESOURCE_GROUP --location $LOCATION
fi

# 2. Create Azure Container Registry
if [ $START_STEP -le 2 ]; then
  echo "[Step 2] Creating Azure Container Registry..."
  az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic || true
fi

# 3. Login to ACR
if [ $START_STEP -le 3 ]; then
  echo "[Step 3] Logging in to ACR..."
  az acr login --name $ACR_NAME
fi

# 4. Build and push Docker image
if [ $START_STEP -le 4 ]; then
  echo "[Step 4] Building and pushing Docker image..."
  az acr build --registry $ACR_NAME --image $IMAGE_NAME:latest .
fi

# 5. Create App Service plan
if [ $START_STEP -le 5 ]; then
  echo "[Step 5] Creating App Service plan..."
  az appservice plan create --name "${WEBAPP_NAME}-plan" --resource-group $RESOURCE_GROUP --is-linux --sku B1 || true
fi

# 6. Create Web App for Containers
if [ $START_STEP -le 6 ]; then
  echo "[Step 6] Creating Web App for Containers..."
  az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan "${WEBAPP_NAME}-plan" \
    --name $WEBAPP_NAME \
    --deployment-container-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest || true
fi

# 7. Configure Web App to use ACR credentials
if [ $START_STEP -le 7 ]; then
  echo "[Step 7] Configuring Web App to use ACR credentials..."
  ACR_USERNAME=$(az acr credential show -n $ACR_NAME --query username -o tsv)
  ACR_PASSWORD=$(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv)
  az webapp config container set \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io \
    --docker-registry-server-user $ACR_USERNAME \
    --docker-registry-server-password $ACR_PASSWORD
fi

# 8. Output the app URL
echo "\nDeployment complete!"
echo "Your app will be available at: https://$WEBAPP_NAME.azurewebsites.net" 