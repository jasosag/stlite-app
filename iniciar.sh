#!/usr/bin/env bash
# Arranca la conciliación. En la Terminal de Cursor:
#   chmod +x iniciar.sh && ./iniciar.sh
set -euo pipefail
cd "$(dirname "$0")"

PORT=8517
URL="http://localhost:${PORT}"

puerto_ocupado() {
  python3 - "$PORT" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
s.settimeout(0.4)
try:
    s.connect(("127.0.0.1", port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

if puerto_ocupado; then
  echo "La app ya está corriendo."
  echo "Ábrela en el navegador:  ${URL}"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró Python 3."
  echo "En Mac:     brew install python"
  echo "En Ubuntu:  sudo apt install -y python3 python3-pip python3.12-venv"
  exit 1
fi

venv_usable() {
  [ -x .venv/bin/python3 ] && .venv/bin/python3 -m pip --version >/dev/null 2>&1
}

if [ -d .venv ] && ! venv_usable; then
  echo "El entorno .venv quedó a medias. Se elimina para recrearlo..."
  rm -rf .venv
fi

if [ ! -d .venv ]; then
  echo "Creando entorno virtual .venv..."
  if ! python3 -m venv .venv >/tmp/conciliacion-venv.log 2>&1; then
    echo "No se pudo crear .venv (falta el módulo venv / ensurepip)."
    echo "Se instala con el Python del sistema. En Ubuntu puedes arreglar venv con:"
    echo "  sudo apt install -y python3.12-venv"
    rm -rf .venv
  fi
fi

PIP_FLAGS=()
if venv_usable; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  export PATH="${HOME}/.local/bin:${PATH}"
  PIP_FLAGS=(--user)
fi

echo "Instalando dependencias (solo la primera vez tarda un poco)..."
python3 -m pip install "${PIP_FLAGS[@]}" --upgrade pip
python3 -m pip install "${PIP_FLAGS[@]}" -r requirements.txt

echo
echo "============================================"
echo "  Abre en tu navegador:"
echo "  ${URL}"
echo "  Para detener la app:  Ctrl+C"
echo "============================================"
echo

python3 -m streamlit run app.py --server.port "${PORT}"
