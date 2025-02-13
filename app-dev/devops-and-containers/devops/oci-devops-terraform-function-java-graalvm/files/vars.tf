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
variable docker_user { 
    description = "Your docker user to login OCIR to create the initial Function image"
}
variable docker_pwd { 
    description = "Your docker password (auth token) to login OCIR to create the initial Function image"
}
variable initial_image { 
    default = "docker.io/mikarinneoracle/hello-world-java-graalvm"
    description = "Intial native X86 Hello-world public image that is used to deploy the initial OCI Function"
}