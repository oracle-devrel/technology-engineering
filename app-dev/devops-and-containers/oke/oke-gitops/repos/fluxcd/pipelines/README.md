# Pipeline repository

The *script* folder contains all the scripts for the pipelines to run. These scripts are common for every pipeline.

- mirror_helm.yaml is a pipeline to mirror a Helm Chart and all the images defined in the Chart as default
- mirroe_images.yaml is a pipeline to mirror a list of public images into OCIR

To use these mirror pipelines, it is best to copy them, modify them, and create the build pipeline pointing to the modified
yaml with all the parameters set.