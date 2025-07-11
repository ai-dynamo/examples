# Dynamo Deployment of Hello World Example on AWS ECS
## 1. ECS Cluster Setup 
1. Go to AWS ECS console, **Clusters** tab and click on **Create cluster**
2. Input the cluster name and choose **AWS Fargate** as the infrastructure. This option will create a serverless cluster to deploy containers
3. Click on **Create** and a cluster will be deployed through cloudformation.
## 2. Task Definitions Setup
We need to start 3 containers for the hello world example. A sample task definition JSON is attached.
1. ETCD container
- Container name use `etcd`
- Image URL is `bitnami/etcd` and **Yes** for Essential container
- Container port  

|Container port|Protocol|Port name| App protocol|
|-|-|-|-|
|2379|TCP|2379|HTTP|
|2380|TCP|2379|HTTP|
- Environment variable key is `ALLOW_NONE_AUTHENTICATION` and value is `YES`
2. NATS container
- Container name use `nats`
- Image URL is `nats` and **Yes** for Essential container
- Container port  

|Container port|Protocol|Port name| App protocol|
|-|-|-|-|
|4222|TCP|4222|HTTP|
|6222|TCP|6222|HTTP|
|8222|TCP|8222|HTTP|
- Docker configuration, add `-js, --trace` in **Command**

3. Dynamo hello world pipeline container
- Container name use `dynamo-hello-world-pipeline`
- Add your Image URL (You can use the prebuild [Dynamo container](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-dynamo/containers/vllm-runtime)) and **Yes** for Essential container. It can be AWS ECR URL or Nvidia NGC URL. If using NGC URL, please also choose **Private registry authentication** and add your Secreate Manager ARN or name. 
- Container port  

|Container port|Protocol|Port name| App protocol|
|-|-|-|-|
|8000|TCP|8000|HTTP|

- Environment variables

|Key|Value type|Value|
|-|-|-|
|ETCD_ENDPOINTS|Value|http://localhost:2379|
|NATS_SERVER|Value|http://localhost:4222|
- Docker configuration  
Add `sh,-c` in **Entry point** and `cd examples/hello_world && uv run dynamo serve hello_world:Frontend` in **Command**

## 3. Task Deployment
You can create a service or directly run the task from the task definition
1. Environment setup
- Choose the Fargate cluster for **Existing cluster** created in step 1.
2. Networking setup
- Make sure you security group has inbound rule for port 22 and 8000, so that you can ssh into the instance for debugging purpose
- Turn on **public IP**

## 4. Testing
Find the public IP of the task from the task page. Run following commands to query the endpoint.
```sh
export DYNAMO_IP_ADDRESS=TASK_PUBLIC_IP_ADDRESS
curl -X 'POST' 'http://$DYNAMO_IP_ADDRESS:8000/generate' \
    -H 'accept: text/event-stream' \
    -H 'Content-Type: application/json' \
    -d '{"text": "test"}'
```
You should be able to see following output `Frontend: Middle: Backend: test-mid-back`.
