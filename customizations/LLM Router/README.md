# LLM Router with NVIDIA Dynamo Cloud Platform - Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying [NVIDIA LLM Router](https://github.com/NVIDIA-AI-Blueprints/llm-router) with the official [NVIDIA Dynamo Cloud Platform](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_cloud.html) on Kubernetes.

## NVIDIA LLM Router and Dynamo Integration

### Overview

This integration combines two powerful NVIDIA technologies to create an intelligent, scalable LLM serving platform:

1. **NVIDIA Dynamo Cloud Platform**: Official distributed inference serving framework with disaggregated serving capabilities
2. **NVIDIA LLM Router**: Intelligent request routing based on task classification and complexity analysis

Together, they provide a complete solution for deploying multiple LLMs with automatic routing based on request characteristics, maximizing both performance and cost efficiency.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   LLM Router    │───▶│ Dynamo Platform │
│                 │    │                 │    │                 │
│ OpenAI API      │    │ • Task Router   │    │ • Frontend      │
│ Compatible      │    │ • Complexity    │    │ • Processor     │
│                 │    │   Router        │    │ • VllmWorker    │
│                 │    │                 │    │ • PrefillWorker │
└─────────────────┘    └─────────────────┘    │ • Router        │
                                              └─────────────────┘
```

### Key Benefits

- **Intelligent Routing**: Automatically routes requests to the most appropriate model based on task type or complexity
- **Cost Optimization**: Uses smaller, faster models for simple tasks and larger models only when needed
- **High Performance**: Rust-based router with minimal latency overhead
- **Scalability**: Dynamo's disaggregated serving handles multiple models efficiently
- **OpenAI Compatibility**: Drop-in replacement for existing OpenAI API applications

### Integration Components

#### 1. NVIDIA Dynamo Cloud Platform
- **Purpose**: Distributed LLM inference serving
- **Features**: Disaggregated serving, KV cache management, multi-model support
- **Deployment**: Kubernetes-native with custom resources
- **Models Supported**: Multiple LLMs (Llama, Mixtral, Phi, Nemotron, etc.)

#### 2. NVIDIA LLM Router
- **Purpose**: Intelligent request routing and model selection
- **Features**: OpenAI API compliant, flexible policy system, configurable backends, performant routing
- **Architecture**: Rust-based controller + Triton inference server
- **Routing Policies**: Task classification (12 categories), complexity analysis (7 categories), custom policy creation
- **Customization**: Fine-tune models for domain-specific routing (e.g., banking intent classification)

#### 3. Integration Configuration
- **Router Policies**: Define routing rules for different task types
- **Model Mapping**: Map router decisions to Dynamo-served models
- **Service Discovery**: Kubernetes-native service communication
- **Security**: API key management via Kubernetes secrets

### Routing Strategies

#### Task-Based Routing
Routes requests based on the type of task being performed:

| Task Type | Target Model | Use Case |
|-----------|--------------|----------|
| Code Generation | llama-3.3-nemotron-super-49b-v1 | Programming tasks |
| Brainstorming | llama-3.1-70b-instruct | Creative ideation |
| Chatbot | mixtral-8x22b-instruct-v0.1 | Conversational AI |
| Summarization | llama-3.1-70b-instruct | Text summarization |
| Open QA | llama-3.1-70b-instruct | Complex questions |
| Closed QA | llama-3.1-70b-instruct | Simple Q&A |
| Classification | llama-3.1-8b-instruct | Text classification |
| Extraction | llama-3.1-8b-instruct | Information extraction |
| Rewrite | llama-3.1-8b-instruct | Text rewriting |
| Text Generation | mixtral-8x22b-instruct-v0.1 | General text generation |
| Other | mixtral-8x22b-instruct-v0.1 | Miscellaneous tasks |
| Unknown | llama-3.1-8b-instruct | Unclassified tasks |

#### Complexity-Based Routing
Routes requests based on the complexity of the task:

| Complexity Level | Target Model | Use Case |
|------------------|--------------|----------|
| Creativity | llama-3.1-70b-instruct | Creative tasks |
| Reasoning | llama-3.3-nemotron-super-49b-v1 | Complex reasoning |
| Contextual-Knowledge | llama-3.1-8b-instruct | Context-dependent tasks |
| Few-Shot | llama-3.1-70b-instruct | Tasks with examples |
| Domain-Knowledge | mixtral-8x22b-instruct-v0.1 | Specialized knowledge |
| No-Label-Reason | llama-3.1-8b-instruct | Unclassified complexity |
| Constraint | llama-3.1-8b-instruct | Tasks with constraints |

### Performance Benefits

1. **Reduced Latency**: Smaller models handle simple tasks faster
2. **Cost Efficiency**: Expensive large models used only when necessary
3. **Higher Throughput**: Better resource utilization across model pool
4. **Scalability**: Independent scaling of router and serving components

### API Usage Example

```bash
# Task-based routing example
curl -X POST http://llm-router.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Write a Python function to sort a list"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "task_router"
    }
  }'

