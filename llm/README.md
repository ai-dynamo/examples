# LLM and Multi-Modal Examples 

## Preliminary

```bash
git clone https://github.com/ai-dynamo/dynamo.git
cd dynamo
```

## About Mermaid chart

In this repo, we make use of Mermaid charts. For the colors, we use pink to indicate that we are physically within the boundary of a node and yellow to design the boundaries of a worker (worker belongs to a node and multiple workers can be within a node).

## HF model pre-download

If the compute nodes don't have internet access and/or you don't want to re-download the model every time within the containers, you should download the HF model locally.

```bash
export HF_HOME = <your_local_HF_folder>
huggingface-cli login
huggingface-cli download <model_id>
```

Then once you are at the step to run the Dynamo container, add as argument --hf-cache

```bash
./container/run.sh -it  --hf-cache <your_local_HF_folder>
```

This applies to all `container run` command in the repository.
