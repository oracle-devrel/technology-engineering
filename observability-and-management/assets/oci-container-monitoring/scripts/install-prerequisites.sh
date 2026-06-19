#!/bin/bash
#######################################
# Install Prerequisites for OCI Container Monitoring
# Installs required tools: OCI CLI, Terraform, jq, curl
#######################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Prerequisites Installation Script            ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
elif [ "$(uname)" = "Darwin" ]; then
    OS="macos"
else
    echo -e "${RED}Unsupported operating system${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: ${OS}${NC}"
echo ""

#######################################
# Install jq
#######################################
install_jq() {
    if command -v jq &> /dev/null; then
        echo -e "${GREEN}✓ jq is already installed${NC}"
        return 0
    fi

    echo -e "${YELLOW}Installing jq...${NC}"

    case $OS in
        ubuntu|debian)
            sudo apt-get update && sudo apt-get install -y jq
            ;;
        centos|rhel|ol|fedora)
            sudo yum install -y jq
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install jq
            else
                echo -e "${RED}Homebrew not found. Please install Homebrew first.${NC}"
                return 1
            fi
            ;;
        *)
            echo -e "${RED}Unsupported OS for jq installation${NC}"
            return 1
            ;;
    esac

    echo -e "${GREEN}✓ jq installed successfully${NC}"
}

#######################################
# Install curl
#######################################
install_curl() {
    if command -v curl &> /dev/null; then
        echo -e "${GREEN}✓ curl is already installed${NC}"
        return 0
    fi

    echo -e "${YELLOW}Installing curl...${NC}"

    case $OS in
        ubuntu|debian)
            sudo apt-get update && sudo apt-get install -y curl
            ;;
        centos|rhel|ol|fedora)
            sudo yum install -y curl
            ;;
        macos)
            echo -e "${GREEN}✓ curl is pre-installed on macOS${NC}"
            ;;
        *)
            echo -e "${RED}Unsupported OS for curl installation${NC}"
            return 1
            ;;
    esac

    echo -e "${GREEN}✓ curl installed successfully${NC}"
}

#######################################
# Install OCI CLI
#######################################
install_oci_cli() {
    if command -v oci &> /dev/null; then
        echo -e "${GREEN}✓ OCI CLI is already installed${NC}"
        oci --version
        return 0
    fi

    echo -e "${YELLOW}Installing OCI CLI...${NC}"

    # Use the official installer
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults

    # Add to PATH
    if [ "$OS" = "macos" ]; then
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bash_profile
        export PATH="$HOME/bin:$PATH"
    else
        echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/bin:$PATH"
    fi

    echo -e "${GREEN}✓ OCI CLI installed successfully${NC}"
    echo -e "${YELLOW}Please run 'oci setup config' to configure OCI CLI${NC}"
}

#######################################
# Install Terraform
#######################################
install_terraform() {
    if command -v terraform &> /dev/null; then
        echo -e "${GREEN}✓ Terraform is already installed${NC}"
        terraform version
        return 0
    fi

    echo -e "${YELLOW}Installing Terraform...${NC}"

    local TF_VERSION="1.6.6"

    case $OS in
        ubuntu|debian)
            # Add HashiCorp GPG key
            wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

            # Add HashiCorp repository
            echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

            # Install Terraform
            sudo apt-get update && sudo apt-get install -y terraform
            ;;
        centos|rhel|ol|fedora)
            # Add HashiCorp repository
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo

            # Install Terraform
            sudo yum install -y terraform
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew tap hashicorp/tap
                brew install hashicorp/tap/terraform
            else
                # Manual installation for macOS
                cd /tmp
                wget "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_darwin_amd64.zip"
                unzip "terraform_${TF_VERSION}_darwin_amd64.zip"
                sudo mv terraform /usr/local/bin/
                rm "terraform_${TF_VERSION}_darwin_amd64.zip"
            fi
            ;;
        *)
            echo -e "${RED}Unsupported OS for Terraform installation${NC}"
            return 1
            ;;
    esac

    echo -e "${GREEN}✓ Terraform installed successfully${NC}"
}

#######################################
# Verify Installations
#######################################
verify_installations() {
    echo ""
    echo -e "${CYAN}Verifying installations...${NC}"
    echo ""

    local all_good=true

    # Check jq
    if command -v jq &> /dev/null; then
        echo -e "${GREEN}✓ jq: $(jq --version)${NC}"
    else
        echo -e "${RED}✗ jq not found${NC}"
        all_good=false
    fi

    # Check curl
    if command -v curl &> /dev/null; then
        echo -e "${GREEN}✓ curl: $(curl --version | head -n1)${NC}"
    else
        echo -e "${RED}✗ curl not found${NC}"
        all_good=false
    fi

    # Check OCI CLI
    if command -v oci &> /dev/null; then
        echo -e "${GREEN}✓ OCI CLI: $(oci --version)${NC}"
    else
        echo -e "${RED}✗ OCI CLI not found${NC}"
        all_good=false
    fi

    # Check Terraform
    if command -v terraform &> /dev/null; then
        echo -e "${GREEN}✓ Terraform: $(terraform version | head -n1)${NC}"
    else
        echo -e "${RED}✗ Terraform not found${NC}"
        all_good=false
    fi

    echo ""
    if $all_good; then
        echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║   All prerequisites installed successfully!      ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "1. Configure OCI CLI: ${BLUE}oci setup config${NC}"
        echo -e "2. Run environment setup: ${BLUE}./scripts/setup-environment.sh${NC}"
        echo -e "3. Deploy monitoring: ${BLUE}./scripts/deploy.sh${NC}"
    else
        echo -e "${RED}Some prerequisites failed to install. Please check errors above.${NC}"
        exit 1
    fi
}

#######################################
# Main Installation Process
#######################################
main() {
    echo -e "${YELLOW}This script will install:${NC}"
    echo -e "  - jq (JSON processor)"
    echo -e "  - curl (HTTP client)"
    echo -e "  - OCI CLI (Oracle Cloud Infrastructure CLI)"
    echo -e "  - Terraform (Infrastructure as Code)"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 0
    fi

    echo ""
    install_curl
    echo ""
    install_jq
    echo ""
    install_oci_cli
    echo ""
    install_terraform
    echo ""
    verify_installations
}

# Run main function
main
