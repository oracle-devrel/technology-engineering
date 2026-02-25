# OpenShift 4.20 Agent Based Day 2: Enforce FQDN Node Names (Node joins cluster with the short name instead of the FQDN)

## Background

In some Agent Based Day 2 scenarios, a new node appears with a shortname (for example `nodename`) while the initial cluster nodes are registered as FQDN (for example `nodename.yourdomain.com`).

This is not only cosmetic. It breaks node identity consistency and can trigger authorization issues such as:
- CSINode access forbidden because the node user name is FQDN but the node object name is shortname
- lease access forbidden for the same reason
- kubelet fails to register the node object if the name does not match

The goal is:
- `/etc/hostname` is FQDN
- `hostnamectl` static hostname is FQDN
- kubelet registers using the same FQDN, so CSRs contain `CN=system:node:<FQDN>`

I avoid systemd quoting issues by putting the logic into a standalone script file and keeping the unit file simple.

Important limitation:
- A MachineConfig applies only after the node is registered and the machine-config-daemon is running on it. This is why Phase 1 is a local validation on a new host before CSR approval.

---

## Prerequisites

1. Working forward and reverse DNS for the node IP
2. The node can reach the API and required services
3. SSH or console access to the new node for Phase 1
4. `oc`, `jq`, `base64` available on the admin host for Phase 2

---

## Phase 1: Local test on a new host (do not approve CSR)

### Purpose

I use this phase to validate the logic locally first:
- systemd unit parses cleanly (no unbalanced quoting)
- hostname is forced to FQDN and survives reboot
- kubelet generates CSRs that reflect the FQDN identity

This does not require any MachineConfig rollout yet.

### Step 1: Boot a new node normally

Boot the new node with your standard Agent Based Day 2 ISO.
Do not approve the CSR yet.

### Step 2: Create script, unit, and kubelet drop-in on the node

Run this on the new node (console):

```bash
sudo tee /usr/local/sbin/set-static-fqdn.sh >/dev/null <<'EOF'
#!/usr/bin/bash
set -euo pipefail

# 1) Wenn transient bereits ein FQDN ist, nimm ihn (bei dir ist das oft der Fall)
TRANSIENT=$(hostnamectl status 2>/dev/null | awk -F': ' '/Transient hostname:/{print $2}' | head -n1 || true)
TRANSIENT=${TRANSIENT%.}

# 2) Fallback: Reverse Lookup über die primäre IPv4
IFACE=$(ip -o -4 route show default | awk '{print $5; exit}')
IP=$(ip -o -4 addr show dev "${IFACE}" | awk '{print $4}' | cut -d/ -f1 | head -n1)

FQDN=""
if [[ "${TRANSIENT}" == *.* ]]; then
  FQDN="${TRANSIENT}"
else
  for i in $(seq 1 30); do
    FQDN=$(getent hosts "${IP}" | awk '{for(i=2;i<=NF;i++) if($i ~ /\./){print $i; exit}}' | head -n1 || true)
    FQDN=${FQDN%.}
    [[ "${FQDN}" == *.* ]] && break
    sleep 1
  done
fi

# 3) Niemals hart failen (sonst blockierst du kubelet). Wenn kein FQDN, bleib konsistent.
if [[ "${FQDN}" == *.* ]]; then
  /usr/bin/hostnamectl set-hostname "${FQDN}"
  printf "%s\n" "${FQDN}" > /etc/hostname
  printf "KUBELET_NODE_NAME=%s\n" "${FQDN}" > /run/kubelet-fqdn.env
else
  SHORT=$(hostname -s)
  printf "KUBELET_NODE_NAME=%s\n" "${SHORT}" > /run/kubelet-fqdn.env
fi
EOF

sudo chmod 0755 /usr/local/sbin/set-static-fqdn.sh

sudo tee /etc/systemd/system/set-static-fqdn.service >/dev/null <<'EOF'
[Unit]
Description=Force static hostname to FQDN before kubelet
Wants=NetworkManager-wait-online.service
After=NetworkManager-wait-online.service
Before=kubelet.service

[Service]
Type=oneshot
TimeoutStartSec=60
ExecStart=/usr/local/sbin/set-static-fqdn.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /etc/systemd/system/kubelet.service.d
sudo tee /etc/systemd/system/kubelet.service.d/10-static-fqdn.conf >/dev/null <<'EOF'
[Unit]
Wants=set-static-fqdn.service
After=set-static-fqdn.service

[Service]
EnvironmentFile=/run/kubelet-fqdn.env
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now set-static-fqdn.service
sudo systemctl restart kubelet
```

### Step 3: Verify locally on the node
```bash
sudo systemd-analyze verify /etc/systemd/system/set-static-fqdn.service || true

cat /etc/hostname
hostnamectl

cat /run/kubelet-fqdn.env || true
journalctl -u kubelet --no-pager -n 50 | egrep -i "Attempting to register node|Unable to register node" || true

Step 4: Reboot validation
sudo systemctl reboot


After reboot:

cat /etc/hostname
hostnamectl

Step 5: Verify CSR subject on the admin host (still do not approve)
oc get csr --sort-by=.metadata.creationTimestamp | tail -n 20

CSR=<dein-csr>
oc get csr "$CSR" -o jsonpath='{.spec.request}' | base64 -d | openssl req -noout -subject
```

### Expected:

