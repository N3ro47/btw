#!/bin/bash

# Define the output file
OUTPUT_FILE="project_bundle.txt"

# Find and bundle .g4, .py, README*, and .arch files
find . -type f \( -name "*.g4" -o -name "*.py" -o -name "README*" -o -name "*.arch" \) \
    -not -path "*/.*" \
    -not -path "*/.venv/*" \
    -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" \
    -exec sh -c '
        for file; do
            echo "================================================================================"
            echo "FILE: $file"
            echo "================================================================================"
            cat "$file"
            echo -e "\n"
        done
    ' sh {} + > "$OUTPUT_FILE"

echo "Project files bundled into $OUTPUT_FILE"
