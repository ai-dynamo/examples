<!--
SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Simple Pipeline Example

This example demonstrates a basic two-service pipeline architecture where a Frontend service communicates with Backend service(s). It showcases service dependencies, distributed processing, and different routing strategies for scaling workloads across multiple workers.

## Architecture

```
Users/Clients (HTTP)
      │
      ▼
┌─────────────┐    depends    ┌─────────────┐
│  Frontend   │──────────────►│   Backend   │
│   (HTTP)    │               │  (Workers)  │
└─────────────┘               └─────────────┘
```

## Components

- **Frontend**: HTTP API service that receives requests and forwards them to backend workers
- **Backend**: Worker service that processes text and generates streaming responses
- **Configuration**: YAML files that define service behavior and worker counts

## Examples Included

### 1. `simple_pipeline.py`
Basic pipeline with automatic dependency injection and default routing.

### 2. `routed_pipeline.py`
Advanced pipeline with configurable routing strategies and explicit client management.


## Implementation Details

### Basic Pipeline (`simple_pipeline.py`)

Demonstrates:
1. **Service Dependencies**: Using `depends(Backend)` to inject backend service
2. **Automatic Routing**: Dynamo handles routing to backend workers automatically
3. **Streaming Passthrough**: Frontend streams responses directly from backend

```{code-block} python
:caption: Dependency Injection Pattern

class Frontend:
    backend = depends(Backend)  # Dependency injection

    async def generate(self, request):
        response_generator = self.backend.generate(request.text)
        return StreamingResponse(response_generator)
```

### Routed Pipeline (`routed_pipeline.py`)

Demonstrates:
1. **Explicit Client Management**: Manual client creation for advanced routing control
2. **Routing Strategies**: Configurable round-robin or random routing
3. **Async Initialization**: Using `@async_on_start` for setup tasks

```{code-block} python
:caption: Advanced Routing Pattern

@async_on_start
async def async_init(self):
    runtime = dynamo_context["runtime"]
    backend_ns, backend_name = Backend.dynamo_address()
    self.backend_client = await runtime.namespace(backend_ns).component(backend_name).endpoint("generate").client()

async def generate(self, request):
    if self.routing_mode == "round_robin":
        response_stream = await self.backend_client.round_robin(request.text)
    elif self.routing_mode == "random":
        response_stream = await self.backend_client.random(request.text)
```

### Scaling and Load Distribution

The pipeline supports running multiple backend workers for parallel processing:

```{code-block} yaml
:caption: Scaling Configuration

Backend:
  ServiceArgs:
    workers: 4  # Run 4 backend workers
```

## Getting Started

### Prerequisites

```{note}
Make sure that `etcd` and `nats` are running
```

### Running the Basic Pipeline

1. **Start the pipeline** (this will start both Frontend and Backend services):
```bash
cd new_examples/basics/simple_pipeline
dynamo serve simple_pipeline:Frontend
```

2. **Test the service**:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "world,universe,galaxy"}'
```

Expected output:
```
Hello world!
Hello universe!
Hello galaxy!
```

### Running the Routed Pipeline

1. **Start with configuration**:
```bash
cd new_examples/basics/simple_pipeline
dynamo serve routed_pipeline:Frontend -f config.yaml
```

2. **Test the service**:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "sun,moon,stars"}'
```

Expected output (with config.yaml):
```
Goodnight sun!
Goodnight moon!
Goodnight stars!
```

## Configuration Options

The `config.yaml` file demonstrates various configuration options:

```{code-block} yaml
:caption: config.yaml

Backend:
  greeting: "Goodnight"
  sleep_time: 1
  ServiceArgs:
    workers: 2        # Run 2 backend workers

Frontend:
  routing_mode: "round_robin"  # or "random"
  ServiceArgs:
    workers: 1        # Single frontend instance
```

### Backend Configuration
- `greeting`: Custom greeting message (default: "Hello")
- `sleep_time`: Processing delay per word in seconds (default: 1)
- `workers`: Number of backend worker instances (default: 1)

### Frontend Configuration
- `routing_mode`: How to distribute requests across backend workers
  - `"round_robin"`: Distributes requests evenly across workers
  - `"random"`: Randomly selects a worker for each request

### Routing Strategies
- **Round-robin**: Ensures even distribution of load across all workers
- **Random**: Provides load balancing with some natural variance
- **Direct routing**: Can target specific workers using `backend_client.direct(request, worker_id)`

## Observing Behavior

```{tip}
1. **Check logs** to see which backend worker processes each request
2. **Multiple requests** will show load distribution across workers
3. **Configuration changes** take effect on service restart
```

## Advanced Usage

### Custom Routing Logic

You can implement custom routing by accessing the backend client directly:

```{code-block} python
:caption: Custom Routing Examples

# Target a specific worker
response = await self.backend_client.direct(request.text, worker_id="worker-1")

# Implement custom load balancing
best_worker = await self.select_best_worker()
response = await self.backend_client.direct(request.text, best_worker)
```

## Next Steps

After understanding service pipelines, explore:

```{seealso}
- [Multistage Pipeline](../multistage_pipeline/README.md): Complex multi-stage processing with queues and routing
```
