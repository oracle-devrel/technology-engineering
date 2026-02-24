#!/bin/bash
# Copyright (c) 2025 Oracle and/or its affiliates.

# This script creates a mapping of node displayname (normally an OCI-style name
# for OKE nodes) to an alias used by Kubernetes.
#
# Use whenever PyTorch's c10d cannot resolve hostnames with:
#
#   ./utils/host_list.sh >> mpi.yaml
#   kubectl apply -f mpi.yaml

echo "  HOST_LIST: |"
kubectl get nodes -o custom-columns=HOSTNAME:.status.addresses[0].address,NODE:.metadata.labels.displayName --no-headers|sed 's/^/    /'
