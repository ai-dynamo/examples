# Dynamo Deployment of Hello World Example with Helm Chart
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

## 3. Helm Deployment and test
1. Now deploy the helm chart in local k8s environment.
```sh
helm install dynamo-hello-world chart/
```
2. Test the deployed example
```sh
kubectl port-forward svc/dynamo-helloworld-frontend 8000:80
curl -X 'POST' 'http://localhost:8000/generate' \
    -H 'accept: text/event-stream' \
    -H 'Content-Type: application/json' \
    -d '{"text": "dynamo_k8s_test"}'
```
and you should see the output `Frontend: Middle: Backend: dynamo_k8s_test-mid-back`
