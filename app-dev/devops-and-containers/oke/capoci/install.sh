: '
Copyright (c) 2021 Oracle and/or its affiliates.

The Universal Permissive License (UPL), Version 1.0

Subject to the condition set forth below, permission is hereby granted to any
person obtaining a copy of this software, associated documentation and/or data
(collectively the "Software"), free of charge and under any and all copyright
rights in the Software, and any and all patent rights owned or freely
licensable by each licensor hereunder covering either (i) the unmodified
Software as contributed to or provided by such licensor, or (ii) the Larger
Works (as defined below), to deal in both

(a) the Software, and
(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
one is included with the Software (each a "Larger Work" to which the Software
is contributed by such licensors),

without restriction, including without limitation the rights to copy, create
derivative works of, display, perform, and distribute the Software and make,
use, sell, offer for sale, import, export, have made, and have sold the
Software and the Larger Work(s), and to sublicense the foregoing rights on
either these or other terms.

This license is subject to the following condition:
The above copyright notice and either this complete permission notice or at
a minimum a reference to the UPL must be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'

#!/bin/bash

# Be sure that the following policies are in place for the OKE instance principal:
# Allow dynamic-group <oke-dynamic-group> to manage instance-family in compartment <compartment name>
# Allow dynamic-group <oke-dynamic-group> to manage virtual-network-family in compartment <compartment name>
# Allow dynamic-group <oke-dynamic-group> to manage cluster-family in compartment <compartment name>

# Modify url to change ClusterAPI version to be installed
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.5.1/clusterctl-linux-amd64 -o clusterctl

export USE_INSTANCE_PRINCIPAL="true"
export USE_INSTANCE_PRINCIPAL_B64="$(echo -n "$USE_INSTANCE_PRINCIPAL" | base64 | tr -d '\n')"
export EXP_CLUSTER_RESOURCE_SET="true"
export EXP_MACHINE_POOL="true"
export EXP_OKE="true"

chmod +x clusterctl
./clusterctl init --infrastructure oci --wait-providers