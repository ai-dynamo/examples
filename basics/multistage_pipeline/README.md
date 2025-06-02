<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Multi-Stage Pipeline Example

This example demonstrates a multi-stage text processing pipeline that combines the simplicity of the simple_pipeline example with the distributed architecture of the disagg_skeleton example.

## Architecture

```
Users/Clients (HTTP)
      │
      ▼
┌─────────────┐
│  Frontend   │  HTTP API endpoint (/generate)
└─────────────┘
      │
      ▼
┌─────────────┐
│   Middle    │  Processing layer (queries router for best worker)
└─────────────┘
      │    ↑
      │    │ return worker_id
      ↓    │
┌─────────────┐
│   Router    │  Routes based on strategy (hash, load)
└─────────────┘

┌─────────────┐              ┌─────────────┐
│  Backend    │    push      │    Queue    │
│  Workers    │─────────────►│   (NATS)    │
└─────────────┘              └─────────────┘
                                    ▲
                                    │ pull
                              ┌─────────────┐
                              │Queue Worker │
                              └─────────────┘
```

## Components

- **Frontend**: HTTP API that receives text processing requests
- **Middle**: Processing layer that validates requests and queries the router
- **Router**: Intelligent routing service that selects the best worker
- **Backend**: Worker instances that process text and can queue tasks
- **QueueWorker**: Optional worker that pulls and processes tasks from queue

## Features

- **Streaming responses**: Results stream back through the pipeline
- **Smart routing**: Router can use hash-based or load-based algorithms
- **Queue integration**: Uses `NatsQueue` from `dynamo._core` for reliable task queuing
- **Configurable behavior**: Different configs for different greetings and settings

## Prerequisites

1. Start NATS service (required for queue functionality):
```bash
docker run -d --name nats -p 4222:4222 nats:latest
```

2. Set environment variable:
```bash
export NATS_SERVER="nats://localhost:4222"
```

## Running the Example

### Basic deployment (without queue worker):

1. Start the main pipeline with "Hello" configuration:
```bash
cd dynamo/new_examples/basics/multistage_pipeline
dynamo serve graphs.multistage:Frontend --config configs/hello.yaml
```

2. In another terminal, start backend workers:
```bash
cd dynamo/new_examples/basics/multistage_pipeline
dynamo serve components.backend:Backend --config configs/hello.yaml
```

3. Test the pipeline:
```bash
# Simple request
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "world,universe,galaxy"}'

# Request with ID
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "sun,moon,stars", "request_id": "astronomy-123"}'
```

### Full deployment (with queue worker):

1. Start the queue worker in addition to the above:
```bash
cd dynamo/new_examples/basics/multistage_pipeline
dynamo serve components.backend:QueueWorker --config configs/hello.yaml
```

2. Test with longer text (will be queued):
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a much longer text with more than ten words that will trigger queue processing"}'
```

### Using different configurations:

Try the "Goodbye" configuration for different behavior:
```bash
dynamo serve graphs.multistage:Frontend --config configs/goodbye.yaml
```

## Configuration Options

### Middle component:
- `routing_mode`: "smart" (uses router), "random", or "round_robin"
- `greeting`: Default greeting to use
- `min_workers`: Minimum backend workers required

### Router component:
- `algorithm`: "hash" (sticky sessions) or "load" (least loaded)

### Backend component:
- `sleep_time`: Processing delay per word
- `queue_enabled`: Whether to use queue
- `queue_threshold`: Word count threshold for queuing

## Implementation Notes

- The queue implementation uses `NatsQueue` from `dynamo._core` for reliable message queuing
- The `TextProcessingQueue` wrapper provides a singleton pattern with context manager support
- Linter warnings about imports may appear due to dynamic path resolution at runtime

## Observing Behavior

1. **Routing**: With hash-based routing, similar text will go to the same worker
2. **Queue**: Check logs to see when tasks are queued and processed
3. **Load distribution**: Multiple workers share the processing load

## Scaling

You can start multiple backend workers on different nodes:
```bash
# Node 1
export NATS_SERVER="nats://node1:4222"
dynamo serve components.backend:Backend --config configs/hello.yaml

# Node 2
export NATS_SERVER="nats://node1:4222"
dynamo serve components.backend:Backend --config configs/hello.yaml
```
