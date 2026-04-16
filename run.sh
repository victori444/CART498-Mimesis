#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"

cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but was not found in your terminal."
    exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Creating virtual environment in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

if ! "$PYTHON_BIN" -c "import PyPDF2, dotenv, openai, tqdm" >/dev/null 2>&1; then
    echo "Installing Python dependencies from requirements.txt"
    "$PYTHON_BIN" -m pip install -r "$PROJECT_DIR/requirements.txt"
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Warning: .env file not found. The app will ask for your OPENAI_API_KEY."
fi

exec "$PYTHON_BIN" "$PROJECT_DIR/main.py"
