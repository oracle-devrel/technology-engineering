# Deploy with Helm

## Set up Dependencies
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Fmacos%2Farm64%2Fstable%2Fbinary+download) / Kubernetes cluster created using [kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Helm](https://helm.sh/docs/intro/install/)

## Minikube Specific Configuration

Start Minikube:
```bash
minikube start --driver docker --container-runtime docker --gpus all --cpus 8
minikube addons enable nvidia-device-plugin
```
Minikube has a limitation when dealing with symbolic links - symbolic links inside a minikube pod can not be created in a mounted path from the host using `minikube mount <host_folder>:<minikube_target_path>`.

Instead, you can copy over the data using `minikube cp <Host models path> /data/nim` command from your host SSD to minikube host.
in [Values.yaml](protein-design-chart/values.yaml), we define the minikube folder path that the PV is created under.

Note, it is important to save the copied files under a [specific locations](https://minikube.sigs.k8s.io/docs/handbook/persistent_volumes/) on the minikube container to prevent data loss between reboots.

Copying over a large number of files from your host machine to the minikube container will increase its volume size. You can modify the default path (`/var/lib/docker`) of the docker data dir to be under a dedicated mounted SSD.
To do so, first stop the docker service
```bash
sudo systemctl stop docker
```
Edit (or create) `/etc/docker/daemon.json` and add a `data-root` entry:
```bash
{   .
    .
    .
    "data-root": "/path/to/new/docker/data/directory"
}
```
Copy the existing docker data to:
```bash
sudo rsync -avxP /var/lib/docker/ /path/to/new/docker/data/directory
```
Start the docker service
```bash
sudo systemctl start docker
```

## Configure Cluster & Helm Deployment
Set your NGC key as a Kubernetes secret:
```bash
kubectl create secret generic ngc-registry-secret --from-literal=NGC_REGISTRY_KEY=<YOUR_NGC_REGISTRY_KEY>
```
Set an environment varible with your desired chart name
```bash
export CHART_NAME=<your-chart-name>
```
Install Helm Chart:
```bash
cd protein-design-chart/
helm install "${CHART_NAME}" . --debug
```
Uninstall Helm Chart:
```bash
cd protein-design-chart/
helm uninstall "${CHART_NAME}"  --wait
```
Test pod GPU Access:
```bash
kubectl run gpu-test1 --image=nvidia/cuda:12.6.2-base-ubuntu22.04 --restart=Never --command -- nvidia-smi
```

Set up port forwarding to make requests from your local machine to all the 4 services:
```bash
kubectl port-forward service/"${CHART_NAME}"-protein-design-chart-alphafold2 8081:8081 & \
kubectl port-forward service/"${CHART_NAME}"-protein-design-chart-rfdiffusion 8082:8082 & \
kubectl port-forward service/"${CHART_NAME}"-protein-design-chart-proteinmpnn 8083:8083 & \
kubectl port-forward service/"${CHART_NAME}"-protein-design-chart-alphafold2multimer 8084:8084
```

## Troubleshooting and Debugging Kubernetes Pods
List all pods:
```bash
kubectl get pods
```

Display detailed information about a specific pod:
```bash
kubectl describe pod <pod_name>
```

View the logs of a pod:
```bash
kubectl logs <pod_name>
```

Open an interactive shell in a pod's container:
```bash
kubectl exec -it <alphafold2-multimer/rfdiffusion/proteinmpnn pod name> -- bash
```

## Running the Blueprint With the Helm Deployment

Note, due to the large size of the model files, a substantial `initialDelay` was set for the `livenessProbe` and  `readinessProbe` in [each deployment](./templates/). This extended delay prevents premature pod termination, allowing sufficient time for the model files to load before the probes begin their checks.
You can adjust these values once the models are downloaded and cached in the PV.

Before executing the notebook, ensure each pod's web server is actively listening and ready to handle incoming requests. Verify this by checking the [pod log output](#troubleshooting-and-debugging-kubernetes-pods). If you attempt to access a pod before it is fully operational, the port-forwarding command will terminate. In such case, you’ll need to execute `pkill -f "kubectl port-forward"` to stop any existing port-forwarding processes, then reinitiate the port-forwarding command as described [here](#configure-cluster--helm-deployment)

Run the [protein-binder-design.ipynb](../src/protein-binder-design.ipynb) notebook
