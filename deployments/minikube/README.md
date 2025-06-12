# Deploying Dynamo Cloud on Kubernetes (Minikube)

This document covers the process of deploying Dynamo Cloud and running inference in a vLLM distributed runtime within a Kubernetes environment. The Dynamo Cloud Platform provides a managed deployment experience:

- Contains the infrastructure components required for the Dynamo cloud platform
- Used when deploying with the `dynamo deploy` CLI commands
- Provides a managed deployment experience

This overview covers the setup process on a Minikube instance, including:

- Deploying the Dynamo Operator & API Store, and creating Dynamo CRDs
- Building & pushing the Dynamo Container Runtime in vLLM to a private registry
- Deploying an inference graph built in vLLM Dynamo Runtime
- Running inference

---

## Prerequisites

Please refer to the general prerequisites required for running Dynamo. The cluster setup process will be covered in this document. In addition to the Dynamo prerequisites, the following are required for setting up the Minikube cluster:

- kubectl
- Helm
- Minikube

---

## Pull Dynamo GitHub

The Dynamo GitHub repository will be leveraged extensively throughout this walkthrough. Pull the repository using:

```bash

Clone Dynamo GitHub repo
git clone https://github.com/ai-dynamo/dynamo.git

Go to root of Dynamo repo
cd dynamo

Checkout to version of Dynamo this example can be run on
git checkout eec345aacb6affb167aece3c719d907be545db43
```

---

## Install Earthly

Earthly is a build automation tool designed for building containers and other artifacts in a repeatable, portable, and efficient way. Dynamo leverages Earthly for building and packaging the container images deployed in Kubernetes.

```bash
# Pull binaries and install Earthly
sudo /bin/sh -c 'wget https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -O /usr/local/bin/earthly && chmod +x /usr/local/bin/earthly && /usr/local/bin/earthly bootstrap --with-autocomplete'

Verify Earthly installation
earthly --help
```

---

## Set Up Minikube Cluster

### Start Kubernetes using Minikube

To run Minikube, you'll need:

- 2 CPUs or more
- 2GB of free memory
- 20GB of free disk space

If your machine has NVIDIA drivers, run the optional command below. Start the cluster:

```bash
#Start Minikube cluster with GPUs
minikube start --driver=docker --container-runtime=docker --gpus=all --force

#Update DNS within Docker to allow internet access
echo -e "options rotate\noptions timeout:1\nnameserver 8.8.8.8" | ssh -o "StrictHostKeyChecking no" -i $(minikube ssh-key) docker@$(minikube ip) -T "sudo tee -a /etc/resolv.conf"

# Optional: Unmount /proc/driver/nvidia if machine has preinstalled drivers
ssh -o "StrictHostKeyChecking no" -i $(minikube ssh-key) docker@$(minikube ip) "sudo umount -R /proc/driver/nvidia"
```

---

### Install GPU Operator

The NVIDIA GPU Operator is needed to run GPU-accelerated applications and microservices in Kubernetes.

```bash
# add nvidia helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia && helm repo update

# install gpu-operator (assuming drivers are already installed)
helm install --generate-name
-n gpu-operator --create-namespace
nvidia/gpu-operator
--set driver.enabled=false
--set validator.driver.env.name=DISABLE_DEV_CHAR_SYMLINK_CREATION
--set-string validator.driver.env.value=true

# if drivers are not installed and you want GPU Operator to manage them
helm install --generate-name -n gpu-operator --create-namespace nvidia/gpu-operator

# verify GPU Operator pods are running
kubectl get pods -n gpu-operator
```

---

### Set Up Ingress Controller

Set up an Ingress controller to expose the Dynamo API Store service. In this case, we'll be leveraging NGINX and the Minikube addon to easily enable this ingress controller:

```bash
# enable ingress add on
minikube addons enable ingress

# verify pods are running
kubectl get pods -n ingress-nginx
```

---

### Verify Default StorageClass

Ensure the cluster has access to a default storage class. Dynamo Cloud requires Persistent Volume Claim (PVC) support. Minikube should come preinstalled with a default `standard` storage class that can be leveraged for provisioning volumes:

```bash
# get storage class
kubectl get storageclass

# Output should show (default) flag next to storage class
```

---

## Dynamo Cloud

The Dynamo Cloud Platform consists of several key components:

- **Dynamo Operator**: Manages the lifecycle of Dynamo inference graphs.
- **API Store**: Stores and manages service configurations and metadata related to Dynamo deployments.
- **Custom Resources**: Kubernetes custom resources for defining and managing Dynamo services.

---

### Building Docker Images for Dynamo Cloud Components

