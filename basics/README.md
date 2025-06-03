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

# Dynamo Basics and Hello World Examples

This directory contains foundational Dynamo examples that demonstrate core concepts from simple single-service deployments to complex multi-stage pipelines. These examples are designed to be explored in progression, building upon concepts from previous examples.

```{toctree}
:maxdepth: 2
:caption: Examples

hello_world/README
hello_world_configurable/README
simple_pipeline/README
multistage_pipeline/README
```

## Learning Path

### 1. [Hello World](hello_world/README.md)
**Start here** - The simplest possible Dynamo service demonstrating:
- Basic service creation with `@service` decorator
- HTTP API endpoints with `@api()` decorator
- Streaming responses
- Basic logging setup

### 2. [Hello World Configurable](hello_world_configurable/README.md)
**Add configuration** - Builds on Hello World by adding:
- Configuration management with `ServiceConfig`
- YAML configuration files
- Customizable service behavior
- Default value handling

### 3. [Simple Pipeline](simple_pipeline/README.md)
**Connect services** - Demonstrates multi-service architecture:
- Service dependencies with `depends()` decorator
- Frontend-Backend architecture
- Multiple worker instances
- Routing strategies (round-robin, random)
- Two implementation approaches (basic and advanced)

### 4. [Multistage Pipeline](multistage_pipeline/README.md)
**Complex workflows** - Advanced multi-stage processing with:
- Multi-component architecture (Frontend → Middle → Router → Backend)
- Queue-based processing with NATS
- Smart routing algorithms
- Distributed worker management
- Production-ready patterns

## Quick Start

Each example can be run independently. To get started:

1. **Choose an example** based on your learning goals
2. **Navigate to the example directory**
3. **Follow the README instructions** in each example
4. **Experiment with configurations** and observe behavior changes

### Example Commands

```bash
# Start with the basics
cd hello_world
dynamo serve hello_world:Frontend

# Try configuration
cd hello_world_configurable
dynamo serve hello_world_configurable:Frontend -f config.yaml

# Explore pipelines
cd simple_pipeline
dynamo serve simple_pipeline:Frontend

# Build complex workflows
cd multistage_pipeline
dynamo serve graphs.multistage:Frontend --config configs/hello.yaml
```

## Key Concepts Covered

### Core Service Patterns
- **Single Service**: Standalone HTTP API services
- **Service Dependencies**: Connecting services with dependency injection
- **Multi-Stage Pipelines**: Complex workflows with multiple processing stages

### Configuration Management
- **Static Configuration**: YAML-based service configuration
- **Runtime Configuration**: Dynamic behavior modification
- **Environment-Specific Settings**: Different configs for different environments

### Scaling and Routing
- **Worker Scaling**: Running multiple instances of services
- **Load Distribution**: Round-robin, random, and custom routing strategies
- **Queue-Based Processing**: Asynchronous task processing with message queues

### Production Patterns
- **Streaming Responses**: Real-time data streaming
- **Error Handling**: Graceful error management
- **Logging and Observability**: Service monitoring and debugging
- **Resource Management**: Efficient resource utilization

## Testing Examples

Each example includes curl commands for testing. Basic testing pattern:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "world,universe,galaxy"}'
```

## Next Steps

After completing these basic examples, explore:

```{seealso}
- **LLM Examples**: Production LLM deployment patterns
- **Advanced Patterns**: Complex architectural patterns
- **Production Deployments**: Kubernetes and cloud deployments
```

## Prerequisites

Most examples require only:
- Dynamo framework installed
- Python 3.8+ environment

Some advanced examples may require:
- Docker (for NATS queue)
- Additional Python packages (specified in individual READMEs)

## Getting Help

```{tip}
- Check individual example READMEs for detailed instructions
- Review logs for debugging information
- Experiment with configuration changes to understand behavior
```
