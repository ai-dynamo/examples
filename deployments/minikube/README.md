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

# clone Dynamo GitHub repo
git clone https://github.com/ai-dynamo/dynamo.git

# go to root of Dynamo repo
cd dynamo
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
# Start Minikube cluster with GPUs, NOTE: Potentially add --force flag to force minikube to use all available gpus
minikube start --driver=docker --container-runtime=docker --gpus=all 

# Optional: Unmount /proc/driver/nvidia if machine has preinstalled drivers
ssh -o "StrictHostKeyChecking no" -i $(minikube ssh-key) docker@$(minikube ip) "sudo umount -R /proc/driver/nvidia"
```

---

### Accessing GPU Resources In Kubernetes

In the event that NVIDIA drivers are preinstalled on the target compute instance we'll be running Dynamo related workloads on, specifying the GPU flags in the `minikube start` command will automatically bring up NVIDIA device plugin pods. The [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) lets Kubernetes detect and allocate NVIDIA GPUs to pods, enabling GPU-accelerated workloads. Without it, Kubernetes can't schedule GPUs for containers.

Once the device plugin pods are in a running state we can proceed with running GPU workloads in the minikube cluster. Please note depending on your cluster setup, you might manually have to install the NVIDIA device plugin, or the [NVIDIA GPU Operator](https://github.com/NVIDIA/gpu-operator) which is preferred over just the NVIDIA device plugin especially for production or large-scale Kubernetes environments, as the GPU Operator automates the installation and management of GPU drivers, the device plugin, monitoring, and other GPU software on Kubernetes nodes. We can verify the device plugin pods are running by checking pod status in the `kube-system` namespace:



```bash
# check status of device plugin pod
kubectl get pods -n kube-system

# output is truncated to only show device plugin pods
NAME                                   READY   STATUS    RESTARTS      AGE
...
nvidia-device-plugin-daemonset-hvd5x   1/1     Running   0             1d
```

---

### Set Up Ingress Controller

Set up an Ingress controller to expose the Dynamo API Store service. In this case, we'll be leveraging NGINX and the Minikube addon to easily enable this ingress controller:

```bash
# enable ingress add on
minikube addons enable ingress

# verify pods are running
kubectl get pods -n ingress-nginx

# output should be similar
NAME                                        READY   STATUS      RESTARTS   AGE
ingress-nginx-admission-create-wnv5m        0/1     Completed   0          1d
ingress-nginx-admission-patch-977pp         0/1     Completed   0          1d
ingress-nginx-controller-768f948f8f-gg8vd   1/1     Running     0          1d
```

---

### Verify Default StorageClass

Ensure the cluster has access to a default storage class. Dynamo Cloud requires Persistent Volume Claim (PVC) support. Minikube should come preinstalled with a default `standard` storage class that can be leveraged for provisioning volumes:

```bash
# get storage class
kubectl get storageclass

# Output should show (default) flag next to storage class
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  1d
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

# Uncomment below and Set your Docker username and password
#export DOCKER_USERNAME=<YOUR_DOCKER_USERNAME>
#export DOCKER_PASSWORD=<YOUR_DOCKER_PASSWORD>
```

Login to your registry:

```bash
docker login ${CONTAINER_REGISTRY}
```

Build and push the API Store and Operator images:


```bash
# build API store component
cd deploy/cloud/api-store
earthly --push +docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG

# build the dynamo operator
cd ../operator
earthly --push +docker --DOCKER_SERVER=$DOCKER_SERVER --IMAGE_TAG=$IMAGE_TAG
```
---

### Deploying the Dynamo Cloud Platform

Navigate to the helm directory and set environment variables, we'll configure the namespace dynamo cloud will be deployed in:

```bash
cd ../helm
export PROJECT_ROOT=$(pwd)
export NAMESPACE=dynamo-cloud
```

Create the namespace and set it as the default cluster context:

```bash
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE
```

Run the deploy script:

```bash
# install CRDs first, then platform
./deploy.sh --crds
```

Check pod status:

```bash
# view dynamo cloud pods
kubectl get pods -n $NAMESPACE

