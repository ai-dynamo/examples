# Dynamo Deployment of vLLM Example on AWS ECS
## 1. ECS Cluster Setup 
1. Go to AWS ECS console, **Clusters** tab and click on **Create cluster** with name `dynamo-GPU`
2. Input the cluster name and choose **AWS EC2 instances** as the infrastructure. This option will create a cluster with EC2 instances to deploy containers.
3. Choose the GPU supported AMI `Amazon Linux 2 (GPU)` 
4. Choose `g6e.2xlarge` as the **EC2 instance type** and add an `SSH Key pair` so you can log in the instance for debugging purpose.
5. Set **Root EBS volume size** as `200`
6. For the networking, use the default settings. Make sure the **security group** has 
- an inbound rule which allows "All traffic" from this security group. 
- an inbound rule for port 22 and 8000, so that you can ssh into the instance for debugging purpose
7. Select `Turn on` for **Auto-assign public IP** option.
8. Click on **Create** and a cluster will be deployed through cloudformation.
## 2. Task Definitions Setup
We will create 3 tasks for the vLLM example. A sample task definition JSON is attached.
1. ETCD and Nats Task
This task will create etcd and nats containers on a CPU cluster. You can reuse the task from the AWS_ECS_HelloWorld example

2. Dynamo vLLM Frontend Task
This task will create vLLM frontend, processors, routers and a decode worker.
Please follow steps below to create this task
- Set container name as `dynamo-frontend` and use prebuild [Dynamo container](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-dynamo/containers/vllm-runtime).
- Choose `Amazon EC2 instances` as the **Launch type** with **Task size** `2 vCPU` and `40 GB`memory
- Choose `host` as the Network mode. 
- Container name use `dynamo-vLLM-frontend`
- Add your Image URL (You can use the prebuild [Dynamo container](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/ai-dynamo/containers/vllm-runtime)) and **Yes** for Essential container. It can be AWS ECR URL or Nvidia NGC URL. If using NGC URL, please also choose **Private registry authentication** and add your Secret Manager ARN or name. 
- Container port  

|Container port|Protocol|Port name| App protocol|
|-|-|-|-|
|8000|TCP|8000|HTTP|
- Use `1` GPU for **Resource allocation limits**
- Environment variables settings as below. Will override the `IP_ADDRESS` later.

|Key|Value type|Value|
|-|-|-|
|ETCD_ENDPOINTS|Value|http://IP_ADDRESS:2379|
|NATS_SERVER|Value|http://IP_ADDRESS:4222|
- Docker configuration  
Add `sh,-c` in **Entry point** and `cd examples/llm && uv run dynamo serve graphs.agg_router:Frontend -f configs/disagg_router.yaml` in **Command**

3. Dynamo vLLM PrefillWorker Task
Create the PrefillWorker task same as the frontend worker, except for following changes
- Set container name as `dynamo-prefill`
- No container port mapping
- Docker configuration with command `cd examples/llm && uv run dynamo serve components.prefill_worker:PrefillWorker -f configs/disagg_router.yaml`

## 3. Task Deployment
You can create a service or directly run the task from the task definition
1. ETCD/NATS Task
- Choose the Fargate cluster for **Existing cluster** created in the hello world example.
- Wait for this deployment to finish, and get the **Private IP** of this task. 
2. Dynamo Frontend Task
- Choose the EC2 cluster for **Existing cluster** created in step 1.
- In the **Container Overrides**, use the IP for ETCD/NATS task for the `ETCD_ENDPOINTS` and `NATS_SERVER` values.
3. Dynamo PrefillWorker Task
- Choose the EC2 cluster for **Existing cluster** created in step 1.
- In the **Container Overrides**, use the IP for ETCD/NATS task for the `ETCD_ENDPOINTS` and `NATS_SERVER` values.

## 4. Testing
Find the public IP of the dynamo frontend task from the task page. Run following commands to query the endpoint.
```sh
export DYNAMO_IP_ADDRESS=TASK_PUBLIC_IP_ADDRESS
curl http://$DYNAMO_IP_ADDRESS:8000/v1/models
curl $DYNAMO_IP_ADDRESS:8000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
    {
        "role": "user",
        "content": "In the heart of Eldoria, an ancient land of boundless magic and mysterious creatures, lies the long-forgotten city of Aeloria. Once a beacon of knowledge and power, Aeloria was buried beneath the shifting sands of time, lost to the world for centuries. You are an intrepid explorer, known for your unparalleled curiosity and courage, who has stumbled upon an ancient map hinting at ests that Aeloria holds a secret so profound that it has the potential to reshape the very fabric of reality. Your journey will take you through treacherous deserts, enchanted forests, and across perilous mountain ranges. Your Task: Character Background: Develop a detailed background for your character. Describe their motivations for seeking out Aeloria, their skills and weaknesses, and any personal connections to the ancient city or its legends. Are they driven by a quest for knowledge, a search for lost familt clue is hidden."
    }
    ],
    "stream":false,
    "max_tokens": 30
  }'
```
You should be able to see the name of the model and responses from it.