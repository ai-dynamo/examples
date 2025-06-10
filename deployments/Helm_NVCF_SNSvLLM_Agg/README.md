# Dynamo Deployment of Single-Node-Sized vLLM model Agg Serving with NVCF 
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

4. Get pipeline values from the application image.
```
dynamo get frontend:DYNAMO_TAG > pipeline-values.yaml
```

5. Push the application image to your docker registry
```
docker tag frontend:DYNAMO_TAG nvcr.io/ORG/TEAM/dynamo-application:vllm-agg
docker push nvcr.io/ORG/TEAM/dynamo-application:vllm-agg
```
## 2. Helm Chart update
1. The `pipeline-values.yaml` can be used as a reference for your `values.yaml` files.
2. In this example, we removed `Processor` and `VllmWorker` services from the Helm Chart, so they will be deployed in same pods as the `Frontend` service.
3. Update the `image:"nvcr.io/ORG/TEAM/dynamo-application:vllm-agg"` in the `values.yaml` with the Dynamo Application Image you built.
4. Update the `AUTHENTICATION_TOKEN` with your docker registry token
5. Update the version `DYNAMO_TAG` with real tag (Optional)
6. Now test the helm chart in local k8s environment.
```
helm install dynamo-vllm-test chart/
```
## 3. NVCF Deployment
1. Upload the Application Image to the NGC Private Registry which has NVCF access and update `chart/values.yaml` with new image URL. 
2. Upload the Helm chart into NGC Private Registry
```
# Package the Helm Chart as dynamo-pipeline-0.1.0.tgz
helm package chart/
# Create NGC Privacy Registry for Helm Chart
ngc registry chart create TEAM/dynamo-pipeline --short-desc "NVCF Dynamo deployment"
# Upload Helm Chart to the NGC Privacy Registry
ngc registry chart push TEAM/dynamo-pipeline:0.1.0
```
3. Create NVCF Function. Detailed instructions [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/function-creation.html)
```sh
ngc cloud-function function create  \
    --name nvcf-dynamo-pipeline \
    --helm-chart TEAM/dynamo-pipeline:0.1.0 \
    --helm-chart-service dynamo-vllm-frontend \
    --inference-url "/v1/chat/completions" \
    --inference-port 80 \
    --health-protocol "HTTP" \ 
    --health-uri "/v1/health" \
    --health-port 80 

```
4. Deploy NVCF Function. Detailed instructions [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/function-deployment.html)
```sh
ngc cloud-function function deploy create \
    $FUNCTION_ID:$FUNCTION_VERSION_ID \
    --targeted-deployment-specification \
    $DEPLOYMENT_SPECIFICATIONS 
```
