# First access to ArgoCD

ArgoCD has been installed in the argocd namespace of the cluster.
For the first access, you can get the admin password directly from the secret by running this command:

`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

Then, you can initially access the argocd interface by performing a port-forwarding:

`kubectl port-forward svc/argo-cd-argocd-server -n argocd 8080:443`

After running the command, you should be able to access ArgoCD UI from `localhost:8080`, enter with username **admin** and the admin password.

NOTE: If you have deployed the Helm Chart on a private OKE cluster, you will need to perform some networking setup to be able to connect through kubectl.

# Connecting to the OCI Code Repository

Under `Settings --> Repositories` click on **CONNECT REPO** and select to connect to a repository **VIA HTTPS**.
Fill the form with the following values:
1. `Repository type`: "git"
2. `Repository URL`: <oke-cluster-config clone URL>
3. `Username`: \<OCI username of a user with access to the git repository>
4. `Password`: \<Auth Token of the user>

The repository we want to connect to is the oke-cluster-config repository in OCI DevOps, already created by the Resource Manager Stack.
It's better to go into the OCI DevOps, find the repository, and find the right HTTPS clone URL.

NOTE: The username to connect to the OCI DevOps Code Repository should be `<tenancy_name>/<user_domain>/<user_name>`

# Clone the OCI Code Repository locally

It is always better to clone the Git repository locally and have an appropriate IDE where we can work. A lot of YAMLs are involved when managing a cluster,
so it's important to correctly indent the code.
Once you have cloned the **oke-cluster-config**, it's time to perform the following actions:
1. Deploy the cluster secret by running `kubectl apply -f in-cluster.yml`
2. Substitute ${REPO} with the repository https URL from OCI DevOps
3. Push the code to the remote Git repository (optional)
4. Run `kubectl apply -f root.yml`
5. You will lose the port-forwarding session if still active, but don't worry, it's something expected
6. Access to the ArgoCD UI, and be sure that `all-apps` application is synchronized

After having performed these steps, you will have an installation of ArgoCD configured with the apps-of-apps pattern.

# How to use this template

The concept is simple, there are some naming conventions that need to be known so that everything is kept in order.

## Apps folder
The apps folder will contain the applications to deploy in the cluster. When we talk about applications, we mean here **infrastructure** applications.
Infrastructure applications are usually not developed by the company IT team, and it is a best practice to separate infra application from custom business applications.
As such, infra applications are usually pre-packaged applications deployed as Helm charts. Think of an application to collect logs and send them to a backend, or a Helm chart
installing a Kafka cluster on OKE.
The same ArgoCD application is actually an infra application!
As cluster administrators, you are tasked to install and maintain these kind of applications in the cluster, so that developers can make use of them.
Apart from installing infra applications, a Kubernetes administrator should also configure the cluster and the single namespace so that everything is secured.

To keep everything in order, it is better to use some naming conventions:

```
- apps
    - <cluster-name>
        - _config_
            - <Kubernetes-object-kind>
                * <object-name>.yml
        - <namespace>
            - _config_
            - <application name>
```

The content of the application folder depends on the way the application is deployed. If there is a Helm chart available, I will only need the `values.yml` file to deploy the Helm chart.
Here is an example:
```
- argocd
    * argocd.yml
    * values.yml
```

When dealing with Helm, it's always better to keep at hand all the possible values configurable for the Helm chart. The **"all-values file"** will not be considered by ArgoCD, as we will
only specify the `values.yml` file.
You can get all the default values of a chart by running this command:
`helm show values <repo-name>/<chart-name> > all-values.yml`

Depending on your needs, you can opt to deploy applications directly using a Kubernetes manifest or Kustomize.

## AppSets folder

The `appsets` folder is structured as a Helm chart for convenience. It contains all the code necessary to instruct ArgoCD on what applications to deploy, in which cluster and namespace. All YAMLs are in the `templates` folder.
Folders are organized by namespace, so the structure needs to be something like this:
```
- templates
    - <namespace>
        * application.yml
        * <namespace>-config.yml
    * cluster-config.yml
```

**cluster-config** will point to the apps/<cluster-name>/\_config_ folder so that all the cluster-wide configurations are deployed.
<namespace>-config.yml will point to apps/<cluster-name>/namespace/\_config_ so that all namespace-wide configurations are deployed.
**application.yml** will point to apps/<cluster-name>/namespace/application/values.yml to read the values and deploy the Helm chart. You can have a look at the argocd application to understand it.

# FAQ

* I need to setup some roles cluster wide, so some ClusterRole, where should I put my manifests?
  * In apps/in-cluster/\_config_/clusterRole/<manifest>.yml

* I need to configure some ResourceQuota in the namespace `example`, where should I put the created manifest?
  * In apps/in-cluster/example/\_config_/<manifest>.yml

* I need to deploy a Helm application in a namespace called `example`, what should I do?
  * Create a value file in apps/in-cluster/example/<application>/values.yml
    * If you have troubles filling up the right values, create a yaml with all the default values with `helm show values`
  * Create a new AppSet in appsets/templates/example/<helm-application>.yml
  * Be sure that the AppSet points to the right value file created in the previous steps

