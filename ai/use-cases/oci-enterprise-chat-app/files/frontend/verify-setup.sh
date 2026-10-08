#!/bin/bash

# AIQ RAG Frontend Setup Verification Script

echo "======================================"
echo "AIQ RAG Frontend Setup Verification"
echo "======================================"
echo ""

# Check Node.js version
echo "Checking Node.js version..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo "✓ Node.js installed: $NODE_VERSION"

    # Extract major version
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$MAJOR_VERSION" -ge 18 ]; then
        echo "✓ Node.js version is compatible (18+)"
    else
        echo "✗ Node.js version should be 18 or higher"
    fi
else
    echo "✗ Node.js not found. Please install Node.js 18+"
fi

echo ""

# Check npm
echo "Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo "✓ npm installed: $NPM_VERSION"
else
    echo "✗ npm not found"
fi

echo ""

# Check if in correct directory
echo "Checking directory structure..."
if [ -f "package.json" ]; then
    echo "✓ package.json found"
else
    echo "✗ package.json not found. Are you in the frontend directory?"
fi

if [ -d "src" ]; then
    echo "✓ src directory found"
else
    echo "✗ src directory not found"
fi

if [ -f "src/App.tsx" ]; then
    echo "✓ App.tsx found"
else
    echo "✗ App.tsx not found"
fi

echo ""

# Check for required files
echo "Checking configuration files..."
FILES=("tsconfig.json" "tailwind.config.js" "postcss.config.js" ".env")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file found"
    else
        echo "✗ $file not found"
    fi
done

echo ""

# Check if node_modules exists
echo "Checking dependencies..."
if [ -d "node_modules" ]; then
    echo "✓ node_modules directory found"
    echo "  Dependencies appear to be installed"
else
    echo "⚠ node_modules not found"
    echo "  Run 'npm install' to install dependencies"
fi

echo ""

# Check backend connectivity (optional)
echo "Checking backend API connectivity..."
if command -v curl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|404\|301\|302"; then
        echo "✓ Backend API is accessible at http://localhost:8000"
    else
        echo "⚠ Backend API not responding at http://localhost:8000"
        echo "  Make sure the backend is running before starting the frontend"
    fi
else
    echo "⚠ curl not available, skipping API check"
fi

echo ""
echo "======================================"
echo "Verification Complete"
echo "======================================"
echo ""

if [ ! -d "node_modules" ]; then
    echo "Next steps:"
    echo "1. Run: npm install"
    echo "2. Run: npm start"
else
    echo "Next step:"
    echo "Run: npm start"
fi

echo ""
