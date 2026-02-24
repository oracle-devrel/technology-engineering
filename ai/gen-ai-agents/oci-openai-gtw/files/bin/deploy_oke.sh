#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
. $SCRIPT_DIR/../starter.sh env -no-auto
. $BIN_DIR/build_common.sh
cd $SCRIPT_DIR/..

function wait_ingress() {
  # Wait for the ingress deployment
  echo "Waiting for Ingress Controller Pods..."
  kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=600s
  kubectl wait --namespace ingress-nginx --for=condition=Complete job/ingress-nginx-admission-patch  
}

# Call build_common to push the ${TF_VAR_prefix}-app:latest and ${TF_VAR_prefix}-ui:latest to OCIR Docker registry
ocir_docker_push

# One time configuration
if [ ! -f $KUBECONFIG ]; then
  create_kubeconfig
 
  # Check if Ingress Controller is installed
  kubectl get service ingress-nginx-controller -n ingress-nginx
  if [ "$?" != "0" ]; then
    # Deploy Latest ingress-nginx
    kubectl create clusterrolebinding starter_clst_adm --clusterrole=cluster-admin --user=$TF_VAR_current_user_ocid
    echo "OKE Deploy: Role Binding created"  
    # LATEST_INGRESS_CONTROLLER=`curl --silent "https://api.github.com/repos/kubernetes/ingress-nginx/releases/latest" | jq -r .name`
    # echo LATEST_INGRESS_CONTROLLER=$LATEST_INGRESS_CONTROLLER
    # kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/$LATEST_INGRESS_CONTROLLER/deploy/static/provider/cloud/deploy.yaml
    if [ "$TF_VAR_tls" == "new_http_01" ]; then
      helm install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx \
      --namespace ingress-nginx \
      --create-namespace \
      --set controller.enableExternalDNS=true 
      wait_ingress

      # ccm-letsencrypt-prod.yaml
      sed "s&##CERTIFICATE_EMAIL##&${TF_VAR_certificate_email}&" src/oke/tls/ccm-letsencrypt-prod.yaml > $TARGET_DIR/ccm-letsencrypt-prod.yaml
      kubectl apply -f $TARGET_DIR/ccm-letsencrypt-prod.yaml --timeout=600s
      sed "s&##CERTIFICATE_EMAIL##&${TF_VAR_certificate_email}&" src/oke/tls/ccm-letsencrypt-staging.yaml > $TARGET_DIR/ccm-letsencrypt-staging.yaml
      kubectl apply -f $TARGET_DIR/ccm-letsencrypt-staging.yaml

      # external-dns-config.yaml
      sed "s&##COMPARTMENT_OCID##&${TF_VAR_compartment_ocid}&" src/oke/tls/external-dns-config.yaml > $TARGET_DIR/external-dns-config.tmp
      sed "s&##REGION##&${TF_VAR_region}&" $TARGET_DIR/external-dns-config.tmp > $TARGET_DIR/external-dns-config.yaml
      kubectl create secret generic external-dns-config --from-file=$TARGET_DIR/external-dns-config.yaml

      # external-dns.yaml
      sed "s&##COMPARTMENT_OCID##&${TF_VAR_compartment_ocid}&" src/oke/tls/external-dns.yaml > $TARGET_DIR/external-dns.tmp
      sed "s&##REGION##&${TF_VAR_region}&" $TARGET_DIR/external-dns.tmp > $TARGET_DIR/external-dns.yaml
      kubectl apply -f $TARGET_DIR/external-dns.yaml
    else
      helm install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx \
      --namespace ingress-nginx \
      --create-namespace 
      wait_ingress
    fi
    
    # Wait for the ingress external IP
    TF_VAR_ingress_ip=""
    while [ -z $TF_VAR_ingress_ip ]; do
      echo "Waiting for Ingress IP..."
      TF_VAR_ingress_ip=`kubectl get service -n ingress-nginx ingress-nginx-controller -o jsonpath="{.status.loadBalancer.ingress[0].ip}"`
      if [ -z "$TF_VAR_ingress_ip" ]; then
        sleep 10
      fi
    done

    date
    kubectl get all -n ingress-nginx
    sleep 5
    echo "Ingress ready: $TF_VAR_ingress_ip"
  else
    echo "OKE Deploy: Skipping creation of ingress" 
  fi  
