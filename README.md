# Mi Sistema (Streamlit)

Base de un sistema en Python con Streamlit: panel de inicio, registros en memoria, formulario de alta y configuración.

## Comando para instalar Python y Streamlit

Pega **este comando** en la Terminal de Cursor (macOS o Linux):

```bash
python3 -m pip install --upgrade pip && python3 -m pip install streamlit pandas
```

Si usas Windows (PowerShell):

```powershell
py -m pip install --upgrade pip; py -m pip install streamlit pandas
```

Python 3.10 o superior debe estar instalado. Si `python3` no se reconoce, instálalo desde [python.org](https://www.python.org/downloads/) y vuelve a ejecutar el comando.

## Cómo correr la app

Desde la carpeta del proyecto:

```bash
python3 -m streamlit run app.py --server.port 8517
```

Luego abre `http://localhost:8517` en el navegador.

## Estructura

- `app.py` — punto de entrada del sistema (navegación, registros, configuración)
- `requirements.txt` — dependencias
- `.streamlit/config.toml` — puerto, tema y opciones del servidor
