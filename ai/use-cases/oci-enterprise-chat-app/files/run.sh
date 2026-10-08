#!/bin/bash

# AIQ RAG Application Runner
# Runs both frontend and backend concurrently

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"

    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping backend (PID: $BACKEND_PID)${NC}"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi

    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "${BLUE}Stopping frontend (PID: $FRONTEND_PID)${NC}"
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    # Kill any remaining child processes
    pkill -P $$ 2>/dev/null || true

    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║       AIQ RAG Document Analyzer           ║"
    echo "║         Starting Application...           ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is not installed${NC}"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: npm is not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}All dependencies found.${NC}"
}

setup_backend() {
    echo -e "${YELLOW}Setting up backend...${NC}"
    cd "$BACKEND_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        echo -e "${BLUE}Installing Python dependencies...${NC}"
        pip install -q -r requirements.txt
    fi

    echo -e "${GREEN}Backend setup complete.${NC}"
}

setup_frontend() {
    echo -e "${YELLOW}Setting up frontend...${NC}"
    cd "$FRONTEND_DIR"

    # Install npm dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}Installing npm dependencies...${NC}"
        npm install --legacy-peer-deps
    fi

    echo -e "${GREEN}Frontend setup complete.${NC}"
}

start_backend() {
    echo -e "${BLUE}Starting backend server...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate

    # Start uvicorn in background
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1 | sed 's/^/[BACKEND] /' &
    BACKEND_PID=$!

    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}  → API: http://localhost:8000${NC}"
    echo -e "${GREEN}  → Docs: http://localhost:8000/docs${NC}"
}

start_frontend() {
    echo -e "${BLUE}Starting frontend server...${NC}"
    cd "$FRONTEND_DIR"

    # Start React dev server in background
    BROWSER=none npm start 2>&1 | sed 's/^/[FRONTEND] /' &
    FRONTEND_PID=$!

    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"
    echo -e "${GREEN}  → App: http://localhost:3000${NC}"
}

main() {
    print_banner
    check_dependencies

    echo ""
    setup_backend
    setup_frontend

    echo ""
    echo -e "${YELLOW}Starting services...${NC}"
    echo ""

    start_backend
    sleep 2
    start_frontend

    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         All services are running!         ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  Frontend: http://localhost:3000          ║${NC}"
    echo -e "${GREEN}║  Backend:  http://localhost:8000          ║${NC}"
    echo -e "${GREEN}║  API Docs: http://localhost:8000/docs     ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  Press Ctrl+C to stop all services        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo ""

    # Wait for both processes
    wait
}

main "$@"
