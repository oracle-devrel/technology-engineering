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
The apps folder will contain the applications to deploy in the cluster. Applications can be helm or kustomize charts. Examples are in each folder.

## AppSets folder

The `appsets` folder is structured as a Helm chart for convenience. It contains all the code necessary to instruct ArgoCD on what applications to deploy, in which cluster and namespace. All YAMLs are in the `templates` folder.
The folder in examples contains some examples using generators to deploy applications.
