# LLM Router with NVIDIA Dynamo Cloud Platform - Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying [NVIDIA LLM Router](https://github.com/NVIDIA-AI-Blueprints/llm-router) with the official [NVIDIA Dynamo Cloud Platform](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_cloud.html) on Kubernetes.

## Overview

This integration demonstrates how to deploy the official NVIDIA Dynamo Cloud Platform for distributed LLM inference and route requests intelligently using the NVIDIA LLM Router. The setup includes:

1. **NVIDIA Dynamo Cloud Platform**: Official distributed inference serving framework with disaggregated serving capabilities
2. **LLM Router**: Intelligent request routing based on task complexity and type
3. **Multiple LLM Models**: Various models deployed via Dynamo's inference graphs

### Architecture

The integration consists of:

- **NVIDIA Dynamo Cloud Platform**: Official distributed inference serving framework
- **LLM Router**: Routes requests to appropriate models based on task complexity and type
- **Multiple LLM Models**: Various models deployed via Dynamo's disaggregated serving

### Key Components

- **dynamo-cloud-deployment.yaml**: Configuration for Dynamo Cloud Platform deployment
- **dynamo-llm-deployment.yaml**: DynamoGraphDeployment for multi-LLM inference
- **router-config-dynamo.yaml**: Router policies for Dynamo integration
- **llm-router-values-dynamo.yaml**: Helm values for LLM Router with Dynamo
- **deploy-dynamo-integration.sh**: Automated deployment script

## Quick Start

### Automated Deployment (Recommended)

```bash
# Make the script executable
chmod +x deploy-dynamo-integration.sh

# Deploy everything (Dynamo + LLM Router)
./deploy-dynamo-integration.sh

# Or deploy components separately:
./deploy-dynamo-integration.sh --dynamo-only    # Deploy only Dynamo
./deploy-dynamo-integration.sh --router-only    # Deploy only LLM Router
./deploy-dynamo-integration.sh --verify-only    # Verify existing deployment
```

### Manual Deployment

If you prefer manual deployment or need to customize the process:

#### Step 1: Deploy NVIDIA Dynamo Cloud Platform

```bash
# 1. Clone Dynamo repository
git clone https://github.com/ai-dynamo/dynamo.git
cd dynamo

# 2. Configure environment (edit dynamo-cloud-deployment.yaml first)
export DOCKER_SERVER=nvcr.io/your-org
export IMAGE_TAG=latest
export NAMESPACE=dynamo-cloud
export DOCKER_USERNAME=your-username
export DOCKER_PASSWORD=your-password

# 3. Build and push Dynamo components
earthly --push +all-docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG

# 4. Deploy the platform
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE
cd deploy/cloud/helm
./deploy.sh --crds

# 5. Deploy LLM inference graph
kubectl apply -f ../../../dynamo-llm-deployment.yaml
```

#### Step 2: Deploy LLM Router

```bash
# 1. Create router namespace and ConfigMap
kubectl create namespace llm-router
kubectl create configmap router-config-dynamo \
  --from-file=router-config-dynamo.yaml \
  -n llm-router

# 2. Add NVIDIA Helm repository
helm repo add nvidia-llm-router https://helm.ngc.nvidia.com/nvidia-ai-blueprints/llm-router
helm repo update

# 3. Deploy LLM Router
helm upgrade --install llm-router nvidia-llm-router/llm-router \
  --namespace llm-router \
  --values llm-router-values-override.yaml \
  --wait --timeout=10m
```

## Prerequisites