# Complexity-based routing example
curl -X POST http://llm-router.local/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "",
    "messages": [{"role": "user", "content": "Explain quantum entanglement"}],
    "max_tokens": 512,
    "nim-llm-router": {
      "policy": "complexity_router"
    }
  }'
```

### How Dynamo Model Routing Works

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

## Integration Deployment Overview

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

- **dynamo-llm-deployment.yaml**: DynamoGraphDeployment for multi-LLM inference
- **router-config-dynamo.yaml**: Router policies for Dynamo integration (uses `${DYNAMO_API_BASE}` variable)
- **llm-router-values-override.yaml**: Helm values for LLM Router with Dynamo integration (defines `dynamo.api_base` variable)

## Prerequisites

Before starting the deployment, ensure you have:

- **Kubernetes cluster** (1.24+) with kubectl configured
- **Helm 3.x** for managing deployments
- **Earthly** for building Dynamo components ([Install Guide](https://earthly.dev/get-earthly))
- **NVIDIA GPU nodes** with GPU Operator installed
- **Container registry access** (NVIDIA NGC or private registry)
- **Git** for cloning repositories

### Environment Variables

You'll need to configure these environment variables before deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCKER_SERVER` | Your container registry URL | `nvcr.io/your-org` |
| `IMAGE_TAG` | Image tag to use | `latest` or `v1.0.0` |
| `DOCKER_USERNAME` | Registry username | `your-username` |
| `DOCKER_PASSWORD` | Registry password/token | `your-password` |
| `NAMESPACE` | Kubernetes namespace | `dynamo-cloud` |

### Configuration Variables

The deployment uses a configurable `api_base` variable for flexible endpoint management:

| Variable | File | Description | Default Value |
|----------|------|-------------|---------------|
| `dynamo.api_base` | `llm-router-values-override.yaml` | Dynamo LLM endpoint URL | `http://dynamo-llm-service.dynamo-cloud.svc.cluster.local:8080` |
| `${DYNAMO_API_BASE}` | `router-config-dynamo.yaml` | Template variable substituted during deployment | Derived from `dynamo.api_base` |

This approach allows you to:
- **Switch environments** by changing only the `dynamo.api_base` value
- **Override during deployment** with `--set dynamo.api_base=http://new-endpoint:8080`
- **Use different values files** for different environments (dev/staging/prod)

### Resource Requirements

**Minimum Requirements for Testing**:
- **Local Development**: 1 GPU for single model serving
- **Production Deployment**: Varies based on models and architecture choice

**Architecture Options**:

1. **Aggregated Serving** (Simplest):
   - Single worker handles both prefill and decode
   - Minimum: 1 GPU per model
   - Good for: Development, testing, small-scale deployments

2. **Disaggregated Serving** (Production):
   - Separate workers for prefill and decode
   - Allows independent scaling
   - Better resource utilization for high-throughput scenarios