fi

# Create secrets
kubectl delete secret ${TF_VAR_prefix}-db-secret  --ignore-not-found=true
kubectl create secret generic ${TF_VAR_prefix}-db-secret --from-literal=db_user=$TF_VAR_db_user --from-literal=db_password=$TF_VAR_db_password --from-literal=db_url=$DB_URL --from-literal=jdbc_url=$JDBC_URL --from-literal=TF_VAR_compartment_ocid=$TF_VAR_compartment_ocid --from-literal=TF_VAR_nosql_endpoint=$TF_VAR_nosql_endpoint

kubectl delete secret ocirsecret  --ignore-not-found=true
if [ "$TF_VAR_auth_token" == "" ]; then
  # Create a temporary docker auth_token (valid for 1 hour)... 
  export TOKEN=`oci raw-request --region $TF_VAR_region --http-method GET --target-uri "https://${OCIR_HOST}/20180419/docker/token" | jq -r .data.token`
  echo "TOKEN=$TOKEN" | cut -c 1-50
  kubectl create secret docker-registry ocirsecret --docker-server=$OCIR_HOST --docker-username="BEARER_TOKEN" --docker-password="$TOKEN" --docker-email="$TF_VAR_email"
else
  kubectl create secret docker-registry ocirsecret --docker-server=$OCIR_HOST --docker-username="$TF_VAR_namespace/$TF_VAR_username" --docker-password="$TF_VAR_auth_token" --docker-email="$TF_VAR_email"
fi  

# Using & as separator
sed "s&##DOCKER_PREFIX##&${DOCKER_PREFIX}&" src/app/app.yaml > $TARGET_DIR/app.yaml
sed "s&##DOCKER_PREFIX##&${DOCKER_PREFIX}&" src/ui/ui.yaml > $TARGET_DIR/ui.yaml
cp src/oke/ingress-app.yaml $TARGET_DIR/ingress-app.yaml
cp src/oke/ingress-ui.yaml $TARGET_DIR/ingress-ui.yaml

# TLS - Domain Name
if [ "$TF_VAR_tls" == "new_http_01" ]; then
  sed -i "s&##DNS_NAME##&$TF_VAR_dns_name&" $TARGET_DIR/ingress-app.yaml
  sed -i "s&##DNS_NAME##&$TF_VAR_dns_name&" $TARGET_DIR/ingress-ui.yaml
fi

# If present, replace the ORDS URL
if [ "$ORDS_URL" != "" ]; then
  ORDS_HOST=`basename $(dirname $ORDS_URL)`
  sed -i "s&##ORDS_HOST##&$ORDS_HOST&" $TARGET_DIR/app.yaml
  sed -i "s&##ORDS_HOST##&$ORDS_HOST&" $TARGET_DIR/ingress-app.yaml
fi 

# delete the old pod, just to be sure a new image is pulled
kubectl delete pod ${TF_VAR_prefix}-ui --ignore-not-found=true
kubectl delete deployment ${TF_VAR_prefix}-dep --ignore-not-found=true
# Wait to be sure that the deployment is deleted before to recreate
kubectl wait --for=delete deployment/${TF_VAR_prefix}-dep --timeout=30s

# Create objects in Kubernetes
kubectl apply -f $TARGET_DIR/app.yaml
kubectl apply -f $TARGET_DIR/ui.yaml
kubectl apply -f $TARGET_DIR/ingress-app.yaml
kubectl apply -f $TARGET_DIR/ingress-ui.yaml