# output should be similar
NAME                                                              READY   STATUS             RESTARTS     AGE
dynamo-cloud-dynamo-api-store-54bfd67cfd-8j5jk                    1/1     Running            0            66s
dynamo-cloud-dynamo-operator-buildkitd-0                          1/1     Running            0            66s
dynamo-cloud-dynamo-operator-controller-manager-99b6469dc-s2gh4   2/2     Running            0            66s
dynamo-cloud-etcd-0                                               1/1     Running            0            66s
dynamo-cloud-minio-5f9b646749-sk56p                               1/1     Running            0            66s
dynamo-cloud-nats-0                                               2/2     Running            0            66s
dynamo-cloud-nats-box-764fdb68f4-w42fm                            1/1     Running            0            66s
dynamo-cloud-postgresql-0                                         1/1     Running            0            66s
```

---

### Exposing the Dynamo API Store Service

We'll need to expose the Dynamo API Store service as this will serve as the entry point for configuring our inference graph. Use the following ingress configuration, which will be exposed via NGINX:

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

Set up environment for vLLM runtime image build:

```bash
export FRAMEWORK="VLLM"
export BASE_IMAGE="nvcr.io/nvidia/cuda-dl-base"
BASE_IMAGE_TAG="25.01-cuda12.8-devel-ubuntu24.04"
export BUILD_PLATFORM="linux/amd64"
```

Dry run and build the image (the build process can take up to 20-30 minutes for vLLM runtime):

```bash
./container/build.sh --framework $FRAMEWORK --base-image $BASE_IMAGE --base-image-tag $BASE_IMAGE_TAG --platform $BUILD_PLATFORM
```


---

### Pushing Dynamo Runtime Container Images to Private Registry

Export variables and push the image for optional reuse later:

```bash
export DYNAMO_IMAGE=dynamo
export DYNAMO_IMAGE_TAG=latest-vllm
export REGISTRY_DYNAMO_IMAGE_TAG=vllm-1.0.0

docker tag $DYNAMO_IMAGE:$DYNAMO_IMAGE_TAG $DOCKER_SERVER/$DYNAMO_IMAGE:$REGISTRY_DYNAMO_IMAGE_TAG
docker push $DOCKER_SERVER/$DYNAMO_IMAGE:$REGISTRY_DYNAMO_IMAGE_TAG
```

---

## Deploying Dynamo Inference Graphs to Kubernetes

Export variables and run the command to access the container shell. The image in this case should be the vLLM image that was built in the previous step

```bash
export DYNAMO_VLLM_IMAGE=<YOUR_DYNAMO_VLLM_IMAGE>
export FRAMEWORK=VLLM

./container/run.sh -it --image $DYNAMO_VLLM_IMAGE --framework $FRAMEWORK --mount-workspace
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

In a separate terminal (outside the container shell), check the builder pod and deployment status. Note it could take up to 10 minutes for the builder pod to complete its job:


```bash
kubectl get pods

# output for builder pod should be similar
NAME                                             READY  STATUS    RESTARTS   AGE
dynamo-image-builder-d14tkjnp3bks7390bab0-m449g  1/1    Running   0          11m
```

After checking the builder pod status, you can follow the build process and debug any issues by streaming the logs from the builder pod. First, get the name of the builder pod (it will look like `dynamo-image-builder-...`). Then, use the following command:

```bash
kubectl logs -f <BUILDER_POD_NAME>
```

Replace `<BUILDER_POD_NAME>` with the actual pod name from the previous `kubectl get pods` output. The `-f` flag will stream the logs in real time so you can monitor the build process and catch any errors as they happen.

If you want to see logs for a previous run (if the pod has restarted), you can add the `--previous` flag:

```bash
kubectl logs --previous <BUILDER_POD_NAME>
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
# get services running in dynamo-cloud namespace
kubectl get svc

# output should be similar
NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
....
llm-agg-frontend      ClusterIP   10.110.239.205   <none>        3000/TCP    6m44s
```

Once we've verified service details, we'll create an Ingress resource to expose the service and run inference on it. Use the following ingress configuration, which will be exposed via NGINX:

```yaml
cat <<EOF > llm_agg_frontend_ingress.yaml 
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: llm-agg-frontend-ingress
  namespace: $NAMESPACE
spec:
  ingressClassName: nginx
  rules:
  - host: dynamo-llm-agg-frontend.test
    http:
      paths:
      - backend:
          service:
            name: llm-agg-frontend
            port:
              number: 8000
        path: /
        pathType: Prefix
EOF
```

Apply the ingress resource:

```bash
kubectl apply -f llm_agg_frontend_ingress.yaml
kubectl get ingress
```

Once the ingress resource has been created, make sure to add the entry along with it's address in your `/etc/hosts` file. Look up the external IP address as reported by Minikube by running the `minikube ip` command. Once found, update the hosts file with the following line:

`<YOUR_MINIKUBE_IP> dynamo-llm-agg-frontend.test`

Once configured, we can make cURL requests to the Dynamo API endpoint:

```bash
curl http://dynamo-llm-agg-frontend.test/v1/chat/completions   -H "Content-Type: application/json"   -d '{
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

---

## Clean Up Resources

In order to clean up any Dynamo related resources, from the container shell you launched the deployment from, simply run the following command:

```bash
# delete dynamo deployment
dynamo deployment delete $DEPLOYMENT_NAME
```

This will spin down the Dynamo deployment we configured and spin down all the resources that were leveraged for the deployment. As a final cleanup step, we can also delete the ingress resource that was created to expose the service:

```bash
# delete ingress resource created for dynamo service
kubectl delete -f llm_agg_frontend_ingress.yaml
```