ignore_defined_tags   = ["CCA_Basic_Tag.email", "Oracle_Tags.CreatedBy", "Oracle_Tags.CreatedOn"]

# not used with OCI Resource Manager
#availability_domain = "3"
#shape = "VM.Standard3.Flex"
shape = "VM.Standard.E4.Flex"

# when resources are provisioned the states must be "RUNNING"
# after successfull provisioning states can be set to "STOPPED" to save cost

# lifecycle state of Golden and Managed Instances
gi_state = "RUNNING"
mi_state = "RUNNING"
#gi_state = "STOPPED"
#mi_state = "STOPPED"

# network
vcndef = {
  name     = "VCNPatchTrain"
  cidr     = ["10.0.0.0/16","192.168.0.0/16"]
  subnets = {
    private = { name = "private", cidr = "10.0.0.0/17",   private = true }
    public  = { name = "public",  cidr = "10.0.128.0/17", private = false }
  }
}

defined_tags = {
    "ResourceControl.dns"    = "true"
    "ResourceControl.keepup" = "false"
  }
