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

Si `./iniciar.sh` dice `command not found` o `python3` no existe:

```bash
brew install python
```

Luego vuelve a pegar `./iniciar.sh`.

### B. En internet (gratis, con Streamlit Cloud)

Así otras personas abren la app con un enlace, sin instalar Python.

1. Sube este proyecto a **GitHub** (en Cursor: Create repo, o `git push` a un repositorio tuyo).
2. Entra a [https://share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub.
3. Pulsa **Create app**.
4. Elige tu repositorio, la rama `main` y el archivo **`app.py`**.
5. Pulsa **Deploy**. En uno o dos minutos te da una URL tipo `https://tu-app.streamlit.app`.

Streamlit Cloud lee `requirements.txt` solo. No uses `iniciar.sh` ahí: ese script es solo para tu Mac.

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
