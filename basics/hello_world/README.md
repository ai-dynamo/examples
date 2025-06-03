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

# Hello World Example

This is the simplest Dynamo example demonstrating a basic HTTP API service that streams responses. It showcases the fundamental concepts of creating a Dynamo service with HTTP endpoints.

## Architecture

```
Users/Clients (HTTP)
      │
      ▼
┌─────────────┐
│  Frontend   │  HTTP API endpoint (/generate)
└─────────────┘
```

## Components

- **Frontend**: A single HTTP service that receives text input and streams back greetings for each comma-separated word

## Implementation Details

The example demonstrates:

1. **Service Definition**: Using the `@service` decorator to create a Dynamo service
2. **HTTP API**: Using the `@api()` decorator to expose HTTP endpoints
3. **Streaming Responses**: Using FastAPI's `StreamingResponse` for real-time data streaming
4. **Logging**: Basic logging configuration with `configure_dynamo_logging`

## Getting Started

### Prerequisites

```{note}
Make sure that `etcd` and `nats` are running
```

### Running the Example

1. Start the service:
```bash
cd new_examples/basics/hello_world
dynamo serve hello_world:Frontend
```

The service will start on `http://localhost:8000` by default.

### Testing the Service

Test with a simple request:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "world,universe,galaxy"}'
```

Expected streaming output:
```
Hello world!
Hello universe!
Hello galaxy!
```

## Next Steps

After understanding this basic example, explore:

```{seealso}
- [Hello World Configurable](../hello_world_configurable/README.md): Add configuration to your services
- [Simple Pipeline](../simple_pipeline/README.md): Connect multiple services together
- [Multistage Pipeline](../multistage_pipeline/README.md): Build complex multi-stage processing pipelines
```