**Component Resource Allocation**:
- **Frontend**: CPU-only (handles HTTP requests)
- **Processor**: CPU-only (request processing)
- **VllmWorker**: GPU required (model inference)
- **PrefillWorker**: GPU required (prefill operations)
- **Router**: CPU-only (KV-aware routing)
- **LLM Router**: 1 GPU (routing model inference)

## Deployment Guide

This guide walks you through deploying NVIDIA Dynamo and LLM Router step by step using the official deployment methods.

### Step 1: Prepare Your Environment

First, ensure you have all prerequisites:

```bash
# Install Dynamo SDK (recommended method)
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -yq python3-dev python3-pip python3-venv libucx0
python3 -m venv venv
source venv/bin/activate
pip install "ai-dynamo[all]"

# Set up required services (etcd and NATS)
git clone https://github.com/ai-dynamo/dynamo.git
cd dynamo
docker compose -f deploy/metrics/docker-compose.yml up -d
```

### Step 2: Deploy Dynamo Cloud Platform (For Kubernetes)

**For Kubernetes deployment, you must first deploy the Dynamo Cloud Platform:**

```bash
# Set environment variables for Dynamo Cloud Platform
export DOCKER_SERVER=your-registry.com
export IMAGE_TAG=latest
export NAMESPACE=dynamo-cloud
export DOCKER_USERNAME=your-username
export DOCKER_PASSWORD=your-password

# Build and push Dynamo Cloud Platform components
cd dynamo
earthly --push +all-docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG

# Create namespace and deploy the platform
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE
cd deploy/cloud/helm
./deploy.sh --crds

# Verify platform deployment
kubectl get pods -n $NAMESPACE
```

### Step 3: Deploy NVIDIA Dynamo LLM Services

**Option A: Local Development (Recommended for testing)**

```bash
# Navigate to LLM examples
cd examples/llm

# Start aggregated serving (single worker for prefill and decode)
dynamo serve graphs.agg:Frontend -f ./configs/agg.yaml

# Or start disaggregated serving (separate prefill and decode workers)
# dynamo serve graphs.disagg:Frontend -f ./configs/disagg.yaml
```

**Option B: Kubernetes Deployment**

```bash
# Set up Dynamo Cloud access
kubectl port-forward svc/dynamo-store 8080:80 -n dynamo-cloud &
export DYNAMO_CLOUD=http://localhost:8080

# Build and deploy your LLM service
cd examples/llm
DYNAMO_TAG=$(dynamo build hello_world:Frontend | grep "Successfully built" | awk '{ print $3 }' | sed 's/\.$//')
dynamo deployment create $DYNAMO_TAG -n llm-deployment

# Monitor deployment
kubectl get pods -n dynamo-cloud
```

### Step 4: Test Dynamo LLM Services

Once Dynamo is running, test the LLM services:

```bash
# Test with a sample request
curl localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "stream": false,
    "max_tokens": 30
  }' | jq

# For Kubernetes deployment, use port forwarding to access the service
kubectl port-forward svc/llm-deployment-frontend 3000:3000 -n dynamo-cloud
```

### Step 5: Set Up LLM Router API Keys

