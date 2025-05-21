# Dynamo Deployment of Single-Node-Sized vLLM model Disagg Serving with NVCF 
## 1. Dynamo Application Image 
1. Build the Dynamo Base Image with vLLM backend following instructions [here].(https://github.com/ai-dynamo/dynamo/blob/main/README.md#building-the-dynamo-base-image)
2. Push the built image to your docker registry and set environment variable
```bash
export DYNAMO_IMAGE=nvcr.io/ORG/TEAM/dynamo:latest-vllm
```
3. Build the Dynamo Application Image
```
cd dynamo/examples/llm
DOCKER_BUILDKIT=0 dynamo build graphs.agg:Frontend --containerize
```
You should get an image named `frontend:DYNAMO_TAG`, where `DYANMO_TAG` is a 16 character long string. 

4. Get pipeline values from the application image before pushing it to your docker registry 
```
dynamo get frontend:DYNAMO_TAG > pipeline-values.yaml
```
## 2. Helm Chart update
1. The `pipeline-values.yaml` can be used as a reference for your `values.yaml` files.
2. Update the `image:"nvcr.io/ORG/TEAM/dynamo-application:vllm-disagg"` in the `values.yaml` with the Dynamo Application Image you built.
3. Update the `AUTHENTICATION_TOKEN` with your docker registry token
4. You can test the helm chart by local deployment.
```
helm install dynamo-vllm-test chart/
```
## 3. NVCF Deployment

