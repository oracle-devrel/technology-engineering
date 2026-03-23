#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. $SCRIPT_DIR/../starter.sh env -no-auto
. $BIN_DIR/build_common.sh
cd $PROJECT_DIR

if [ ! -f $PROJECT_DIR/src/terraform/oke.tf ]; then
  echo "oke.tf not found"
  echo "Nothing to delete. This was an existing OKE installation"
  exit
fi  

echo "OKE DESTROY"

if [ "$1" != "--auto-approve" ]; then
  error_exit "Please call this script via ./starter.sh destroy"
fi

if [ ! -f $KUBECONFIG ]; then
  create_kubeconfig
fi

# Check if OKE is still in the terraform state file
get_id_from_tfstate "OKE_OCID" "starter_oke"
if [ "$OKE_OCID" == "" ]; then
  echo "destroy_oke skipped. OKE not detected in $STATE_FILE"
  exit 0
fi 

# The goal is to destroy all LoadBalancers created by OKE in OCI before to delete OKE.
#
# Delete all ingress, services
kubectl delete ingress,services --all

# Delete the ingress controller
helm uninstall ingress-nginx --namespace ingress-nginx
# kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.4.0/deploy/static/provider/cloud/deploy.yaml

# Rename kubeconfig. Avoid to reuse if a new OKE is created for the same directory.
mv $KUBECONFIG $KUBECONFIG.${DATE_POSTFIX}