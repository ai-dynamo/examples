# Dynamo Deployment of Hello World Example with NVCF 
## 1. Dynamo Application Image 
1. Build the Dynamo Base Image. For the hello world example, we can just build the leaner image without CUDA and vLLM making it suitable for CPU only deployments.
```bash
export CI_REGISTRY_IMAGE=nvcr.io/ORG/TEAM
export CI_COMMIT_SHA=hello-world

earthly +dynamo-base-docker --CI_REGISTRY_IMAGE=$CI_REGISTRY_IMAGE --CI_COMMIT_SHA=$CI_COMMIT_SHA
# Image should succesfully be built and tagged as nvcr.io/ORG/TEAM/dynamo-base-docker:hello-world
```
2. Push the built image to your docker registry and set environment variable
```bash
docker push nvcr.io/ORG/TEAM/dynamo-base-docker:hello-world
export DYNAMO_IMAGE=nvcr.io/ORG/TEAM/dynamo-base-docker:hello-world
```
3. Build the Dynamo Application Image
```
cd dynamo/examples/hello_world
DOCKER_BUILDKIT=0 dynamo build hello_world:Frontend --containerize
```
You should get an image named `frontend:DYNAMO_TAG`, where `DYANMO_TAG` is a 16 character long string. 

4. Get pipeline values from the application image.
```
dynamo get frontend:DYNAMO_TAG > pipeline-values.yaml
```

5. Push the application image to your docker registry
```
docker tag frontend:DYNAMO_TAG nvcr.io/ORG/TEAM/dynamo-application:hello-world
docker push nvcr.io/ORG/TEAM/dynamo-application:hello-world
```
## 2. Helm Chart update
1. The `pipeline-values.yaml` can be used as a reference for your `values.yaml` files.
2. In this example, 3 pods, `frontend`,`middle` and `backend` will be deployed together with `nats` and `etcd` services. 
3. Update the `image:"nvcr.io/ORG/TEAM/dynamo-application:hello-world"` in the `values.yaml` with the Dynamo Application Image you built.
4. Update the `AUTHENTICATION_TOKEN` with your docker registry token
5. Update the version `DYNAMO_TAG` with real tag (Optional)
6. Now test the helm chart in local k8s environment.
```
helm install dynamo-hello-world chart/
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
    --helm-chart-service dynamo-helloworld-frontend \
    --inference-url "/generate" \
    --inference-port 80 \
    --health-protocol "HTTP" \ 
    --health-uri "/health" \
    --health-port 80 

```
4. Deploy NVCF Function. Detailed instructions [here](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/function-deployment.html)
```sh
ngc cloud-function function deploy create \
    $FUNCTION_ID:$FUNCTION_VERSION_ID \
    --targeted-deployment-specification \
    $DEPLOYMENT_SPECIFICATIONS 
```