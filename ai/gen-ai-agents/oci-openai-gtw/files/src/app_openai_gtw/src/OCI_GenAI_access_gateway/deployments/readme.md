## Procedure to deploy on to OCI OKE.
----

### Dynamic group and policies for repo and genertive-ai access from OKE

- Create a dynamic group adding the compute instance behind the node pool ,you may use all the instance at once or can select individual node OCIDs.

```
All {instance.compartment.id = 'OCID of the compartment'}
```

- Create a policy using the OCID of the dynamic group.

```
allow dynamic-group id <OCID of the Dynamic group> to use generative-ai-family in compartment id <OCID of the compartment>
allow dynamic-group id <OCID of the Dynamic group> to use repos in compartment id <OCID of the compartment> 
```
- If you are using more than one compartment/service (eg data-science),ensure update the polices accordingly

### Setup docker CLI

- Login to OCI OCIR

```
docker login <OCI Region>.ocir.io #Example docker login ord.ocir.io
```

### Update variables/config

- Clone the repo 

```
git clone https://github.com/jin38324/OCI_GenAI_access_gateway
```
- Update file `app/config.py` for below. 

```
AUTH_TYPE = "INSTANCE_PRINCIPAL"
REGION = "OCI REGION"
OCI_COMPARTMENT = "OCID FOR THE COMPARTMENT"
```

- Update file `app/models.yaml` with necessary compartment/s ,model reference Or data science models accordingly. 

### Build and push image 

- Build the docker images 

```
docker build -t <OCI Region>.ocir.io/<Namespace>/oci-openai-gateway:<version> . #example docker build -t ord.ocir.io/ax6ymbvwiimc/oci-openai-gateway:0.0.0 .
```

- Push the image to OCI Container registery.

```
docker push <OCI Region>.ocir.io/<Namespace>/oci-openai-gateway:<version> # Example docker push ord.ocir.io/ax6ymbvwiimc/oci-openai-gateway:0.0.6
```

### Create secret

- Connect to the OKE.
- Create a new namespace 
```
kubectl create ns <namespace name> #kubectl create ns ns-oci-openaigateway
```

- Create a secret to store the API Key.

```
kubectl create secret generic app-api-key -n <namespace name> --from-literal=DEFAULT_API_KEYS="<key>"

# kubectl create secret generic app-api-key -n ns-oci-openaigateway --from-literal=DEFAULT_API_KEYS="sk-xxx"

```


### Deploy the application 

- Edit file `deployments/oke.yaml` and update below values

```
namespace : with the namespace name created
image : absolute image path
#Any other values accordingly 
```

- Deploy the application 

```
kubectl apply -f deployments/oke.yaml -n <namespace name>
```

- Wait for the deployment to complete 

```
kubectl get all -n <namespace name >
```

- A sample view would looks like below 

```
rahul_m_r@codeeditor:OCI_GenAI_access_gateway (us-chicago-1)$ kubectl get all -n ns-oci-openaigateway
NAME                                                READY   STATUS    RESTARTS   AGE
pod/oci-openaigateway-deployment-68c8657c59-flnkn   1/1     Running   0          19s

NAME                                TYPE           CLUSTER-IP     EXTERNAL-IP       PORT(S)          AGE
service/oci-openaigateway-service   LoadBalancer   10.96.39.190   <pubIP>  8088:30956/TCP   53m

NAME                                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/oci-openaigateway-deployment   1/1     1            1           53m

NAME                                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/oci-openaigateway-deployment-65cdbf7b65   0         0         0       53m
```

- For any errors ,you may check the logs for the deployment 

```
kubectl logs deployment.apps/oci-openaigateway-deployment -n <namespace name>
```

### Validate the deployment

- Fetch the loadbalancer IP and launch and validate the application .

```
http://<LBIP>/docs or http://<LBIP>/redoc
```

### Additional references (Optional)

- Use a side car container and add OCI Object storage bucket as a store to refere model.yaml - (Blog link)[https://blogs.oracle.com/linux/post/object-storage-buckets-and-oke]
- Enable session persistance when using with OCI OKE and OCI Loadbalancer - (Blog link)[https://www.ateam-oracle.com/post/oci-load-balancer-session-persistence-know-how]