#!/bin/bash
###############################################################################
# OCI Management Agent Sidecar Entrypoint Script
# Installs, registers, and runs Management Agent with Prometheus plugin
###############################################################################

set -e

echo "=========================================="
echo "OCI Management Agent Sidecar"
echo "=========================================="
echo "Region: ${OCI_REGION}"
echo "Metrics Namespace: ${METRICS_NAMESPACE}"
echo "Prometheus Scrape Interval: ${PROMETHEUS_SCRAPE_INTERVAL}"
echo "=========================================="

# Validate required environment variables
if [ -z "$MGMT_AGENT_INSTALL_KEY" ]; then
    echo "ERROR: MGMT_AGENT_INSTALL_KEY environment variable is required"
    exit 1
fi

# Download Management Agent RPM from Pre-Authenticated Request (PAR) if not already present
# NOTE: The RPM must be pre-downloaded and uploaded to OCI Object Storage with a PAR URL
# See documentation for instructions on obtaining and uploading the Management Agent RPM
if [ ! -f "/tmp/oracle.mgmt_agent.rpm" ]; then
    echo "Downloading Management Agent from PAR..."
    echo "URL: https://frxfz3gch4zb.objectstorage.${OCI_REGION}.oci.customer-oci.com/p/yhfyLtJRVhgcLikaY2LYqvpTg6tMb6HfjrWGWl8ZtZgOBoz0SVJXXjpZzIjw2MkH/n/frxfz3gch4zb/b/Observability/o/oracle.mgmt_agent.230821.1905.Linux-x86_64.rpm"

    # Download with progress and timeout
    wget --verbose --timeout=300 --tries=3 \
        "https://frxfz3gch4zb.objectstorage.${OCI_REGION}.oci.customer-oci.com/p/yhfyLtJRVhgcLikaY2LYqvpTg6tMb6HfjrWGWl8ZtZgOBoz0SVJXXjpZzIjw2MkH/n/frxfz3gch4zb/b/Observability/o/oracle.mgmt_agent.230821.1905.Linux-x86_64.rpm" \
        -O /tmp/oracle.mgmt_agent.rpm 2>&1 | tee /tmp/download.log

    DOWNLOAD_STATUS=$?
    if [ $DOWNLOAD_STATUS -ne 0 ]; then
        echo "ERROR: Failed to download Management Agent (exit code: $DOWNLOAD_STATUS)"
        echo "Download log:"
        cat /tmp/download.log
        echo ""
        echo "Possible causes:"
        echo "  1. Network connectivity issues"
        echo "  2. Invalid PAR URL or expired PAR"
        echo "  3. Firewall blocking outbound connections"
        echo ""
        echo "IMPORTANT: You must download the Management Agent RPM and upload it to OCI Object Storage"
        echo "Then create a Pre-Authenticated Request (PAR) and update the download URL in this script."
        echo "See MANAGEMENT_AGENT_SETUP.md for detailed instructions."
        exit 1
    fi

    # Verify downloaded file
    if [ ! -s "/tmp/oracle.mgmt_agent.rpm" ]; then
        echo "ERROR: Downloaded file is empty or doesn't exist"
        ls -lh /tmp/oracle.mgmt_agent.rpm
        exit 1
    fi

    FILE_SIZE=$(stat -f%z "/tmp/oracle.mgmt_agent.rpm" 2>/dev/null || stat -c%s "/tmp/oracle.mgmt_agent.rpm" 2>/dev/null)
    echo "✓ Management Agent downloaded successfully (${FILE_SIZE} bytes)"
fi