**IMPORTANT**: The router configuration uses Kubernetes secrets for API key management following the [official NVIDIA pattern](https://github.com/NVIDIA-AI-Blueprints/llm-router/blob/main/deploy/helm/llm-router/templates/router-controller-configmap.yaml).

```bash
# 1. Create the LLM Router namespace
kubectl create namespace llm-router

# 2. Create secret for Dynamo API key (if authentication is required)
# Note: For local Dynamo deployments, API keys may not be required
kubectl create secret generic dynamo-api-secret \
  --from-literal=DYNAMO_API_KEY="your-dynamo-api-key-here" \
  --namespace=llm-router

# 3. (Optional) Create image pull secret for private registries (only if using private container registry)
kubectl create secret docker-registry nvcr-secret \
  --docker-server=nvcr.io \
  --docker-username='$oauthtoken' \
  --docker-password="your-ngc-api-key-here" \
  --namespace=llm-router

# 4. Verify secrets were created
kubectl get secrets -n llm-router
```

### Step 6: Deploy LLM Router

**Note**: The NVIDIA LLM Router does not have an official Helm repository. You must clone the GitHub repository and deploy using local Helm charts.

```bash
# 1. Clone the NVIDIA LLM Router repository (required for Helm charts)
git clone https://github.com/NVIDIA-AI-Blueprints/llm-router.git
cd llm-router

# 2. Build and push LLM Router images to your registry
docker build -t your-registry.com/router-server:latest -f src/router-server/router-server.dockerfile .
docker build -t your-registry.com/router-controller:latest -f src/router-controller/router-controller.dockerfile .
docker push your-registry.com/router-server:latest
docker push your-registry.com/router-controller:latest

# 3. Create API key secret (using dummy key for Dynamo integration)
kubectl create secret generic llm-api-keys \
  --from-literal=nvidia_api_key=dummy-key-for-dynamo \
  --namespace=llm-router

# 4. Prepare router models (download from NGC)
# Follow the main project README to download models to local 'routers/' directory
# Then create PVC and upload models:

kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: router-models-pvc
  namespace: llm-router
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Gi
EOF

# Create temporary pod to upload models
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: model-uploader
  namespace: llm-router
spec:
  containers:
  - name: uploader
    image: alpine
    command: ["sleep", "3600"]
    volumeMounts:
    - name: models
      mountPath: /models
  volumes:
  - name: models
    persistentVolumeClaim:
      claimName: router-models-pvc
EOF

# Wait and copy models
kubectl wait --for=condition=ready pod/model-uploader -n llm-router --timeout=60s
kubectl cp routers/ llm-router/model-uploader:/models/
kubectl delete pod model-uploader -n llm-router

# 5. Create custom values file for Dynamo integration
cat > values.dynamo.yaml <<EOF
global:
  imageRegistry: "your-registry.com/"

routerServer:
  volumes:
    modelRepository:
      storage:
        persistentVolumeClaim:
          enabled: true
          existingClaim: "router-models-pvc"

routerController:
  config:
    policies:
      - name: "task_router"
        url: http://llm-router-router-server:8000/v2/models/task_router_ensemble/infer
        llms:
          - name: Brainstorming
            api_base: http://llm-deployment-frontend.dynamo-cloud.svc.cluster.local:3000
            api_key: ""
            model: deepseek-ai/DeepSeek-R1-Distill-Llama-8B
          - name: Chatbot
            api_base: http://llm-deployment-frontend.dynamo-cloud.svc.cluster.local:3000
            api_key: ""
            model: deepseek-ai/DeepSeek-R1-Distill-Llama-8B
EOF

# 6. Deploy LLM Router using Helm chart
cd deploy/helm/llm-router
helm upgrade --install llm-router . \
  --namespace llm-router \
  --values values.dynamo.yaml \
  --wait --timeout=10m

# 7. Verify LLM Router deployment
kubectl get pods -n llm-router
kubectl get svc -n llm-router
```

### Step 7: Configure External Access

```bash
# For development/testing, use port forwarding to access LLM Router
kubectl port-forward svc/llm-router-router-controller 8084:8084 -n llm-router

# Test the LLM Router API
curl http://localhost:8084/health
```

## Configuration

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

### API Key Management

The router configuration uses **environment variable substitution** for secure API key management, following the [official NVIDIA LLM Router pattern](https://github.com/NVIDIA-AI-Blueprints/llm-router/blob/main/deploy/helm/llm-router/templates/router-controller-configmap.yaml):

```yaml
# In router-config-dynamo.yaml
llms:
  - name: Brainstorming
    api_base: http://dynamo-llm-service.dynamo-cloud.svc.cluster.local:8080/v1
    api_key: "${DYNAMO_API_KEY}"  # Resolved from Kubernetes secret
    model: llama-3.1-70b-instruct
```

The LLM Router controller:
1. Reads `DYNAMO_API_KEY` from the Kubernetes secret
2. Replaces `${DYNAMO_API_KEY}` placeholders in the configuration
3. Uses the actual API key value for authentication with Dynamo services

**Security Note**: Never use empty strings (`""`) for API keys. Always use proper Kubernetes secrets with environment variable references.

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

All routes point to: `${DYNAMO_API_BASE}/v1` (configured via environment variable)

## Testing the Integration

Once both Dynamo and LLM Router are deployed, test the complete integration:

```bash
# Test LLM Router with task-based routing
curl -X POST http://localhost:8084/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user", 
        "content": "Write a Python function to calculate fibonacci numbers"
      }
    ],
    "model": "",
    "nim-llm-router": {
      "policy": "task_router",
      "routing_strategy": "triton",
      "model": ""
    }
  }' | jq

# Test with complexity-based routing
curl -X POST http://localhost:8084/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user", 
        "content": "Explain quantum computing in simple terms"
      }
    ],
    "model": "",
    "nim-llm-router": {
      "policy": "complexity_router",
      "routing_strategy": "triton",
      "model": ""
    }
  }' | jq

# Monitor routing decisions in LLM Router logs
kubectl logs -f deployment/llm-router-router-controller -n llm-router

# Monitor Dynamo inference logs
kubectl logs -f deployment/llm-deployment-frontend -n dynamo-cloud
```

## Configuration Validation

Before deploying, validate your configuration files:

### 1. Validate Dynamo Configuration

```bash
# For local development, test the service directly
curl http://localhost:8000/health

# For Kubernetes deployment, check service status
kubectl get pods -n dynamo-cloud
kubectl get svc -n dynamo-cloud

# Test the Dynamo API endpoint
kubectl port-forward svc/dynamo-frontend 8000:8000 -n dynamo-cloud &
curl http://localhost:8000/v1/models
```

### 2. Validate Router Configuration

```bash
# Check if environment variable substitution will work
export DYNAMO_API_BASE="http://dynamo-llm-service.dynamo-cloud.svc.cluster.local:8080"
envsubst < router-config-dynamo.yaml | kubectl apply --dry-run=client -f -
```

### 3. Validate Helm Values

```bash
# Validate the Helm values file
cd llm-router/deploy/helm/llm-router
helm template llm-router . --values ../../../../llm-router-values-override.yaml --dry-run
```

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

## Quick Configuration Checklist

Before deployment, ensure you customize these key settings:

1. **`dynamo-llm-deployment.yaml`**:
   - Update `dynamoComponent: frontend:latest` with your actual component reference
   - Adjust GPU resource requirements based on your hardware

2. **`llm-router-values-override.yaml`**:
   - Change `host: llm-router.local` to your actual domain
   - Update `api_base` URL if using external Dynamo deployment

3. **Environment Variables**:
   - Set `DOCKER_SERVER`, `IMAGE_TAG`, `NAMESPACE` before deployment
   - Create `DYNAMO_API_KEY` secret during Step 4

## Files in This Directory

- **`README.md`** - This comprehensive deployment guide
- **`dynamo-llm-deployment.yaml`** - DynamoGraphDeployment for multi-LLM inference
- **`router-config-dynamo.yaml`** - Router configuration for Dynamo integration
- **`llm-router-values-override.yaml`** - Helm values override for LLM Router with Dynamo integration

## Resources

- [NVIDIA Dynamo Cloud Platform Documentation](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_cloud.html)
- [NVIDIA Dynamo Kubernetes Operator](https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/dynamo_operator.html)
- [NVIDIA Dynamo GitHub Repository](https://github.com/ai-dynamo/dynamo)
- [LLM Router GitHub Repository](https://github.com/NVIDIA-AI-Blueprints/llm-router)
- [LLM Router Helm Chart](https://github.com/NVIDIA-AI-Blueprints/llm-router/tree/main/deploy/helm/llm-router)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html) 