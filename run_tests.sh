#!/bin/bash
# Test runner script for CVForge

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests with pytest
echo "Running CVForge tests..."
python3 -m pytest tests/ -v --tb=short

# Show coverage if pytest-cov is installed
if python3 -c "import pytest_cov" 2>/dev/null; then
    echo ""
    echo "Running tests with coverage..."
    python3 -m pytest tests/ --cov=core --cov-report=term-missing
fi