# Extract Management Agent RPM contents if not already extracted
if [ ! -d "/opt/oracle/mgmt_agent/agent_inst" ]; then
    echo "Extracting Management Agent from RPM (bypassing systemd requirement)..."

    # Install rpm2cpio if not available
    if ! command -v rpm2cpio &> /dev/null; then
        echo "Installing rpm2cpio..."
        yum install -y rpm2cpio 2>&1 | tee /tmp/rpm2cpio-install.log
    fi

    # Create extraction directory
    mkdir -p /opt/oracle/mgmt_agent
    cd /opt/oracle/mgmt_agent

    # Extract RPM contents without running pre/post install scripts
    echo "Extracting RPM contents using rpm2cpio..."
    rpm2cpio /tmp/oracle.mgmt_agent.rpm | cpio -idmv 2>&1 | tee /tmp/rpm-extract.log
    EXTRACT_STATUS=$?

    if [ $EXTRACT_STATUS -ne 0 ]; then
        echo "ERROR: Failed to extract Management Agent RPM (exit code: $EXTRACT_STATUS)"
        echo "Extract log:"
        cat /tmp/rpm-extract.log
        exit 1
    fi

    # Move extracted files to proper location
    if [ -d "opt/oracle/mgmt_agent" ]; then
        echo "Moving extracted files to /opt/oracle/mgmt_agent..."
        cp -r opt/oracle/mgmt_agent/* /opt/oracle/mgmt_agent/
        rm -rf opt
    fi

    # Check if we got a ZIP file that needs to be extracted
    if [ -f "/opt/oracle/mgmt_agent/zip/oracle.mgmt_agent-230821.1905.linux.zip" ]; then
        echo "Found ZIP file inside RPM - extracting agent using Oracle extractor..."
        cd /opt/oracle/mgmt_agent

        # Use the Oracle-provided Java extractor (proper way to unpack agent)
        # Usage: java -jar unpack.jar <path-to>/oracle.mgmt_agent-*.zip
        java -jar zip/zip_extractor/agent-unpack-1.0.9059.jar \
            zip/oracle.mgmt_agent-230821.1905.linux.zip 2>&1 | tee /tmp/zip-extract.log
        ZIP_STATUS=$?

        if [ $ZIP_STATUS -ne 0 ]; then
            echo "ERROR: Failed to extract ZIP file (exit code: $ZIP_STATUS)"
            cat /tmp/zip-extract.log
            exit 1
        fi

        echo "✓ ZIP file extracted successfully using Oracle extractor"

        # The Java extractor creates files in zip/unpack/agent_inst/ directory
        # This is the correct structure from Oracle's agent-unpack tool
        if [ -d "/opt/oracle/mgmt_agent/zip/unpack/agent_inst" ]; then
            echo "Found extracted agent in zip/unpack/agent_inst/"
            echo "Moving agent files to /opt/oracle/mgmt_agent/agent_inst..."

            # Copy entire agent_inst directory to the proper location
            cp -r /opt/oracle/mgmt_agent/zip/unpack/agent_inst /opt/oracle/mgmt_agent/

            # Verify the copy succeeded
            if [ -f "/opt/oracle/mgmt_agent/agent_inst/bin/setup.sh" ]; then
                echo "✓ Agent files successfully moved to /opt/oracle/mgmt_agent/agent_inst"

                # Clean up the zip directory
                rm -rf /opt/oracle/mgmt_agent/zip
                echo "✓ Cleaned up temporary extraction files"
            else
                echo "ERROR: Failed to copy agent files properly"
                echo "Directory structure after copy attempt:"
                ls -laR /opt/oracle/mgmt_agent/ 2>&1 | head -50
                exit 1
            fi
        else
            echo "ERROR: Expected extracted files not found at zip/unpack/agent_inst/"
            echo "Zip extraction structure:"
            find /opt/oracle/mgmt_agent/zip -ls 2>&1 || true
            exit 1
        fi
    fi

    # Final verification - agent_inst must exist with setup.sh
    if [ ! -f "/opt/oracle/mgmt_agent/agent_inst/bin/setup.sh" ]; then
        echo "ERROR: setup.sh not found at /opt/oracle/mgmt_agent/agent_inst/bin/setup.sh"
        echo "Directory contents:"
        ls -laR /opt/oracle/mgmt_agent/ 2>&1 | head -100
        exit 1
    fi

    echo "✓ Management Agent extracted and ready"
    ls -la /opt/oracle/mgmt_agent/agent_inst/bin/ | head -20

    # Set proper permissions on agent_inst bin directory
    chmod -R 755 /opt/oracle/mgmt_agent/agent_inst/bin
    chmod +x /opt/oracle/mgmt_agent/agent_inst/bin/*
fi

# Generate secure wallet password (minimum 8 chars with complexity requirements)
WALLET_PASSWORD=$(openssl rand -base64 16 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 16)aA1!

# Create input response file for agent setup
echo "Creating response file for agent registration..."
cat > /tmp/mgmt_agent_input.rsp <<EOF
ManagementAgentInstallKey=${MGMT_AGENT_INSTALL_KEY}
AgentDisplayName=$(hostname)-mgmt-agent
CredentialWalletPassword=${WALLET_PASSWORD}
Service.plugin.prometheus.download=true
EOF

# Setup and register Management Agent if not already configured
if [ ! -f "/opt/oracle/mgmt_agent/agent_inst/config/mgmt_agent.properties" ]; then
    echo "=========================================="
    echo "Registering Management Agent with OCI..."
    echo "=========================================="
    echo "This performs:"
    echo "  1. Validating install key"
    echo "  2. Generating communication wallet"
    echo "  3. Generating security artifacts"
    echo "  4. Registering with OCI Management Agent service"
    echo "=========================================="

    # Run agent setup (this registers the agent with OCI)
    echo "Executing setup.sh with response file..."
    echo "Install Key: ${MGMT_AGENT_INSTALL_KEY:0:20}...${MGMT_AGENT_INSTALL_KEY: -10}"
    echo "Agent Name: $(hostname)-mgmt-agent"

    /opt/oracle/mgmt_agent/agent_inst/bin/setup.sh opts=/tmp/mgmt_agent_input.rsp 2>&1 | tee /tmp/setup.log
    SETUP_STATUS=$?

    if [ $SETUP_STATUS -ne 0 ]; then
        echo "ERROR: Agent setup and registration failed (exit code: $SETUP_STATUS)"
        echo ""
        echo "Setup log:"
        cat /tmp/setup.log
        echo ""
        echo "Agent log (if available):"
        cat /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log 2>/dev/null || echo "No log file available yet"
        echo ""
        echo "Please check:"
        echo "  1. Install key is valid and not expired"
        echo "  2. IAM policies allow container instance to register agent"
        echo "  3. Resource Principal authentication is working"
        echo "  4. Network connectivity to OCI services (*.oraclecloud.com)"
        exit 1
    fi

    echo "✓ Management Agent registered successfully with OCI"
else
    echo "✓ Management Agent already registered"
fi

# Wait for agent registration to complete
echo "Waiting for agent registration to finalize..."
sleep 10

# Configure Prometheus plugin
echo "Configuring Prometheus plugin..."
mkdir -p /opt/oracle/mgmt_agent/agent_inst/config/prometheus

# Generate Prometheus plugin configuration
cat > /opt/oracle/mgmt_agent/agent_inst/config/prometheus/prometheusPluginConfig.json <<PLUGEOF
{
  "entities": [
    {
      "namespace": "oci_prometheus_metrics",
      "metricNamespace": "${METRICS_NAMESPACE}",
      "resourceGroup": "$(hostname)",
      "prometheusConfig": {
        "sourceUrl": "http://localhost:9090/metrics",
        "scrapeInterval": "${PROMETHEUS_SCRAPE_INTERVAL}",
        "scrapeTimeout": "${PROMETHEUS_SCRAPE_TIMEOUT}"
      }
    }
  ]
}
PLUGEOF

# Set correct ownership if oracle user exists
if id "oracle" &>/dev/null; then
    chown -R oracle:oracle /opt/oracle/mgmt_agent/agent_inst/config/prometheus
fi

echo "✓ Prometheus plugin configured"

# Cleanup sensitive data and temporary files
rm -f /tmp/mgmt_agent_input.rsp
rm -f /tmp/oracle.mgmt_agent.rpm

echo "=========================================="
echo "Starting Management Agent..."
echo "=========================================="

# Start the agent service
if [ -f "/opt/oracle/mgmt_agent/agent_inst/bin/agentcore" ]; then
    # Start agent in background
    /opt/oracle/mgmt_agent/agent_inst/bin/agentcore start

    # Wait for agent to start
    sleep 5

    # Verify agent is running
    /opt/oracle/mgmt_agent/agent_inst/bin/agentcore status
    if [ $? -eq 0 ]; then
        echo "✓ Management Agent started successfully"
        echo "✓ Agent is now collecting and forwarding metrics to OCI Monitoring"
        echo ""
        echo "Monitoring Details:"
        echo "  - Namespace: ${METRICS_NAMESPACE}"
        echo "  - Scrape Interval: ${PROMETHEUS_SCRAPE_INTERVAL}"
        echo "  - Metrics Source: http://localhost:9090/metrics"
        echo "=========================================="
    else
        echo "ERROR: Agent failed to start properly"
        cat /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log 2>/dev/null || echo "No log file available"
        exit 1
    fi

    # Keep container running and monitor agent health
    echo "Container running. Monitoring agent health..."
    while true; do
        # Check agent status every 60 seconds
        /opt/oracle/mgmt_agent/agent_inst/bin/agentcore status > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "WARNING: Agent status check failed - attempting restart"
            /opt/oracle/mgmt_agent/agent_inst/bin/agentcore start
            sleep 10
        fi

        # Copy latest log entries to /logs volume for external monitoring
        if [ -f "/opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log" ]; then
            tail -n 100 /opt/oracle/mgmt_agent/agent_inst/log/mgmt_agent.log > /logs/agent-latest.log 2>/dev/null || true
        fi

        sleep 60
    done
else
    echo "ERROR: Agent core binary not found at /opt/oracle/mgmt_agent/agent_inst/bin/agentcore"
    exit 1
fi
