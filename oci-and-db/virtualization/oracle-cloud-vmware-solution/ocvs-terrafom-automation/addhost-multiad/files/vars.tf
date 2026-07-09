variable region {default = "your_region"}
variable SDDC_Cluster_OCID {default = "OCID of your Cluster (not SDDC)"}
variable ESXi_hostname {default = "ESXi-hostname"}
variable shape {default = "BM.DenseIO.E4.128"}  # possible: "BM.DenseIO.E4.128" or "BM.DenseIO2.52"
variable OCPU_count {default = 32}  # For AMD only, possible: 32, 64 or 128

# You need to specify the full name of your AD!!
# so for example "EU-FRANKFURT-1-AD-3" it NOT correct, it need to look like "ABCd:EU-FRANKFURT-1-AD-3"
# You can run the below command from the OCI CLI or cloud shell to see your AD names:
# oci iam availability-domain list
variable AD {default = "your_full-region-and-AD-name"}
