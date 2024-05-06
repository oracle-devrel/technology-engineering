#!/bin/bash

# Get the API server endpoint & the CA cert from IMDS
OKE_APISERVER_ENDPOINT=$(curl -sH "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ | jq -r '.metadata."apiserver_host"')
OKE_KUBELET_CA_CERT=$(curl -sH "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ | jq -r '.metadata."cluster_ca_cert"')

# Adjust boot volume size        
sudo dd iflag=direct if=/dev/oracleoci/oraclevda of=/dev/null count=1
echo "1" | sudo tee /sys/class/block/`readlink /dev/oracleoci/oraclevda | cut -d'/' -f 2`/device/rescan
sudo /usr/libexec/oci-growfs -y

bash /etc/oke/oke-install.sh \
  --apiserver-endpoint $OKE_APISERVER_ENDPOINT \
  --kubelet-ca-cert $OKE_KUBELET_CA_CERT