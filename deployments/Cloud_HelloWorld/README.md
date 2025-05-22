# Dynamo Deployment of Hello World Example with Dynamo Cloud
1. Prepare for Dynamo Cloud Setup
# Set your container registry
```sh
export ORG="NGC_ORG"
export TEAM="NGC_TEAM"
export DOCKER_SERVER=nvcr.io/${ORG}/${TEAM}
# Set the image tag (e.g., latest, 0.0.1, etc.)
export IMAGE_TAG=v0.1.0

earthly --push +all-docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG
```
This step will build two images:
- nvcr.io/${ORG}/${TEAM}/dynamo-operator:${IMAGE_TAG}       
- nvcr.io/${ORG}/${TEAM}/dynamo-api-store:${IMAGE_TAG}
Push them into docker registry 
```sh
docker push nvcr.io/${ORG}/${TEAM}/dynamo-operator:${IMAGE_TAG}        
docker nvcr.io/${ORG}/${TEAM}/dynamo-api-store:${IMAGE_TAG}     
```
2. Deploy Dynamo Cloud
Get your docker authentication token
```sh
export DOCKER_USERNAME='$oauthtoken'
export DOCKER_PASSWORD='AUTHENTICATION_TOKEN'
export DOCKER_SERVER='nvcr.io/${ORG}/${TEAM}'
export NAMESPACE='dyanmo-cloud'

cd dynamo/deploy/cloud/helm
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE
./deploy.sh
```
You should see the dynamo cloud related pods running in your k8s cluster. 

3. Connect to Dynamo Cloud and Test
```sh
# In a separate terminal, run port-forward to expose the dynamo-store service locally
kubectl port-forward svc/dynamo-store 8000:80 -n $NAMESPACE

# Set DYNAMO_CLOUD to use the local port-forward endpoint
export DYNAMO_CLOUD=http://localhost:8000
dynamo deployment list
```

## 2. Dynamo Application Deployment
1. Build the Dynamo Base Image. For the hello world example, we can just build the leaner image without CUDA and vLLM making it suitable for CPU only deployments.
```bash
export CI_REGISTRY_IMAGE=nvcr.io/${ORG}/${TEAM}
export CI_COMMIT_SHA=hello-world

earthly +dynamo-base-docker --CI_REGISTRY_IMAGE=$CI_REGISTRY_IMAGE --CI_COMMIT_SHA=$CI_COMMIT_SHA
# Image should succesfully be built and tagged as nvcr.io/ORG/TEAM/dynamo-base-docker:hello-world
```
2. Push the built image to your docker registry and set environment variable
```bash
docker push nvcr.io/${ORG}/${TEAM}/dynamo-base-docker:hello-world
export DYNAMO_IMAGE=nvcr.io/${ORG}/${TEAM}/dynamo-base-docker:hello-world
```
3. Build the Dynamo application bundle. 
```sh
###### Build Dynamo application bundle
cd dynamo/examples/hello_world
DYNAMO_TAG=$(dynamo build hello_world:Frontend | grep "Successfully built" | awk '{ print $3 }' | sed 's/\.$//')
# Create the deployment
export DEPLOYMENT_NAME=hello-world
dynamo deployment create $DYNAMO_TAG --no-wait -n $DEPLOYMENT_NAME
```

## 3. Dynamo Cloud Deployment and test
Test the deployed example
```sh
kubectl port-forward svc/dynamo-helloworld-frontend 8000:80
curl -X 'POST' 'http://localhost:8000/generate' \
    -H 'accept: text/event-stream' \
    -H 'Content-Type: application/json' \
    -d '{"text": "dynamo_k8s_test"}'
```
and you should see the output `Frontend: Middle: Backend: dynamo_k8s_test-mid-back`