Export the needed environment variables:

```bash
# Set your container registry and organization
export CONTAINER_REGISTRY=<YOUR_CONTAINER_REGISTRY>
export DOCKER_ORGANIZATION=<YOUR_DOCKER_ORGANIZATION>
export DOCKER_SERVER=${CONTAINER_REGISTRY}/${DOCKER_ORGANIZATION}

# Set the image tag (e.g., latest, 0.0.1, etc.)
export IMAGE_TAG=1.0.0

# Set your Docker password
export DOCKER_PASSWORD=<YOUR_DOCKER_PASSWORD>
```

Login to your registry:

```bash
docker login ${CONTAINER_REGISTRY}
Username: <YOUR_DOCKER_USERNAME>
Password: <YOUR_DOCKER_PASSWORD>
```

Build and push the API Store and Operator images:


```bash
# build API store component
cd deploy/cloud/api-store
earthly --push +docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG

# build the dynamo operator
cd deploy/cloud/operator
earthly --push +docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG
```
---

### Deploying the Dynamo Cloud Platform

Navigate to the helm directory and set environment variables:

```bash
cd deploy/cloud/helm

export PROJECT_ROOT=$(pwd)
export DOCKER_USERNAME=<YOUR_DOCKER_USERNAME>
export DOCKER_PASSWORD=<YOUR_DOCKER_PASSWORD>
export DOCKER_ORGANIZATION=<YOUR_DOCKER_ORGANIZATION_ID>
export DOCKER_REGISTRY=<YOUR_DOCKER_REGISTRY>
export DOCKER_SERVER=$DOCKER_REGISTRY/$DOCKER_ORGANIZATION
export IMAGE_TAG=1.0.0
export NAMESPACE=dynamo-cloud
```

Create the namespace and image pull secrets:

```bash
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE

kubectl create secret docker-registry docker-imagepullsecret \
  --docker-server=$DOCKER_SERVER \
  --docker-username=$DOCKER_USERNAME \
  --docker-password=$DOCKER_PASSWORD \
  --namespace=$NAMESPACE
```

Run the deploy script:

```bash
# run script in interactive mode to verify checks
./deploy.sh --crds --interactive

# install CRDs first, then platform
./deploy.sh --crds
```

Check pod status:

```bash
kubectl get pods -n $NAMESPACE
```

---

### Exposing the Dynamo API Store Service

We’ll need to expose the Dynamo API Store service as this will serve as the entry point for configuring our inference graph. Use the following ingress configuration, which will be exposed via NGINX:

```yaml
cat <<EOF > dynamo_cloud_ingress.yaml 
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dynamo-cloud-api-store
  namespace: $NAMESPACE
spec:
  ingressClassName: nginx
  rules:
  - host: dynamo-api-store.test
    http:
      paths:
      - backend:
          service:
            name: dynamo-cloud-dynamo-api-store
            port:
              number: 80
        path: /
        pathType: Prefix
EOF
```

Apply the ingress resource:

```bash
kubectl apply -f dynamo_cloud_ingress.yaml
kubectl get ingress
```

Make sure to add the entry along with its address in your `/etc/hosts` file. Look up the external IP address as reported by Minikube by running the `minikube ip` command. Once found, update the hosts file with the following line:

`<YOUR_MINIKUBE_IP> dynamo-api-store.test`

Test connection:

```bash
export DYNAMO_HOST=dynamo-api-store.test
curl http://${DYNAMO_HOST}/healthz
```
---

## Building Dynamo Runtime Container Image

From the root of the Dynamo repo, run the commands below to install Dynamo and dependencies:

```bash
sudo apt-get update
DEBIAN_FRONTEND=noninteractive sudo apt-get install -yq python3-dev python3-pip python3-venv libucx0
python3 -m venv venv
source venv/bin/activate
pip install ai-dynamo[all]
```

Set up environment for vLLM runtime image build:

```bash
export FRAMEWORK="VLLM"
export BASE_IMAGE="nvcr.io/nvidia/cuda-dl-base"
BASE_IMAGE_TAG="25.01-cuda12.8-devel-ubuntu24.04"
export BUILD_PLATFORM="linux/amd64"
```

Dry run and build the image (the build process can take up to 20-30 minutes for vLLM runtime):

```bash
./container/build.sh --framework $FRAMEWORK --base-image $BASE_IMAGE --base-image-tag $BASE_IMAGE_TAG --platform $BUILD_PLATFORM --dry-run

./container/build.sh --framework $FRAMEWORK --base-image $BASE_IMAGE --base-image-tag $BASE_IMAGE_TAG --platform $BUILD_PLATFORM
```


