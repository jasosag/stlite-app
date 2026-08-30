# Conciliación diaria contra Odoo (agencia de viajes)

Cruza **Odoo** (ventas, compras y gastos) con **bancos**, **tarjetas de cada vendedor** y **reportes de proveedores**. Detecta faltantes en Odoo, duplicados y diferencias de monto.

Los datos de ejemplo viven en memoria. Aún no se conecta la API de Odoo ni se escribe de vuelta al ERP.

## Cómo correrla

```bash
chmod +x iniciar.sh && ./iniciar.sh
```

Abre http://localhost:8517

En Streamlit Cloud, tras cambiar código: `git push github main` y Reboot en la app.

## Uso diario (prototipo)

1. Importa (o usa el ejemplo) Odoo + bancos + tarjetas + proveedores.
2. **Ejecutar conciliación**.
3. En **Hoy**, atiende faltantes, duplicados y diferencias.

No subas estados de cuenta reales a GitHub.

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

- **Hoy** — excepciones del día: falta en Odoo, duplicados, diferencia de monto
- **Odoo / Bancos / Tarjetas / Proveedores** — cada fuente
- **Conciliar a mano** — cuando el automático no empata
- **Importar** — CSV o Excel (plantillas incluidas)

## Archivos

- `app.py` — interfaz
- `motor.py` — reglas de cruce
- `datos.py` — ejemplo de agencia de viajes
- `iniciar.sh` — arranque en Mac
- `requirements.txt` — librerías
