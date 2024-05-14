# NVIDIA NIM inference server at scale with Oracle Container Engine for Kubernetes (OKE)

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green) [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_technology-engineering)](https://sonarcloud.io/dashboard?id=oracle-devrel_technology-engineering)

## Introduction

This repository intends to demonstrate how to deploy [NVIDIA NIM](https://developer.nvidia.com/docs/nemo-microservices/inference/overview.html) on Oracle Container Engine for Kubernetes (OKE) with TensorRT-LLM Backend and Triton Inference Server in order to serve Large Language Models (LLM's) in a Kubernetes architecture.

The model used is `Llama2-7B-chat`, running on an NVIDIA A10 Tensor Core GPU hosted on OCI. For scalability, we are hosting the model repository on a Bucket in Oracle Cloud Object Storage.

## 0. Prerequisites & Docs

### Prerequisites

* You have access to an Oracle Cloud Tenancy.
* You have access to shapes with NVIDIA GPU such as A10 GPU's (i.e VM.GPU.A10.1).
* You have a [container registry](https://docs.oracle.com/en-us/iaas/Content/Registry/home.htm).
* You have an [Auth Token](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm#Pushing_Images_Using_the_Docker_CLI) to push/pull images to/from the registry.
* Ability for your instance to authenticate via [instance principal](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm)
* You have access to **NVIDIA AI Entreprise** to pull the NIM containers.
* You are familiar with *Kubernetes* and *Helm* basic terminology.
* You have a HuggingFace account with an Access Token configured to download `Llama2-7B-chat`.

> [!IMPORTANT]
> All tests of this walkthrough have been performed with an early access version of NVIDIA NIM for LLM's with **nemollm-inference-ms:24.02.rc4**. NVIDIA NIM has for ambition to make deployment of LLM's easier compared to the previous implementation with Triton and TRT-LLM. Therefore, this walkthrough assumes you've previously completed [the deployment of Triton on an OKE cluster on OCI](https://github.com/oracle-devrel/technology-engineering/tree/main/cloud-infrastructure/ai-infra-gpu/GPU/triton-gpu-oke). This is a continuation of that guide.

### Docs

* [NVIDIA releases NIM for deploying AI models at scale](https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/)
* [Deploying Triton on OCI](https://github.com/triton-inference-server/server/tree/main/deploy/oci)
* [NIM documentation on how to use non prebuilt models](https://developer.nvidia.com/docs/nemo-microservices/inference/nmi_nonprebuilt_playbook.html)
* [NVIDIA TensorRT-LLM GitHub repository](https://github.com/NVIDIA/TensorRT-LLM)

## 1. Instance Creation

Let's spin up a GPU instance VM on OCI!

1. Start a **VM.GPU.A10.1** instance from the `Instance > Compute` menu with the [NGC image](https://docs.oracle.com/en-us/iaas/Content/Compute/References/ngcimage.htm). A boot volume of **200-250 GB** is also recommended.

2. It is recommended to update your drivers to the latest available, following the guidance from NVIDIA with the compatibility [matrix between the drivers and your CUDA version](https://docs.nvidia.com/deploy/cuda-compatibility/index.html). You can also see [this link](https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Ubuntu&target_version=20.04&target_type=deb_network) for more information.

    ```bash
    sudo apt purge nvidia* libnvidia*
    sudo apt-get install -y cuda-drivers-545
    sudo apt-get install -y nvidia-kernel-open-545
    sudo apt-get -y install cuda-toolkit-12-3
    sudo reboot
    ```

3. Make sure you have `nvidia-container-toolkit` installed. If not, install it by running:

    ```bash
    sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    ```

4. Check that your version matches with the version you need (CUDA >12.3):

    ```bash
    nvidia-smi
    /usr/local/cuda/bin/nvcc --version
    ```

5. Prepare the model registry: It's possible to use [pre-built models](https://developer.nvidia.com/docs/nemo-microservices/inference/nmi_playbook.html). However, we chose to run `Llama2-7B-chat`. At the time of writing, this choice is not available and we therefore have to [build the model repository ourselves](https://developer.nvidia.com/docs/nemo-microservices/inference/nmi_nonprebuilt_playbook.html).

6. Start by logging into the NVIDIA container registry with your username and password and pull the container:

    ```bash
    docker login nvcr.io
    docker pull nvcr.io/ohlfw0olaadg/ea-participants/nemollm-inference-ms:24.02.rc4
    ```

7. Clone the HuggingFace model

    ```bash
    # Install git-lfs
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
    sudo apt-get install git-lfs

    # clone the model from HF
    git clone https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
    ```

8. Create the model config: Copy the file [`model_config.yaml`](model_config.yaml) and create the directory to host the model store. This is where the Model Repo Generator command will store the output.

    ```bash
    mkdir model-store
    chmod -R 777 model-store
    ```

9. Run the Model Repo Generator Command

    ```bash
    docker run --rm -it --gpus all -v $(pwd)/model-store:/model-store -v $(pwd)/model_config.yaml:/model_config.yaml -v $(pwd)/Llama-2-7b-chat-hf:/engine_dir nvcr.io/ohlfw0olaadg/ea-participants/nemollm-inference-ms:24.02.rc4 bash -c "model_repo_generator llm --verbose --yaml_config_file=/model_config.yaml"
    ```

10. Export the model repository to an Oracle Cloud Object Storage Bucket

    At this stage, the model repository is located in the directory `model-store`. You can use `oci-cli` to do a bulk upload to one of your buckets in the region. Here is an example for a bucket called "NIM" where we want the model store to be uploaded in NIM/llama2-7b-hf (in case we upload different model configuration to the same bucket):

    ```bash
    cd model-store
    oci os object bulk-upload -bn NIM --src-dir . --prefix llama2-7b-hf/ --auth instance_principal
    ```

11. Submitting a request to the VM (IaaS execution)

    At this stage, the model repository is uploaded to one OCI bucket. It is a good moment to try the setup.

    > [!IMPORTANT]
    > Because the option parameter `--model-repository` is currently hardoded in the container, we cannot simply point to the Bucket when we start it. One option would be to adapt the python script within the container but we would need sudo privilege. The other would be to mount the bucket as a file system on the machine directly. We chose the second method with [rclone](https://rclone.org/). Make sure fuse3 and jq are installed on the machine. On Ubuntu you can run `sudo apt install fuse3 jq`.

    Start by gathering your Namespace, Compartment OCID and Region, either fetching them from the web console or by running the following commands from your compute instance:

    ```bash
    #NAMESPACE:
    echo namespace is : `oci os ns get --auth instance_principal | jq .data`

    #COMPARTMENT_OCID:
    echo compartment ocid is: `curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ | jq .compartmentId`

    #REGION:
    echo region is: `curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ | jq .region`

    ```

    You can now download rclone locally and mount the bucket. Make sure to adapt `##NAMESPACE##` `##COMPARTMENT_OCID##` `##REGION##` with the previous values.

    ```bash
    curl https://rclone.org/install.sh | sudo bash
    mkdir -p ~/rclone
    mkdir -p ~/test_directory/model_bucket_oci


    cat << EOF > ~/rclone/rclone.conf
    [model_bucket_oci]
    type = oracleobjectstorage
    provider = instance_principal_auth
    namespace = ##NAMESPACE##
    compartment = ##COMPARTMENT_OCID##
    region = ##REGION##

    EOF

    sudo /usr/bin/rclone mount --config=$HOME/rclone/rclone.conf --tpslimit 50 --vfs-cache-mode writes --allow-non-empty --transfers 10 --allow-other model_bucket_oci:NIM/llama2-7b-hf $HOME/test_directory/model_bucket_oci
    ```

    In another terminal window, you can check that `ls $HOME/test_directory/model_bucket_oci` returns the content of the bucket.

    Start the container passing the path to the model-store as an argument:

    ```bash
    docker run --gpus all -p9999:9999 -p9998:9998 -v  $HOME/test_directory/model_bucket_oci:/model-store nvcr.io/ohlfw0olaadg/ea-participants/nemollm-inference-ms:24.02.rc4 nemollm_inference_ms --model llama2-7b-chat --openai_port="9999" --nemo_port="9998" --num_gpus 1
    ```

    After 3 minutes, the inference server should be ready to serve. In another window you can run the following request. Note that if you want to run it from your local machine you will have to use the public IP and open the port 9999 at both the machine and subnet level:

    ```bash
    curl -X "POST" 'http://localhost:9999/v1/completions' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{ "model": "llama2-7b-chat", "prompt": "Can you briefly describe Oracle Cloud?", "max_tokens": 100, "temperature": 0.7, "n": 1, "stream": false, "stop": "string", "frequency_penalty": 0.0 }' | jq ".choices[0].text"
    ```

12. Adapt the cloud-init script

    > [!NOTE]
    > Ideally, a cleaner way of using rclone in Kubernetes would be to use the [rclone container](https://hub.docker.com/r/rclone/rclone) as a sidecar before starting the inference server. This works fine locally using docker but because it needs the `--device` option to use `fuse`, this makes it complicated to use with Kubernetes due to the lack of support for this feature (see https://github.com/kubernetes/kubernetes/issues/7890?ref=karlstoney.com, a Feature Request from 2015 still very active as of March 2024). The workaround I chose is to setup rclone as a service on the host and mount the bucket on startup.

    In [cloud-init](cloud-init), replace the value of your Namespace, Compartment OCID and Region lines 17, 18 and 19 with the values retrieved previously. You can also adapt the value of the bucket line 57. By default it is called `NIM` and has a directory called `llama2-7b-hf`.

    This cloud-init script will be uploaded on your GPU node in your OKE cluster. The first part consists in increasing the boot volume to the value set. Then, it downloads rclone, creates the correct directories and create the configuration file, the same way as we did previously on teh GPU VM. Finally, it starts rclone as a service and mounts the bucket to `/opt/mnt/model_bucket_oci`.

## 2. Deploy on OKE

Here is the target architecture at the end of the deployment:

![Architecture Diagram](architecture-diagram.png)

It is now time to bring everything together in Oracle Kubernetes Engines (OKE)!

1. Deploy an OKE Cluster

    Start by creating an OKE Cluster following [this tutorial](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingclusterusingoke_topic-Using_the_Console_to_create_a_Quick_Cluster_with_Default_Settings.htm) with slight adaptations:

    * Create 1 CPU node pool that will be used for monitoring with 1 node only (i.e VM.Standard.E4.Flex with 5 OCPU and 80GB RAM) with the default image.
    * Once your cluster is up, create another node pool with 1 GPU node (i.e VM.GPU.A10.1) with the default image coming with the GPU drivers. __*Important note*__: Make sure to increase the boot volume (350 GB) and add the previously modified [cloud-init script](cloud-init)

2. Deploy using Helm in Cloud Shell

    See [this documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellgettingstarted.htm#:~:text=Login%20to%20the%20Console.,the%20Cloud%20Shell%20was%20started.) to access Cloud Shell.

3. Adapting the variables

    You can find the Helm configuration in the folder [`oke`](oke/) where you need to adapt the [`values.yaml`](oke/values.yaml):

    Review your credentials for the [secret to pull the image](https://helm.sh/docs/howto/charts_tips_and_tricks/#creating-image-pull-secrets) in [`values.yaml`](oke/values.yaml):

    ```bash
    registry: nvcr.io
    username: $oauthtoken
    password: <YOUR_KEY_FROM_NVIDIA>
    email: someone@host.com
    ```

## 3. Deploy monitoring (Grafana & Prometheus)

The monitoring consist of Grafana and Prometheus pods. The configuration comes from [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack).

Here we add a public Load Balancer to reach the grafana dashboard from the Internet. Use username=admin and password=prom-operator to login. The *serviceMonitorSelectorNilUsesHelmValues* flag is needed so that Prometheus can find the inference server metrics in the example release deployed below.

```bash
helm install example-metrics --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false --set grafana.service.type=LoadBalancer prometheus-community/kube-prometheus-stack --debug
```

The default load balancer created comes with a fixed shape and a bandwidth of 100Mbps. You can switch to a [flexible](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingloadbalancers-subtopic.htm#contengcreatingloadbalancers_subtopic) shape and adapt the bandwidth according to your OCI limits in case the bandwidth is a bottleneck.

An example Grafana dashboard is available in [dashboard-review.json](oke/dashboard-review.json). Use the import function in Grafana to import and view this dashboard.

You can then see the Public IP of you grafana dashboard by running:

```bash
$ kubectl get svc
NAME                                       TYPE           CLUSTER-IP     EXTERNAL-IP       PORT(S)                      AGE
alertmanager-operated                      ClusterIP      None           <none>            9093/TCP,9094/TCP,9094/UDP   2m33s
example-metrics-grafana                    LoadBalancer   10.96.82.33    141.145.220.114   80:31005/TCP                 2m38s
```

## 4. Deploying the inference server

Deploy the inference server using the default configuration with the following commands.

```bash
cd <directory containing Chart.yaml>
helm install example . -f values.yaml --debug
```

Use kubectl to see the status and wait until the inference server pods are running. The first pull might take a few minutes. Once the container is created, loading the model also take a few minutes. You can monitor the pod with:

```bash
kubectl describe pods <POD_NAME>
kubectl logs <POD_NAME>
```

Once the setup is complete, your container should be running:

```bash
$ kubectl get pods
NAME                                               READY   STATUS    RESTARTS   AGE
example-triton-inference-server-5f74b55885-n6lt7   1/1     Running   0          2m21s
```

## 5. Using *Triton* Inference Server on you NIM container

Now that the inference server is running you can send HTTP or GRPC requests to it to perform inferencing. By default, the inferencing service is exposed with a LoadBalancer service type. Use the following to find the external IP for the inference server. In this case it is 34.83.9.133.

```bash
$ kubectl get services
NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                                        AGE
...
example-triton-inference-server  LoadBalancer   10.18.13.28    34.83.9.133   8000:30249/TCP,8001:30068/TCP,8002:32723/TCP   47m
```

The inference server exposes an HTTP endpoint on port 8000, and GRPC endpoint on port 8001 and a Prometheus metrics endpoint on port 8002. You can use curl to get the meta-data of the inference server from the HTTP endpoint.

```bash
curl 34.83.9.133:8000/v2
```

From your client machine, you can now send a request to the public IP on port 8000:

```bash
curl -X "POST" 'http://34.83.9.133:9999/v1/completions' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{ "model": "llama2-7b-chat", "prompt": "Can you briefly describe Oracle Cloud?", "max_tokens": 100, "temperature": 0.7, "n": 1, "stream": false, "stop": "string", "frequency_penalty": 0.0 }' | jq ".choices[0].text"
```

The output should be as follow:

```bash
"\n\nOracle Cloud is a comprehensive cloud computing platform offered by Oracle Corporation. It provides a wide range of cloud services, including Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS). Oracle Cloud offers a variety of benefits, including:\n\n1. Scalability: Oracle Cloud allows customers to scale their resources up or down as needed, providing the flexibility to handle changes in business demand."
```

## Cleaning up

Once you've finished using the inference server you should use helm to delete the deployment.

```bash
$ helm list
NAME            REVISION  UPDATED                   STATUS    CHART                          APP VERSION   NAMESPACE
example         1         Wed Feb 27 22:16:55 2019  DEPLOYED  triton-inference-server-1.0.0  1.0           default
example-metrics	1       	Tue Jan 21 12:24:07 2020	DEPLOYED	prometheus-operator-6.18.0   	 0.32.0     	 default

$ helm uninstall example --debug
$ helm uninstall example-metrics

```

For the Prometheus and Grafana services, you should [explicitly delete CRDs](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack#uninstall-helm-chart):

```bash
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com alertmanagers.monitoring.coreos.com podmonitors.monitoring.coreos.com probes.monitoring.coreos.com prometheuses.monitoring.coreos.com prometheusrules.monitoring.coreos.com servicemonitors.monitoring.coreos.com thanosrulers.monitoring.coreos.com
```

You may also want to delete the OCI bucket you created to hold the model repository.

```bash
oci os bucket delete --bucket-name NIM --empty
```

## Contributing

This project is open source.  Please submit your contributions by forking this repository and submitting a pull request!  Oracle appreciates any contributions that are made by the open source community.

## License

Copyright (c) 2022 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK.
