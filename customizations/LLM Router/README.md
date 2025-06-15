# LLM Router with NVIDIA Dynamo - Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying [NVIDIA LLM Router](https://github.com/NVIDIA-AI-Blueprints/llm-router) with [NVIDIA Dynamo](https://github.com/ai-dynamo/dynamo/tree/main/deploy/cloud) on Kubernetes.

## Overview

The LLM Router intelligently routes LLM requests to the most appropriate model based on the task at hand. This deployment strategy will:

- **Deploy Dynamo using Cloud Operator** - Use the official Dynamo cloud operator for robust, scalable deployment
- **Deploy LLMs via Dynamo Cloud** - Host multiple LLM models through Dynamo's cloud infrastructure
- **Configure LLM Router** - Point the router to different models hosted on Dynamo cloud

## Quick Start

Choose your deployment option using the provided configuration files:

### Option 1: Minimal Verification (1 GPU)
```bash
# 1. Deploy Dynamo Cloud Operator
kubectl apply -f https://github.com/ai-dynamo/dynamo/releases/latest/download/dynamo-operator.yaml

# 2. Deploy single LLM via Dynamo
kubectl create namespace dynamo
kubectl apply -f dynamo-single-llm-config.yaml

# 3. Clone LLM Router and deploy with Helm
git clone https://github.com/NVIDIA-AI-Blueprints/llm-router.git
cd llm-router

# 4. Create ConfigMap and deploy router
kubectl create configmap router-config \
  --from-file=config.yaml=../router-config-single.yaml \
  -n llm-router

helm upgrade --install llm-router deploy/helm/llm-router \
  -f ../llm-router-values-override.yaml \
  -n llm-router \
  --create-namespace \
  --wait --timeout=10m

# 5. Test the integration
kubectl port-forward svc/router-controller 8084:8084 -n llm-router &
curl -X POST http://localhost:8084/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"","messages":[{"role":"user","content":"Hello!"}],"nim-llm-router":{"policy":"task_router"}}'
```

### Option 2: Full Production (32 GPUs)

**Model Routing Configuration:**

| **Task Router** | **Model** | **GPUs** | **Use Case** |
|-----------------|-----------|----------|--------------|
| Brainstorming | llama-3.1-70b-instruct | 4 | Creative ideation |
| Chatbot | mixtral-8x22b-instruct | 4 | Conversational AI |
| Code Generation | llama-3.1-nemotron-70b-instruct | 4 | Programming tasks |
| Summarization | phi-3-mini-128k-instruct | 1 | Text summarization |
| Text Generation | llama-3.2-11b-vision-instruct | 2 | General text creation |
| Open QA | llama-3.1-405b-instruct | 8 | Complex questions |
| Closed QA | llama-3.1-8b-instruct | 1 | Simple Q&A |
| Classification | phi-3-mini-4k-instruct | 1 | Text classification |
| Extraction | llama-3.1-8b-instruct | 1 | Information extraction |
| Rewrite | phi-3-medium-128k-instruct | 2 | Text rewriting |

| **Complexity Router** | **Model** | **GPUs** | **Use Case** |
|----------------------|-----------|----------|--------------|
| Creativity | llama-3.1-70b-instruct | 4 | Creative tasks |
| Reasoning | llama-3.3-nemotron-super-49b | 4 | Complex reasoning |
| Contextual-Knowledge | llama-3.1-405b-instruct | 8 | Knowledge-intensive |
| Few-Shot | llama-3.1-70b-instruct | 4 | Few-shot learning |
| Domain-Knowledge | llama-3.1-nemotron-70b-instruct | 4 | Specialized domains |
| No-Label-Reason | llama-3.1-8b-instruct | 1 | Simple reasoning |
| Constraint | phi-3-medium-128k-instruct | 2 | Constrained tasks |

**Total: 32 GPUs across 10 different models + 1 GPU for Router Server = 33 GPUs**

> **💡 Customization Note:** These model assignments can be changed to suit your specific needs. You can modify the `router-config.yaml` file to:
> - Assign different models to different tasks
> - Add or remove routing categories
> - Adjust GPU allocation based on your hardware
> - Use different model variants or sizes
> 
> The routing configuration is fully customizable based on your use case and available resources.

