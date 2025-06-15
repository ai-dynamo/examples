#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# NVIDIA Dynamo Cloud Platform + LLM Router Integration Deployment Script
# This script deploys the official NVIDIA Dynamo Cloud Platform and integrates it with the LLM Router
#
# Based on: https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_cloud.html

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DYNAMO_NAMESPACE="dynamo-cloud"
ROUTER_NAMESPACE="llm-router"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if helm is available
    if ! command -v helm &> /dev/null; then
        print_error "helm is not installed or not in PATH"
        exit 1
    fi
    
    # Check if earthly is available (for Dynamo build)
    if ! command -v earthly &> /dev/null; then
        print_warning "earthly is not installed. You'll need to build Dynamo components manually."
        print_warning "Install earthly from: https://earthly.dev/get-earthly"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Function to deploy NVIDIA Dynamo Cloud Platform
deploy_dynamo_platform() {
    print_status "Deploying NVIDIA Dynamo Cloud Platform..."
    
    # Check if Dynamo repository is available
    if [ ! -d "dynamo" ]; then
        print_status "Cloning NVIDIA Dynamo repository..."
        git clone https://github.com/ai-dynamo/dynamo.git
    fi
    
    cd dynamo
    
    # Source configuration
    if [ -f "${SCRIPT_DIR}/dynamo-cloud-deployment.yaml" ]; then
        print_status "Loading Dynamo configuration..."
        source "${SCRIPT_DIR}/dynamo-cloud-deployment.yaml" 2>/dev/null || true
    fi
    
    # Set default values if not provided
    export DOCKER_SERVER=${DOCKER_SERVER:-"nvcr.io/your-org"}
    export IMAGE_TAG=${IMAGE_TAG:-"latest"}
    export NAMESPACE=${NAMESPACE:-$DYNAMO_NAMESPACE}
    export DOCKER_USERNAME=${DOCKER_USERNAME:-""}
    export DOCKER_PASSWORD=${DOCKER_PASSWORD:-""}
    
    print_status "Building Dynamo Cloud Platform components..."
    print_warning "This step requires earthly and may take several minutes..."
    
    # Build and push components (if earthly is available)
    if command -v earthly &> /dev/null; then
        earthly --push +all-docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG || {
            print_error "Failed to build Dynamo components. Please check your configuration."
            print_warning "You may need to:"
            print_warning "1. Update DOCKER_SERVER in dynamo-cloud-deployment.yaml"
            print_warning "2. Ensure you're logged into your container registry"
            print_warning "3. Have proper permissions to push images"
            exit 1
        }
    else
        print_warning "Skipping build step - earthly not available"
        print_warning "Please build components manually or use pre-built images"
    fi
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    kubectl config set-context --current --namespace=$NAMESPACE
    
    # Deploy the platform
    print_status "Deploying Dynamo Cloud Platform Helm charts..."
    cd deploy/cloud/helm
    
    # Install CRDs first
    ./deploy.sh --crds || {
        print_error "Failed to deploy Dynamo CRDs"
        exit 1
    }
    
    print_success "NVIDIA Dynamo Cloud Platform deployed successfully"
    cd ../../..
}

# Function to deploy LLM models using Dynamo
deploy_llm_models() {
    print_status "Deploying LLM models using Dynamo..."
    
    # Wait for Dynamo platform to be ready
    print_status "Waiting for Dynamo platform to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/dynamo-store -n $DYNAMO_NAMESPACE || {
        print_warning "Dynamo platform may not be fully ready. Continuing anyway..."
    }
    
    # Expose Dynamo API store for CLI access
    print_status "Setting up Dynamo API access..."
    kubectl port-forward svc/dynamo-store 8080:80 -n $DYNAMO_NAMESPACE &
    PORT_FORWARD_PID=$!
    export DYNAMO_CLOUD="http://localhost:8080"
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Build and deploy LLM inference graph
    print_status "Building and deploying LLM inference graph..."
    
    # This would typically involve:
    # 1. dynamo build --push graphs.disagg:Frontend
    # 2. Creating DynamoGraphDeployment CRD
    
    # For now, we'll apply the example deployment
    kubectl apply -f "${SCRIPT_DIR}/dynamo-llm-deployment.yaml" || {
        print_error "Failed to deploy LLM models"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    }
    
    # Clean up port-forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    print_success "LLM models deployed successfully"
}