- **Kubernetes cluster** (1.24+) with kubectl configured
- **Helm 3.x** for managing deployments
- **Earthly** for building Dynamo components ([Install Guide](https://earthly.dev/get-earthly))
- **NVIDIA GPU nodes** with GPU Operator installed
- **Container registry access** (NVIDIA NGC or private registry)
- **Git** for cloning repositories

## Configuration

### Dynamo Cloud Platform Configuration

Edit `dynamo-cloud-deployment.yaml` to configure:

```bash
# Container Registry Configuration
DOCKER_SERVER=nvcr.io/your-org          # Your container registry
IMAGE_TAG=latest                        # Image tag to use
DOCKER_USERNAME=your-username           # Registry username
DOCKER_PASSWORD=your-password           # Registry password

# Dynamo Cloud Platform Configuration
NAMESPACE=dynamo-cloud                   # Kubernetes namespace

# External Access Configuration
INGRESS_ENABLED=true                     # Enable ingress
INGRESS_CLASS=nginx                      # Ingress class
```

### LLM Model Configuration

The `dynamo-llm-deployment.yaml` file defines a `DynamoGraphDeployment` with multiple services:

- **Frontend**: API gateway (1 replica)
- **Processor**: Request processing (1 replica)
- **VllmWorker**: Multi-model inference (1 replica, 4 GPUs)
- **PrefillWorker**: Disaggregated prefill (2 replicas, 2 GPUs each)
- **Router**: KV-aware routing (1 replica)

**Total GPU Requirements**: 8 GPUs for models + 1 GPU for LLM Router = **9 GPUs**

### Ingress Configuration

The LLM Router is configured with ingress enabled for external access:

```yaml
ingress:
  enabled: true
  className: "nginx"  # Adjust for your ingress controller
  hosts:
    - host: llm-router.local  # Change to your domain
      paths:
        - path: /
          pathType: Prefix
```

**Important**: Update the `host` field in `llm-router-values-override.yaml` to match your domain:

```bash
# For production, replace llm-router.local with your actual domain
sed -i 's/llm-router.local/your-domain.com/g' llm-router-values-override.yaml
```

**For local testing**, add the ingress IP to your `/etc/hosts`:

```bash
# Get the ingress IP and add to hosts file
INGRESS_IP=$(kubectl get ingress llm-router -n llm-router -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "$INGRESS_IP llm-router.local" | sudo tee -a /etc/hosts
```

### Router Configuration

The `router-config-dynamo.yaml` configures routing policies:

| **Task Router** | **Model** | **Use Case** |
|-----------------|-----------|--------------|
| Brainstorming | llama-3.1-70b-instruct | Creative ideation |
| Chatbot | mixtral-8x22b-instruct | Conversational AI |
| Code Generation | llama-3.1-nemotron-70b-instruct | Programming tasks |
| Summarization | phi-3-mini-128k-instruct | Text summarization |
| Text Generation | llama-3.2-11b-vision-instruct | General text creation |
| Open QA | llama-3.1-405b-instruct | Complex questions |
| Closed QA | llama-3.1-8b-instruct | Simple Q&A |
| Classification | phi-3-mini-4k-instruct | Text classification |
| Extraction | llama-3.1-8b-instruct | Information extraction |
| Rewrite | phi-3-medium-128k-instruct | Text rewriting |

| **Complexity Router** | **Model** | **Use Case** |
|----------------------|-----------|--------------|
| Creativity | llama-3.1-70b-instruct | Creative tasks |
| Reasoning | llama-3.3-nemotron-super-49b | Complex reasoning |
| Contextual-Knowledge | llama-3.1-405b-instruct | Knowledge-intensive |
| Few-Shot | llama-3.1-70b-instruct | Few-shot learning |
| Domain-Knowledge | llama-3.1-nemotron-70b-instruct | Specialized domains |
| No-Label-Reason | llama-3.1-8b-instruct | Simple reasoning |
| Constraint | phi-3-medium-128k-instruct | Constrained tasks |

All routes point to: `http://dynamo-llm-service.dynamo-cloud.svc.cluster.local:8080/v1`

## Verification and Testing

### 1. Verify Dynamo Deployment

```bash
# Check Dynamo platform status
kubectl get pods -n dynamo-cloud
kubectl get dynamographdeployment -n dynamo-cloud

# Check services
kubectl get svc -n dynamo-cloud

# Test direct Dynamo endpoint
kubectl port-forward svc/dynamo-llm-service 8080:8080 -n dynamo-cloud &
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### 2. Test LLM Router Integration

```bash
# Option 1: Test via Ingress (recommended for production)
# First, add llm-router.local to your /etc/hosts file:
# echo "$(kubectl get ingress llm-router -n llm-router -o jsonpath='{.status.loadBalancer.ingress[0].ip}') llm-router.local" | sudo tee -a /etc/hosts

# Test task-based routing via ingress
curl -X POST http://llm-router.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Write a Python function"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "task_router"
    }
  }'