```bash
# 1. Deploy Dynamo Cloud Operator
kubectl apply -f https://github.com/ai-dynamo/dynamo/releases/latest/download/dynamo-operator.yaml

# 2. Deploy full LLM cluster via Dynamo
kubectl create namespace dynamo
kubectl apply -f dynamo-llm-config.yaml

# 3. Clone LLM Router and deploy with Helm
git clone https://github.com/NVIDIA-AI-Blueprints/llm-router.git
cd llm-router

# 4. Create ConfigMap and deploy router
kubectl create configmap router-config \
  --from-file=config.yaml=../router-config.yaml \
  -n llm-router

helm upgrade --install llm-router deploy/helm/llm-router \
  -f ../llm-router-values-override.yaml \
  -n llm-router \
  --create-namespace \
  --wait --timeout=10m

# 5. Test the integration
kubectl port-forward svc/router-controller 8084:8084 -n llm-router &
curl -X POST http://localhost:8084/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"","messages":[{"role":"user","content":"Write a Python function"}],"nim-llm-router":{"policy":"task_router"}}'
```

**All configuration files are provided in this directory - no manual file creation needed!**

## Prerequisites

- **Kubernetes cluster** (1.20+) with kubectl configured
- **Helm 3.x** for managing deployments
- **Dynamo Cloud Operator** access and credentials
- **NVIDIA GPU nodes** (with GPU Operator installed) 
- **NVIDIA API keys** for model access through Dynamo cloud

## Step 1: Deploy NVIDIA Dynamo using Cloud Operator

### 1.1 Deploy Dynamo Cloud Operator

Deploy Dynamo using the official cloud operator for production-ready, scalable infrastructure:

```bash
# Install Dynamo Cloud Operator
kubectl apply -f https://github.com/ai-dynamo/dynamo/releases/latest/download/dynamo-operator.yaml

# Verify operator installation
kubectl get pods -n dynamo-system
```

### 1.2 Deploy LLMs via Dynamo Cloud

Choose from the provided configuration files based on your GPU availability:

```bash
# For full production deployment (32 GPUs) - use provided file:
kubectl apply -f dynamo-llm-config.yaml

# OR for minimal testing (1 GPU) - use provided file:
kubectl apply -f dynamo-single-llm-config.yaml
```

**🖥️ GPU Requirements Summary:**
- **Full Configuration**: 32 GPUs for models + 1 GPU for Router Server = **33 GPUs total**
- **Minimal Configuration**: 1 GPU for model + 1 GPU for Router Server = **2 GPUs total**
- **Router Server**: Always requires 1 GPU for routing decisions and model orchestration
- **Recommended for Production**: All models for comprehensive routing

### 1.3 Configuration Options

**Configuration Comparison:**

| Configuration | GPUs | Models | Use Case | File |
|--------------|------|--------|----------|------|
| **Minimal** | 2 (1 model + 1 router) | 1 model | Development, Testing, Verification | `dynamo-single-llm-config.yaml` |
| **Full** | 33 (32 models + 1 router) | 10 comprehensive models | Enterprise production, Maximum routing intelligence | `dynamo-llm-config.yaml` |

Both configuration files are provided in this repository - no manual creation needed!

### 1.4 Verify Dynamo Cloud Deployment

```bash
# Check Dynamo cluster status
kubectl get dynamoclusters -n dynamo

# Verify all models are deployed and ready
kubectl get pods -n dynamo -l app=dynamo-model

# Check model endpoints
kubectl get svc -n dynamo

# The LLM Router will connect to models through:
# http://llm-cluster.dynamo.svc.cluster.local:8080
```

## Step 2: Deploy LLM Router with Official Helm Chart

### 2.1 Download LLM Router

```bash
# Clone the official LLM Router repository
git clone https://github.com/NVIDIA-AI-Blueprints/llm-router.git
cd llm-router
```

### 2.2 Use Provided Helm Values Override

The repository includes a pre-configured Helm values override file (`llm-router-values-override.yaml`) that configures the LLM Router to work with Dynamo. This file includes:

- Router Controller and Server configuration
- Resource allocation (CPU, memory, GPU)
- Security contexts and service accounts
- Monitoring configuration
- Integration with Dynamo endpoints

No additional configuration needed - the file is ready to use.

### 2.3 Use Provided Router Configuration

The repository includes pre-configured router configuration files:

- **`router-config-single.yaml`** - For single LLM verification (all routes point to one model)
- **`router-config.yaml`** - For full production deployment with multiple models and intelligent routing

Both files are ready to use - no manual creation needed!

### 2.4 Deploy LLM Router with Helm

