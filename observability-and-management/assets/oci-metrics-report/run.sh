#!/bin/bash

# OCI Metrics Report Generator - Startup Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting OCI Metrics Report Generator...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Check OCI config
if [ ! -f ~/.oci/config ]; then
    echo -e "${YELLOW}Warning: OCI config file not found at ~/.oci/config${NC}"
    echo "Please configure your OCI CLI before using this application."
fi

# Start the application
echo -e "${GREEN}Starting server on http://localhost:8080${NC}"
echo -e "Press Ctrl+C to stop the server"
echo ""

python app.py
