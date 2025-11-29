#!/bin/bash
# Helper script to run query_product_design with venv activated

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the script with all arguments
python3 query_product_design.py "$@"
