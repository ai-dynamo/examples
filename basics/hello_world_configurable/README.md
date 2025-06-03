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

# Hello World Configurable Example

This example builds upon the basic [Hello World example](../hello_world/README.md) by adding configuration support. It demonstrates how to make Dynamo services configurable using YAML configuration files and the `ServiceConfig` API.

## Architecture

```
Users/Clients (HTTP)
      │
      ▼
┌────────────────┐
│    Frontend    │  HTTP API endpoint (/generate)
│ (configurable) │  Customizable greeting and timing
└────────────────┘
```

## Components

- **Frontend**: A configurable HTTP service that can be customized through configuration files
- **Config File**: YAML configuration that defines service behavior

## Configuration Options

The service supports the following configuration parameters:

- `greeting`: The greeting message (default: "Hello")
- `sleep_time`: Delay in seconds between each streamed response (default: 1)

## Getting Started

### Prerequisites

```{note}
Make sure that `etcd` and `nats` are running
```

### Running the Example

1. **With default configuration**:
```bash
cd new_examples/basics/hello_world_configurable
dynamo serve hello_world_configurable:Frontend
```

2. **With custom configuration**:
```bash
cd new_examples/basics/hello_world_configurable
dynamo serve hello_world_configurable:Frontend -f config.yaml
```

The service will start on `http://localhost:8000` by default.

### Testing the Service

Test with a simple request:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "world,universe,galaxy"}'
```

**With default configuration**, expected output:
```
Hello world!
Hello universe!
Hello galaxy!
```

**With custom configuration** (`config.yaml`), expected output:
```
Hey world!
Hey universe!
Hey galaxy!
```

## Configuration File

The included `config.yaml` demonstrates custom configuration:

```yaml
Frontend:
  greeting: "Hey"
  sleep_time: 0.5
```

## Implementation Details

The example demonstrates:

1. **Service Configuration**: Using `ServiceConfig.get_instance()` to access configuration
2. **Configuration Access**: Using `.get()` method with service name and parameter
3. **Default Values**: Providing fallback values when configuration is missing
4. **Service Initialization**: Loading configuration in the service constructor
5. **Runtime Behavior**: Using configuration values to modify service behavior

### Key Code Patterns

```python
# Load configuration in constructor
config = ServiceConfig.get_instance()
self.greeting = config.get("Frontend", {}).get("greeting", "Hello")
self.sleep_time = config.get("Frontend", {}).get("sleep_time", 1)

# Use configuration values at runtime
yield f"{self.greeting} {word}!\n"
time.sleep(self.sleep_time)
```

## Customizing Configuration

You can create your own configuration file by copying and modifying `config.yaml`:

```yaml
Frontend:
  greeting: "Welcome"
  sleep_time: 2.0
```

Then run with your custom config:
```bash
dynamo serve hello_world_configurable:Frontend -f your_config.yaml
```

## Next Steps

After understanding configurable services, explore:

```{seealso}
- [Simple Pipeline](../simple_pipeline/README.md): Connect multiple configurable services
- [Multistage Pipeline](../multistage_pipeline/README.md): Complex pipelines with multiple configuration layers
```
