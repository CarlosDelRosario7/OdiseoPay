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

if [[ "${ODISEOPAY_SKIP_MIGRATIONS:-0}" != "1" ]]; then
    echo "Aplicando migraciones de la base de datos..."
    if ! "$PYTHON" -m alembic -c alembic.ini upgrade head; then
        echo "Error: no se pudieron aplicar las migraciones." >&2
        echo "Revisa la conexión a MariaDB/MySQL y las variables de server/.env." >&2
        exit 1
    fi
fi

echo "Iniciando API en http://127.0.0.1:5000"
exec "$PYTHON" src/main.py
