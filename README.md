# Conciliación financiera

Software en Python + Streamlit para cruzar **Bancos**, **Tarjetas**, **Ventas** y **Proveedores**.

---

## Cómo desplegarlo (Mac)

Hay dos formas. Si solo lo quieres ver tú, usa la **A**. Si quieres un enlace para otras personas, usa la **B**.

### A. En tu computadora (lo más rápido)

1. Abre este proyecto en Cursor.
2. Abre la Terminal: menú **Terminal → New Terminal** (o `` Ctrl+` ``).
3. Copia y pega **este bloque completo** y pulsa Enter:

```bash
chmod +x iniciar.sh && ./iniciar.sh
```

4. Cuando aparezca `You can now view your Streamlit app`, abre el navegador en:

**http://localhost:8517**

Eso instala lo que falte y levanta la interfaz. Déjala la terminal abierta mientras usas la app. Para apagarla: `Ctrl+C`.

Si aparece el error de `ensurepip` / `python3-venv` (Ubuntu o este entorno Linux), el script ya no se detiene: borra el `.venv` a medias y usa el Python del sistema. Para que el entorno virtual sí funcione en Ubuntu:

```bash
sudo apt install -y python3.12-venv
```

Si en Mac no existe `python3`:

```bash
brew install python
```

Luego vuelve a pegar `./iniciar.sh`.

### B. En internet (gratis, con Streamlit Cloud)

Streamlit Cloud **solo lee GitHub**. En el plan gratis el repositorio tiene que ser **Public**. Eso es lo que pide la pantalla “deploy a public app”.

**1. Pon el código en GitHub (público)**

Este proyecto todavía no está en GitHub. En Cursor, pulsa **Create repo**, elige visibilidad **Public** y un nombre (por ejemplo `conciliacion-financiera`). No lo dejes en Private: Streamlit gratis no lo va a listar.

No subas estados de cuenta ni Excel reales. El código puede ser público; los datos de tu empresa, no.

**2. Autoriza Streamlit**

1. Entra a [https://share.streamlit.io](https://share.streamlit.io).
2. **Sign in with GitHub** → **Authorize streamlit**.
3. Si pide acceso a repos, con **public repositories** basta. No hace falta dar permiso a los privados.

**3. Crea la app**

1. **Create app** (o **New app**).
2. Rellena exactamente esto:
   - **Repository:** el repo público que acabas de crear
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. **Deploy**.

En uno o dos minutos te da una URL tipo `https://lo-que-elijas.streamlit.app`. Esa sí la puedes guardar en Favoritos de Safari.

Si el repo no aparece en la lista: está en Private, o GitHub no está conectado. En GitHub → **Settings** → **General** → **Change repository visibility** → **Public**, recarga Streamlit.

Streamlit Cloud instala lo de `requirements.txt`. No uses `iniciar.sh` ahí: ese script es solo para tu computadora.

---

## Qué hace la app

- **Panel** — totales y pendientes de los cuatro módulos
- **Bancos / Tarjetas / Ventas / Proveedores** — consulta, alta manual y plantilla CSV
- **Conciliar** — sugiere parejas con el mismo monto (ventana de 7 días) y permite cruce manual
- **Importar** — carga CSV o Excel (`.xlsx`)

Los datos de ejemplo viven en memoria: recargar la página los reinicia. Aún no hay base de datos.

## Archivos

- `iniciar.sh` — un solo comando para desplegarlo en tu Mac
- `app.py` — interfaz y lógica de conciliación
- `requirements.txt` — librerías (Streamlit, pandas, openpyxl)
- `.streamlit/config.toml` — puerto 8517 y tema