```bash
# For full production deployment:
kubectl create configmap router-config \
  --from-file=config.yaml=router-config.yaml \
  -n llm-router

# For single LLM verification:
kubectl create configmap router-config \
  --from-file=config.yaml=router-config-single.yaml \
  -n llm-router

# Deploy LLM Router using Helm with the provided values override
helm upgrade --install llm-router deploy/helm/llm-router \
  -f ../llm-router-values-override.yaml \
  -n llm-router \
  --create-namespace \
  --wait --timeout=10m

# Verify deployment
kubectl get pods -n llm-router
kubectl get svc -n llm-router
```

## Step 3: Verification and Testing

### 3.1 Verify Dynamo LLM Endpoints

```bash
# Check Dynamo cluster status
kubectl get dynamoclusters -n dynamo

# Verify all models are deployed and ready
kubectl get pods -n dynamo -l app=dynamo-model

# Test direct LLM endpoint
kubectl port-forward svc/llm-cluster 8080:8080 -n dynamo &

# Test the LLM endpoint (in another terminal)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-8b-instruct",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "max_tokens": 100
  }'
```

### 3.2 Test LLM Router Integration

```bash
# Port forward LLM Router controller
kubectl port-forward svc/router-controller 8084:8084 -n llm-router &

# Test task-based routing
curl -X 'POST' \
  'http://localhost:8084/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "",
    "messages": [
      {
        "role": "user",
        "content": "Write a Python function to calculate factorial"
      }
    ],
    "max_tokens": 512,
    "stream": false,
    "nim-llm-router": {
      "policy": "task_router",
      "routing_strategy": "triton",
      "model": ""
    }
  }'

# Test complexity-based routing
curl -X 'POST' \
  'http://localhost:8084/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "",
    "messages": [
      {
        "role": "user",
        "content": "Explain quantum computing in simple terms"
      }
    ],
    "max_tokens": 512,
    "stream": false,
    "nim-llm-router": {
      "policy": "complexity_router",
      "routing_strategy": "triton",
      "model": ""
    }
  }'
```

### 3.3 Single LLM Verification Setup

For testing with a minimal setup, use the provided configuration files:

```bash
# Deploy single LLM using provided configuration
kubectl apply -f dynamo-single-llm-config.yaml

# Use the provided single LLM router configuration
kubectl create configmap router-config \
  --from-file=config.yaml=router-config-single.yaml \
  -n llm-router \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart router pods to pick up new configuration
kubectl rollout restart deployment/router-controller -n llm-router
```

The provided `router-config-single.yaml` file configures all routing policies to point to the single LLM, making it perfect for verification that the routing mechanism works correctly.

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check GPU node availability and resource requests
2. **Service communication**: Verify service discovery and DNS resolution
3. **Model loading**: Verify NVIDIA API connectivity and quotas

### Debugging Commands

```bash
# Check pod logs
kubectl logs -f deployment/router-controller -n llm-router
kubectl logs -f deployment/router-server -n llm-router
kubectl logs -f deployment/dynamo-orchestrator -n dynamo

# Check events
kubectl get events -n llm-router --sort-by=.metadata.creationTimestamp
kubectl get events -n dynamo --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top pods -n llm-router
kubectl top pods -n dynamo

# Debug networking
kubectl exec -it deployment/router-controller -n llm-router -- nslookup router-server
```

## Cleanup

To remove the deployment:

```bash
# Remove LLM Router
helm uninstall llm-router -n llm-router
kubectl delete namespace llm-router

# Remove Dynamo LLMs
kubectl delete dynamoclusters --all -n dynamo
kubectl delete namespace dynamo

# Remove Dynamo Operator (optional)
kubectl delete -f https://github.com/ai-dynamo/dynamo/releases/latest/download/dynamo-operator.yaml
```

## Files in This Directory

- **`README.md`** - This comprehensive deployment guide
- **`llm-router-values-override.yaml`** - Helm values override for LLM Router
- **`router-config-single.yaml`** - Router configuration for single LLM verification (1 GPU)
- **`router-config.yaml`** - Router configuration for full production deployment (32 GPUs)
- **`dynamo-single-llm-config.yaml`** - Minimal Dynamo configuration for testing (1 GPU)
- **`dynamo-llm-config.yaml`** - Full Dynamo configuration for production (32 GPUs)

## Resources

- [LLM Router GitHub Repository](https://github.com/NVIDIA-AI-Blueprints/llm-router)
- [LLM Router Helm Chart](https://github.com/NVIDIA-AI-Blueprints/llm-router/tree/main/deploy/helm/llm-router)
- [NVIDIA Dynamo Cloud Deployment](https://github.com/ai-dynamo/dynamo/tree/main/deploy/cloud)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html) 