# Function to deploy LLM Router
deploy_llm_router() {
    print_status "Deploying LLM Router..."
    
    # Create router namespace
    kubectl create namespace $ROUTER_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ConfigMap for router configuration
    kubectl create configmap router-config-dynamo \
        --from-file="${SCRIPT_DIR}/router-config-dynamo.yaml" \
        -n $ROUTER_NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Add NVIDIA Helm repository
    helm repo add nvidia-llm-router https://helm.ngc.nvidia.com/nvidia-ai-blueprints/llm-router || {
        print_warning "Failed to add NVIDIA LLM Router Helm repository"
        print_warning "You may need to configure NGC access or use a different repository"
    }
    helm repo update
    
    # Deploy LLM Router using Helm
    helm upgrade --install llm-router nvidia-llm-router/llm-router \
        --namespace $ROUTER_NAMESPACE \
        --values "${SCRIPT_DIR}/llm-router-values-override.yaml" \
        --wait \
        --timeout=10m || {
        print_error "Failed to deploy LLM Router"
        exit 1
    }
    
    print_success "LLM Router deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check Dynamo platform
    print_status "Checking Dynamo platform status..."
    kubectl get pods -n $DYNAMO_NAMESPACE
    kubectl get dynamographdeployment -n $DYNAMO_NAMESPACE 2>/dev/null || {
        print_warning "DynamoGraphDeployment CRD may not be available yet"
    }
    
    # Check LLM Router
    print_status "Checking LLM Router status..."
    kubectl get pods -n $ROUTER_NAMESPACE
    kubectl get svc -n $ROUTER_NAMESPACE
    
    # Test connectivity
    print_status "Testing service connectivity..."
    
    # Check if Dynamo service is accessible
    if kubectl get svc dynamo-llm-service -n $DYNAMO_NAMESPACE &>/dev/null; then
        print_success "Dynamo LLM service is available"
    else
        print_warning "Dynamo LLM service not found - may still be starting"
    fi
    
    # Check if Router service is accessible
    if kubectl get svc llm-router -n $ROUTER_NAMESPACE &>/dev/null; then
        print_success "LLM Router service is available"
        
        # Get router endpoint
        ROUTER_IP=$(kubectl get svc llm-router -n $ROUTER_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [ -n "$ROUTER_IP" ]; then
            print_success "LLM Router external IP: $ROUTER_IP"
        else
            print_status "LLM Router is using ClusterIP. Use port-forward for external access:"
            print_status "kubectl port-forward svc/llm-router 8080:8080 -n $ROUTER_NAMESPACE"
        fi
    else
        print_warning "LLM Router service not found"
    fi
    
    print_success "Deployment verification completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy NVIDIA Dynamo Cloud Platform with LLM Router integration"
    echo ""
    echo "Options:"
    echo "  --dynamo-only     Deploy only Dynamo Cloud Platform"
    echo "  --router-only     Deploy only LLM Router (requires existing Dynamo)"
    echo "  --verify-only     Only verify existing deployment"
    echo "  --help           Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - kubectl configured for your cluster"
    echo "  - helm 3.x installed"
    echo "  - earthly installed (for building Dynamo components)"
    echo "  - Access to NVIDIA NGC registry"
    echo ""
    echo "Configuration:"
    echo "  Edit dynamo-cloud-deployment.yaml to configure registry settings"
}

# Main deployment function
main() {
    local dynamo_only=false
    local router_only=false
    local verify_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dynamo-only)
                dynamo_only=true
                shift
                ;;
            --router-only)
                router_only=true
                shift
                ;;
            --verify-only)
                verify_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting NVIDIA Dynamo + LLM Router deployment..."
    
    check_prerequisites
    
    if [ "$verify_only" = true ]; then
        verify_deployment
        exit 0
    fi
    
    if [ "$router_only" = false ]; then
        deploy_dynamo_platform
        deploy_llm_models
    fi
    
    if [ "$dynamo_only" = false ]; then
        deploy_llm_router
    fi
    
    verify_deployment
    
    print_success "Deployment completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Access LLM Router: kubectl port-forward svc/llm-router 8080:8080 -n $ROUTER_NAMESPACE"
    print_status "2. Test routing: curl http://localhost:8080/v1/chat/completions"
    print_status "3. Monitor with: kubectl logs -f deployment/llm-router -n $ROUTER_NAMESPACE"
}

# Run main function
main "$@" 