---

### Pushing Dynamo Runtime Container Images to Private Registry

Export variables and push the image:

```bash
export CONTAINER_REGISTRY=<YOUR_DOCKER_REGISTRY>
export CONTAINER_REGISTRY_ORG_ID=<YOUR_DOCKER_ORG_ID>
export DYNAMO_IMAGE=dynamo
export DYNAMO_IMAGE_TAG=latest-vllm
export REGISTRY_DYNAMO_IMAGE_TAG=vllm-1.0.0

docker tag $DYNAMO_IMAGE:$DYNAMO_IMAGE_TAG $CONTAINER_REGISTRY/$CONTAINER_REGISTRY_ORG_ID/$DYNAMO_IMAGE:$REGISTRY_DYNAMO_IMAGE_TAG
docker push $CONTAINER_REGISTRY/$CONTAINER_REGISTRY_ORG_ID/$DYNAMO_IMAGE:$REGISTRY_DYNAMO_IMAGE_TAG
```

---

## Deploying Dynamo Inference Graphs to Kubernetes

Export variables and run the container shell:

```bash
export DYNAMO_IMAGE=<YOUR_DYNAMO_VLLM_IMAGE>
export FRAMEWORK=VLLM

./container/run.sh -it --image $DYNAMO_IMAGE --framework $FRAMEWORK --mount-workspace
```

Inside the container shell, set environment variables:

```bash
export PROJECT_ROOT=$(pwd)
export KUBE_NS=<DYNAMO_CLOUD_NAMESPACE>
export DYNAMO_HOST=dynamo-api-store.test
export DYNAMO_CLOUD=http://${DYNAMO_HOST}
export DYNAMO_IMAGE=<YOUR_DYNAMO_VLLM_IMAGE>
```

Deploy the inference graph:

```bash
cd $PROJECT_ROOT/examples/llm

DYNAMO_TAG=$(dynamo build graphs.agg:Frontend | grep "Successfully built" | awk '{ print $NF }' | sed 's/.$//')
echo $DYNAMO_TAG

export DEPLOYMENT_NAME=llm-agg
dynamo deployment create $DYNAMO_TAG -n $DEPLOYMENT_NAME -f ./configs/agg.yaml
```

In a separate terminal (outside the container shell), check the builder pod and deployment status. Note it could take up to 20 minutes for the builder pod to complete its job:


```bash
kubectl get pods

# output for builder pod should be similar
NAME                                             READY  STATUS    RESTARTS   AGE
dynamo-image-builder-d14tkjnp3bks7390bab0-m449g  1/1    Running   0          11m
```

Once the build process completes you should be able to see the relevant Dynamo pods spin up:

```bash
kubectl get pods

# output should be similar
NAME                                       READY  STATUS    RESTARTS   AGE
llm-agg-frontend-789f99b54d-b4rl8          1/1    Running   0          11m
llm-agg-planner-7ffddb754c-7fz5d           1/1    Running   0          11m
llm-agg-processor-9996fbf79-9vk2f          1/1    Running   0          11m
llm-agg-vllmworker-866656b998-ztzmk        1/1    Running   0          11m
```

---

### Exposing the Frontend Service

Once all the pods are in a running state, verify the details regarding the Dynamo service that is spun up:

```bash
kubectl get svc

# output should be similar
NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
llm-agg-frontend      ClusterIP   10.110.239.205   <none>        3000/TCP    6m44s
```

Port forward the frontend service to your local host:

```bash
export DYNAMO_FRONTEND_SVC=llm-agg-frontend
kubectl port-forward svc/$DYNAMO_FRONTEND_SVC 8000:3000
```

In a seperate shell, test the API endpoint:

```bash
curl localhost:8000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
    {
        "role": "user",
        "content": "In the heart of Eldoria, an ancient land of boundless magic and mysterious creatures, lies the long-forgotten city of Aeloria. Once a beacon of knowledge and power, Aeloria was buried beneath the shifting sands of time, lost to the world for centuries. You are an intrepid explorer, known for your unparalleled curiosity and courage, who has stumbled upon an ancient map hinting at ests that Aeloria holds a secret so profound that it has the potential to reshape the very fabric of reality. Your journey will take you through treacherous deserts, enchanted forests, and across perilous mountain ranges. Your Task: Character Background: Develop a detailed background for your character. Describe their motivations for seeking out Aeloria, their skills and weaknesses, and any personal connections to the ancient city or its legends. Are they driven by a quest for knowledge, a search for lost familt clue is hidden."
    }
    ],
    "stream":false,
    "max_tokens": 100
  }'
```