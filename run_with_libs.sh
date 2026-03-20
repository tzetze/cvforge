#!/bin/bash
# Helper script to run Python with Homebrew libraries in the path
# This is needed for WeasyPrint to find gobject, pango, and other system libraries

export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"

# Use virtual environment Python if available, otherwise use system Python
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="python3"
fi

# If first argument is python or python3, replace it with our Python
if [ "$1" = "python" ] || [ "$1" = "python3" ]; then
    shift
    exec "$PYTHON" "$@"
else
    # Otherwise run the command as-is
    exec "$@"
fi

