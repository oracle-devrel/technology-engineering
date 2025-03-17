#!/bin/bash

# Use this script inside a Volcano Kubernetes job.
#
# Assumes that the workers are named "mpiworker", and host management is
# enabled.  Currently only reliable for BM H100 shapes, as it uses the block
# rather than rack ID to sort hosts.
#
# This may add 5-10% performance gain by speeding up MPI operations when passed
# to `mpirun` via
#
#     ./utils/sort_hosts.sh myhosts.sorted
#     mpirun -hostfile myhosts.sorted ...

for host in ${VC_MPIWORKER_HOSTS//,/ }; do
  echo -n "$host " >> myhosts
  mpirun --allow-run-as-root \
    -mca plm_rsh_args "-p 2222" \
    --host $host -n 1 bash -c "curl -s http://169.254.169.254/opc/v1/host/| jq .rdmaTopologyData.customerLocalBlock" >> myhosts || echo "none" >> myhosts
done
python << EOF > ${1:-myhosts.sorted}
import sys

DATA="""\
$(<myhosts)
"""

switches = {}
for l in DATA.splitlines():
    host, switch = l.split()
    switches.setdefault(switch, []).append(host)

for r, hs in sorted(switches.items(), key=lambda x: len(x[1]), reverse=True):
    sys.stderr.write(f"adding switch with {len(hs)} nodes\n")
    for h in hs:
        print(h)
EOF
