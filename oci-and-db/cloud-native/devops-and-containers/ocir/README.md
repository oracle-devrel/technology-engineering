# Mirror images to OCIR

These scripts are supposed to be launched from the OCI Cloud Console.

The user must have the permissions to create a Container Registry repository and to push images on it.

To mirror all the images in a Helm chart repository, just type:
```bash
./mirror-helm-ocir.sh -c <helm-repo-name>/<chart-name>
```
The script will create all the required repository. But be sure to configure REMOTE_REGISTRY and COMPARTMENT_ID first directly in the script!

The same script is also available if you want to mirror explicitly some images, by running:
```bash
./mirror-ocir.sh -i image1,image2
```