# Option 2: Test via port-forward (for development/testing)
kubectl port-forward svc/llm-router 8080:8000 -n llm-router &

# Test task-based routing via port-forward
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Write a Python function"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "task_router"
    }
  }'

# Test complexity-based routing via ingress
curl -X POST http://llm-router.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "complexity_router"
    }
  }'

# Test complexity-based routing via port-forward
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "complexity_router"
    }
  }'
```

### 3. Monitor Deployment

```bash
# Monitor Dynamo logs
kubectl logs -f deployment/dynamo-store -n dynamo-cloud

# Monitor LLM Router logs
kubectl logs -f deployment/llm-router -n llm-router

# Check resource usage
kubectl top pods -n dynamo-cloud
kubectl top pods -n llm-router
```

## How Dynamo Model Routing Works

The key insight is that Dynamo provides a **single gateway endpoint** that routes to different models based on the `model` parameter in the OpenAI-compatible API request:

1. **Single Endpoint**: `http://dynamo-llm-service.dynamo-cloud.svc.cluster.local:8080/v1`
2. **Model-Based Routing**: Dynamo routes internally based on the `model` field in requests
3. **OpenAI Compatibility**: Standard OpenAI API format with model selection

Example request:
```json
{
  "model": "llama-3.1-70b-instruct",  // Dynamo routes based on this
  "messages": [...],
  "temperature": 0.7
}
```

Dynamo's internal architecture handles:
- Model registry and discovery
- Request parsing and routing
- Load balancing across replicas
- KV cache management
- Disaggregated serving coordination

## Troubleshooting

### Common Issues

1. **Build failures**: Ensure earthly is installed and container registry access is configured
2. **CRD not found**: Wait for Dynamo platform to fully deploy before applying DynamoGraphDeployment
3. **Service communication**: Verify cross-namespace RBAC permissions
4. **Model loading**: Check GPU availability and resource requests

### Debugging Commands

```bash
# Check Dynamo platform
kubectl get pods -n dynamo-cloud
kubectl logs -f deployment/dynamo-store -n dynamo-cloud
kubectl describe dynamographdeployment llm-multi-model -n dynamo-cloud

# Check LLM Router
kubectl get pods -n llm-router
kubectl logs -f deployment/llm-router -n llm-router
kubectl describe configmap router-config-dynamo -n llm-router

# Check networking
kubectl exec -it deployment/llm-router -n llm-router -- nslookup dynamo-llm-service.dynamo-cloud.svc.cluster.local

# Check events
kubectl get events -n dynamo-cloud --sort-by=.metadata.creationTimestamp
kubectl get events -n llm-router --sort-by=.metadata.creationTimestamp
```

## Cleanup

```bash
# Remove LLM Router
helm uninstall llm-router -n llm-router
kubectl delete namespace llm-router

# Remove Dynamo deployment
kubectl delete dynamographdeployment llm-multi-model -n dynamo-cloud
kubectl delete namespace dynamo-cloud

# Remove Dynamo platform (if desired)
cd dynamo/deploy/cloud/helm
./deploy.sh --uninstall
```

## Files in This Directory

- **`README.md`** - This comprehensive deployment guide
- **`dynamo-cloud-deployment.yaml`** - Environment configuration for Dynamo Cloud Platform
- **`dynamo-llm-deployment.yaml`** - DynamoGraphDeployment for multi-LLM inference
- **`router-config-dynamo.yaml`** - Router configuration for Dynamo integration
- **`llm-router-values-override.yaml`** - Helm values override for LLM Router with Dynamo integration
- **`deploy-dynamo-integration.sh`** - Automated deployment script

## Resources

- [NVIDIA Dynamo Cloud Platform Documentation](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_cloud.html)
- [NVIDIA Dynamo Kubernetes Operator](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_operator.html)
- [NVIDIA Dynamo GitHub Repository](https://github.com/ai-dynamo/dynamo)
- [LLM Router GitHub Repository](https://github.com/NVIDIA-AI-Blueprints/llm-router)
- [LLM Router Helm Chart](https://github.com/NVIDIA-AI-Blueprints/llm-router/tree/main/deploy/helm/llm-router)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html) 