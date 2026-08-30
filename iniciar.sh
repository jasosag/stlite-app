#!/usr/bin/env bash
# Arranca la conciliación en tu Mac. Úsalo desde la Terminal de Cursor:
#   chmod +x iniciar.sh && ./iniciar.sh
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3."
  echo "Instálalo con:  brew install python"
  echo "O desde:        https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creando entorno virtual .venv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Instalando dependencias (solo la primera vez tarda un poco)..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo
echo "============================================"
echo "  Abre en tu navegador:"
echo "  http://localhost:8517"
echo "  Para detener la app:  Ctrl+C"
echo "============================================"
echo

python3 -m streamlit run app.py --server.port 8517
