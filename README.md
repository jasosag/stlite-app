# Conciliación financiera

Software en Python + Streamlit para cruzar **Bancos**, **Tarjetas**, **Ventas** y **Proveedores**.

## En una Mac: comandos exactos para la Terminal de Cursor

Abre **Terminal** en Cursor (`Ctrl+`` ` o menú Terminal → New Terminal) y pega **un bloque a la vez**, en este orden.

### 1. Confirma que Python está instalado

```bash
python3 --version
```

Debes ver algo como `Python 3.10` o superior. Si dice `command not found`, instala Python y vuelve a este paso:

```bash
brew install python
```

(Si no tienes Homebrew: [https://brew.sh](https://brew.sh) o el instalador de [https://www.python.org/downloads/](https://www.python.org/downloads/).)

### 2. Entra a la carpeta del proyecto

```bash
cd /ruta/a/tu/proyecto
```

Sustituye la ruta por la de esta carpeta (en Cursor puedes arrastrar la carpeta a la terminal).

### 3. Crea el entorno virtual y actívalo

```bash
python3 -m venv .venv && source .venv/bin/activate
```

Cuando esté activo, el prompt suele mostrar `(.venv)`.

### 4. Instala Streamlit y las librerías

```bash
python3 -m pip install --upgrade pip && python3 -m pip install streamlit pandas openpyxl
```

Ese es el único comando de instalación que necesitas.

### 5. Arranca la interfaz

```bash
python3 -m streamlit run app.py --server.port 8517
```

Abre en el navegador: [http://localhost:8517](http://localhost:8517)

Para detener el servidor: `Ctrl+C` en la misma terminal.

## Qué hace la app

- **Panel** — totales y pendientes de los cuatro módulos
- **Bancos / Tarjetas / Ventas / Proveedores** — consulta, alta manual y plantilla CSV
- **Conciliar** — sugiere parejas con el mismo monto (ventana de 7 días) y permite cruce manual
- **Importar** — carga CSV o Excel (`.xlsx`)

Los datos de ejemplo viven en memoria: recargar la página los reinicia. Aún no hay base de datos.

## Archivos

- `app.py` — toda la interfaz y la lógica de conciliación
- `requirements.txt` — dependencias
- `.streamlit/config.toml` — puerto 8517 y tema
