# Dynamo Deployment of Disagg vLLM Example on AWS ECS
## 1. ECS Cluster Setup 
1. Go to AWS ECS console, **Clusters** tab and click on **Create cluster**
2. Input the cluster name and choose **AWS EC2** as the infrastructure. This option will create a cluster with EC2 instances to deploy containers
3. Click on **Create** and a cluster will be deployed through cloudformation.
## 2. Task Definations Setup