Subject contains CN=system:node:<FQDN>

If Phase 1 behaves correctly, Phase 2 is safe to implement as a MachineConfig.

## Phase 2: Roll out as MachineConfig (automatic for every node)
Purpose

I provide two MachineConfigs:

Worker role
Master role

This makes the behavior automatic for every node covered by those pools.

### Step 1: Generate the content and base64 encode (admin host)
```bash
mkdir -p mc-fqdn-fix && cd mc-fqdn-fix

cat > set-static-fqdn.sh <<'EOF'
#!/usr/bin/bash
set -euo pipefail

TRANSIENT=$(hostnamectl status 2>/dev/null | awk -F': ' '/Transient hostname:/{print $2}' | head -n1 || true)
TRANSIENT=${TRANSIENT%.}

IFACE=$(ip -o -4 route show default | awk '{print $5; exit}')
IP=$(ip -o -4 addr show dev "${IFACE}" | awk '{print $4}' | cut -d/ -f1 | head -n1)

FQDN=""
if [[ "${TRANSIENT}" == *.* ]]; then
  FQDN="${TRANSIENT}"
else
  for i in $(seq 1 30); do
    FQDN=$(getent hosts "${IP}" | awk '{for(i=2;i<=NF;i++) if($i ~ /\./){print $i; exit}}' | head -n1 || true)
    FQDN=${FQDN%.}
    [[ "${FQDN}" == *.* ]] && break
    sleep 1
  done
fi

if [[ "${FQDN}" == *.* ]]; then
  /usr/bin/hostnamectl set-hostname "${FQDN}"
  printf "%s\n" "${FQDN}" > /etc/hostname
  printf "KUBELET_NODE_NAME=%s\n" "${FQDN}" > /run/kubelet-fqdn.env
else
  SHORT=$(hostname -s)
  printf "KUBELET_NODE_NAME=%s\n" "${SHORT}" > /run/kubelet-fqdn.env
fi
EOF

cat > set-static-fqdn.service <<'EOF'
[Unit]
Description=Force static hostname to FQDN before kubelet
Wants=NetworkManager-wait-online.service
After=NetworkManager-wait-online.service
Before=kubelet.service

[Service]
Type=oneshot
TimeoutStartSec=60
ExecStart=/usr/local/sbin/set-static-fqdn.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

cat > 10-static-fqdn.conf <<'EOF'
[Unit]
Wants=set-static-fqdn.service
After=set-static-fqdn.service

[Service]
EnvironmentFile=/run/kubelet-fqdn.env
EOF

B64_SCRIPT=$(base64 -w0 set-static-fqdn.sh)
B64_UNIT=$(base64 -w0 set-static-fqdn.service)
B64_DROPIN=$(base64 -w0 10-static-fqdn.conf)
```

### Step 2: Create the MachineConfigs

Create the worker MachineConfig:

```yaml
cat > 99-worker-static-fqdn-before-kubelet-v2.yaml <<EOF
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  name: 99-worker-static-fqdn-before-kubelet-v2
  labels:
    machineconfiguration.openshift.io/role: worker
spec:
  config:
    ignition:
      version: 3.4.0
    storage:
      files:
        - path: /usr/local/sbin/set-static-fqdn.sh
          mode: 493
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_SCRIPT}
        - path: /etc/systemd/system/set-static-fqdn.service
          mode: 420
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_UNIT}
        - path: /etc/systemd/system/kubelet.service.d/10-static-fqdn.conf
          mode: 420
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_DROPIN}
    systemd:
      units:
        - name: set-static-fqdn.service
          enabled: true
EOF
```
Create the master MachineConfig:

```yaml
cat > 99-master-static-fqdn-before-kubelet-v2.yaml <<EOF
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  name: 99-master-static-fqdn-before-kubelet-v2
  labels:
    machineconfiguration.openshift.io/role: master
spec:
  config:
    ignition:
      version: 3.4.0
    storage:
      files:
        - path: /usr/local/sbin/set-static-fqdn.sh
          mode: 493
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_SCRIPT}
        - path: /etc/systemd/system/set-static-fqdn.service
          mode: 420
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_UNIT}
        - path: /etc/systemd/system/kubelet.service.d/10-static-fqdn.conf
          mode: 420
          overwrite: true
          contents:
            source: data:text/plain;base64,${B64_DROPIN}
    systemd:
      units:
        - name: set-static-fqdn.service
          enabled: true
EOF
```

### Step 3: Apply and monitor rollout

```bash
oc apply -f 99-worker-static-fqdn-before-kubelet-v2.yaml
oc apply -f 99-master-static-fqdn-before-kubelet-v2.yaml

oc get mcp
oc describe mcp worker | egrep -i 'Updated|Updating|Degraded|MachineConfig|Message' || true
oc describe mcp master | egrep -i 'Updated|Updating|Degraded|MachineConfig|Message' || true
```

### Step 4: Verify on a node after rollout

On a worker:

```bash
sudo systemd-analyze verify /etc/systemd/system/set-static-fqdn.service || true
systemctl status set-static-fqdn.service --no-pager
cat /etc/hostname
hostnamectl
cat /run/kubelet-fqdn.env || true
```

### Step 5: Validate the behavior for new Day 2 nodes

If these MachineConfigs are present before a new node joins, the CSR should already be created with the correct FQDN CN.