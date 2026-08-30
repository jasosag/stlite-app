"""
Base del sistema — Streamlit
Este archivo es el punto de entrada. Agrega nuevas secciones
en MENU y una función de página por cada una.
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Mi Sistema",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Estilos ---
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.6rem; padding-bottom: 3rem; }
      [data-testid="stSidebar"] { background: #0f172a; }
      [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
      [data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; }
      [data-testid="stMetricValue"] { font-size: 1.7rem; }
      .hero {
        background: linear-gradient(135deg, #0f766e 0%, #134e4a 100%);
        color: #f8fafc;
        padding: 1.4rem 1.6rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
      }
      .hero h1 { margin: 0 0 0.35rem 0; font-size: 1.7rem; color: #fff; }
      .hero p { margin: 0; opacity: 0.9; }
      .empty {
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem 1.5rem;
        text-align: center;
        color: #64748b;
        background: #fff;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

MENU = {
    "Inicio": "inicio",
    "Registros": "registros",
    "Nuevo registro": "nuevo",
    "Configuración": "config",
}


def init_state() -> None:
    if "registros" not in st.session_state:
        st.session_state.registros = [
            {
                "id": 1,
                "titulo": "Reunión de arranque",
                "categoria": "Operación",
                "fecha": date.today().isoformat(),
                "estado": "En curso",
                "notas": "Primera sesión del sistema.",
                "creado": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        ]
    if "nombre_sistema" not in st.session_state:
        st.session_state.nombre_sistema = "Mi Sistema"
    if "proximo_id" not in st.session_state:
        st.session_state.proximo_id = 2


def sidebar() -> str:
    with st.sidebar:
        st.markdown("### ◈ " + st.session_state.nombre_sistema)
        st.caption("Base para construir tu aplicación")
        st.divider()
        seccion = st.radio(
            "Navegación",
            list(MENU.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"{len(st.session_state.registros)} registro(s) en memoria")
        st.caption("Los datos se reinician al recargar la página.")
    return seccion


def df_registros() -> pd.DataFrame:
    if not st.session_state.registros:
        return pd.DataFrame(
            columns=["id", "titulo", "categoria", "fecha", "estado", "notas", "creado"]
        )
    return pd.DataFrame(st.session_state.registros)


def pagina_inicio() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <h1>Bienvenido a {st.session_state.nombre_sistema}</h1>
          <p>Esta es la base de tu sistema. Usa el menú para crear registros, consultarlos y ajustar la configuración.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    registros = st.session_state.registros
    en_curso = sum(1 for r in registros if r["estado"] == "En curso")
    cerrados = sum(1 for r in registros if r["estado"] == "Cerrado")
    pendientes = sum(1 for r in registros if r["estado"] == "Pendiente")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(registros))
    c2.metric("En curso", en_curso)
    c3.metric("Pendientes", pendientes)
    c4.metric("Cerrados", cerrados)

    st.subheader("Últimos registros")
    if not registros:
        st.markdown(
            '<div class="empty">Aún no hay registros. Ve a <strong>Nuevo registro</strong> para crear el primero.</div>',
            unsafe_allow_html=True,
        )
        return

    st.dataframe(
        df_registros()[["titulo", "categoria", "fecha", "estado"]].tail(8),
        use_container_width=True,
        hide_index=True,
    )


def pagina_registros() -> None:
    st.title("Registros")
    st.write("Consulta, filtra o elimina elementos de tu sistema.")

    datos = df_registros()
    if datos.empty:
        st.markdown(
            '<div class="empty">No hay registros todavía. Crea uno desde <strong>Nuevo registro</strong>.</div>',
            unsafe_allow_html=True,
        )
        return

    col_f1, col_f2 = st.columns(2)
    categorias = ["Todas"] + sorted(datos["categoria"].unique().tolist())
    estados = ["Todos"] + sorted(datos["estado"].unique().tolist())
    cat = col_f1.selectbox("Categoría", categorias)
    est = col_f2.selectbox("Estado", estados)

    filtrado = datos.copy()
    if cat != "Todas":
        filtrado = filtrado[filtrado["categoria"] == cat]
    if est != "Todos":
        filtrado = filtrado[filtrado["estado"] == est]

    if filtrado.empty:
        st.info("Ningún registro coincide con esos filtros.")
        return

    st.dataframe(
        filtrado[["id", "titulo", "categoria", "fecha", "estado", "notas"]],
        use_container_width=True,
        hide_index=True,
    )

    ids = filtrado["id"].tolist()
    elegido = st.selectbox("Eliminar registro", ids, format_func=lambda i: f"#{i}")
    if st.button("Eliminar", type="secondary"):
        st.session_state.registros = [
            r for r in st.session_state.registros if r["id"] != elegido
        ]
        st.success(f"Se eliminó el registro #{elegido}.")
        st.rerun()


def pagina_nuevo() -> None:
    st.title("Nuevo registro")
    st.write("Completa el formulario. Los campos con * son obligatorios.")

    with st.form("form_nuevo", clear_on_submit=True):
        titulo = st.text_input("Título *")
        col1, col2 = st.columns(2)
        categoria = col1.selectbox(
            "Categoría",
            ["Operación", "Cliente", "Finanzas", "Otro"],
        )
        estado = col2.selectbox("Estado", ["Pendiente", "En curso", "Cerrado"])
        fecha = st.date_input("Fecha", value=date.today())
        notas = st.text_area("Notas", placeholder="Detalle opcional…")
        enviado = st.form_submit_button("Guardar", type="primary")

    if not enviado:
        return

    if not titulo.strip():
        st.error("El título es obligatorio.")
        return

    nuevo = {
        "id": st.session_state.proximo_id,
        "titulo": titulo.strip(),
        "categoria": categoria,
        "fecha": fecha.isoformat(),
        "estado": estado,
        "notas": notas.strip(),
        "creado": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.registros.append(nuevo)
    st.session_state.proximo_id += 1
    st.success(f"Registro #{nuevo['id']} guardado: {nuevo['titulo']}")
    st.balloons()


def pagina_config() -> None:
    st.title("Configuración")
    st.write("Ajustes básicos. Esto vive en la sesión actual; al recargar se vuelve al valor por defecto.")

    nombre = st.text_input("Nombre del sistema", value=st.session_state.nombre_sistema)
    if st.button("Guardar nombre", type="primary"):
        if not nombre.strip():
            st.error("El nombre no puede estar vacío.")
        else:
            st.session_state.nombre_sistema = nombre.strip()
            st.success("Nombre actualizado. Mira el menú de la izquierda.")
            st.rerun()

    st.divider()
    st.subheader("Datos de la sesión")
    st.warning("Borrar registros elimina todo lo cargado en memoria. No se puede deshacer.")
    if st.button("Vaciar registros"):
        st.session_state.registros = []
        st.session_state.proximo_id = 1
        st.success("Se vació la lista de registros.")
        st.rerun()


def main() -> None:
    init_state()
    seccion = sidebar()
    clave = MENU[seccion]
    if clave == "inicio":
        pagina_inicio()
    elif clave == "registros":
        pagina_registros()
    elif clave == "nuevo":
        pagina_nuevo()
    else:
        pagina_config()


if __name__ == "__main__":
    main()
