# Dynamo Examples, Tutorials and Deployment guides

## 🚧 Work in Progress

This repository is still a work in progress. More comprehensive examples and documentation can be found at the main examples repository: [https://github.com/ai-dynamo/dynamo/tree/main/examples](https://github.com/ai-dynamo/dynamo/tree/main/examples)

## About Dynamo

Dynamo is an AI inference platform designed for high-performance, scalable deployment of machine learning models. These examples demonstrate various deployment patterns, from simple single-node setups to complex multi-stage pipelines and distributed architectures.

> [!NOTE]
> ⚠️ This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.

## Directory Structure

### [`basics/`](./basics/)
Foundational examples to get started with Dynamo:

- **[`hello_world/`](./basics/hello_world/)** - Simple hello world example demonstrating basic Dynamo component structure and execution flow
- **[`hello_world_configurable/`](./basics/hello_world_configurable/)** - Configurable hello world example showing how to parameterize components and use configuration files
- **[`HelloWorld_MultiNodes/`](./basics/HelloWorld_MultiNodes/)** - Multi-node hello world example demonstrating distributed execution across multiple nodes with:
  - Component definitions in [`components/`](./basics/HelloWorld_MultiNodes/components/)
  - Configuration files in [`configs/`](./basics/HelloWorld_MultiNodes/configs/)
  - Visual diagrams in [`_img/`](./basics/HelloWorld_MultiNodes/_img/)
- **[`multistage_pipeline/`](./basics/multistage_pipeline/)** - Multi-stage pipeline example showcasing complex data processing workflows with:
  - Modular components in [`components/`](./basics/multistage_pipeline/components/)
  - Environment-specific configs in [`configs/`](./basics/multistage_pipeline/configs/)
  - Pipeline graphs in [`graphs/`](./basics/multistage_pipeline/graphs/)
- **[`simple_pipeline/`](./basics/simple_pipeline/)** - Streamlined pipeline example for understanding core pipeline concepts

### [`customizations/`](./customizations/)
Advanced examples showing custom implementation patterns:
- Custom component development
- Extending Dynamo functionality
- Integration patterns with existing systems

### [`deployments/`](./deployments/)
Production deployment examples and configurations:
- Cloud deployment strategies
- Container orchestration setups
- Scaling and monitoring configurations

### [`llm/`](./llm/)
Large Language Model examples and configurations:
- Model serving patterns
- Inference optimization techniques
- Multi-model deployment strategies

### [`LLM/`](./LLM/)
Specialized LLM implementations:
- **[`SNSvLLM_Disagg_SingleNode/`](./LLM/SNSvLLM_Disagg_SingleNode/)** - SNS vLLM disaggregated single node example with visual documentation in [`images/`](./LLM/SNSvLLM_Disagg_SingleNode/images/)

## Getting Started

1. **Start with Basics**: Begin with the [`hello_world`](./basics/hello_world/) example to understand core concepts
2. **Explore Configurations**: Try the [`hello_world_configurable`](./basics/hello_world_configurable/) to learn about parameterization
3. **Scale Up**: Move to [`HelloWorld_MultiNodes`](./basics/HelloWorld_MultiNodes/) for distributed scenarios
4. **Build Pipelines**: Experiment with [`simple_pipeline`](./basics/simple_pipeline/) and [`multistage_pipeline`](./basics/multistage_pipeline/) examples

## Additional Resources

- **Main Examples Repository**: [https://github.com/ai-dynamo/dynamo/tree/main/examples](https://github.com/ai-dynamo/dynamo/tree/main/examples) - Comprehensive collection of production-ready examples
- **Documentation**: [https://github.com/ai-dynamo/dynamo/tree/main/docs](https://github.com/ai-dynamo/dynamo/tree/main/docs) - Full documentation and guides
- **SDK Documentation**: [https://github.com/ai-dynamo/dynamo/tree/main/deploy/sdk/docs](https://github.com/ai-dynamo/dynamo/tree/main/deploy/sdk/docs) - SDK reference and CLI guides

## Support

For questions, issues, or contributions, please visit the main [Dynamo repository](https://github.com/ai-dynamo/dynamo) and check the existing issues or create a new one.
