variable region { default = "eu-frankfurt-1" }
variable registry { default = "fra.ocir.io" }
variable compartment_ocid { }
variable project_name { 
    default = "helloworldai-java-project"
    description = "Name of the OCI DevOps project and related resources"
}
variable image_name { 
    default = "helloworldai-java"
    description = "Name of the Docker image in OCIR. Important! Create/Push this into the OCIR repo for this before running this Stack, otherwise the stack will fail due to empty image in the function definition You can do this in OCI Cloud Shell using hello-world image from Docker Hub and then tagging and pushing it accordingly."
}