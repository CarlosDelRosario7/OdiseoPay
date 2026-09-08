#!/usr/bin/env bash

set -euo pipefail

SERVER_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname -- "$SERVER_DIR")"
VENV_DIR="${ODISEOPAY_VENV:-$PROJECT_DIR/.venv}"
PYTHON="$VENV_DIR/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Creando entorno virtual en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Comprobando dependencias..."
"$PYTHON" -m pip install -r "$SERVER_DIR/requirements.txt"

cd "$SERVER_DIR"
echo "Iniciando API en http://127.0.0.1:5000"
exec "$PYTHON" src/main.py