"""
Conciliación diaria — agencia de viajes.
Cruza Odoo (ventas, compras, gastos) con bancos, tarjetas de vendedores
y reportes de proveedores. Datos en memoria hasta conectar la API de Odoo.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pandas as pd
import streamlit as st

from datos import muestra_inicial
from motor import CRUCES, DIAS_VENTANA, _filtra, aplicar_match_manual, conciliar

st.set_page_config(
    page_title="Conciliación diaria · Agencia",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

MENU = [
    "Hoy",
    "Odoo",
    "Bancos",
    "Tarjetas",
    "Proveedores",
    "Conciliar a mano",
    "Importar",
]

COLUMNAS = {
    "odoo": ["fecha", "tipo", "folio", "partner", "referencia", "diario", "monto"],
    "bancos": ["fecha", "cuenta", "referencia", "descripcion", "tipo", "monto"],
    "tarjetas": ["fecha", "vendedor", "tarjeta", "comercio", "autorizacion", "monto"],
    "proveedores": ["fecha", "proveedor", "folio", "concepto", "monto"],
}


def dinero(valor: float) -> str:
    return f"${valor:,.2f}"


def hoy() -> date:
    return date.today()


def init_state() -> None:
    if "listas" not in st.session_state:
        st.session_state.listas = muestra_inicial()
    if "excepciones" not in st.session_state:
        st.session_state.excepciones = []
    if "corrida" not in st.session_state:
        st.session_state.corrida = False
    if "dia" not in st.session_state:
        st.session_state.dia = hoy()


def estilos() -> None:
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1440px; }
          [data-testid="stSidebar"] { background: #0b1220; }
          [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
          [data-testid="stMetricValue"] { font-size: 1.45rem; }
          .hero {
            background: linear-gradient(135deg, #0f766e 0%, #115e59 50%, #0f172a 100%);
            color: #f8fafc; padding: 1.3rem 1.5rem; border-radius: 16px; margin-bottom: 1rem;
          }
          .hero h1 { margin: 0 0 0.35rem 0; font-size: 1.55rem; color: #fff; }
          .hero p { margin: 0; opacity: 0.92; }
          .empty {
            border: 1px dashed #cbd5e1; border-radius: 12px; padding: 1.6rem 1.3rem;
            text-align: center; color: #64748b; background: #fff;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def filas(modulo: str) -> list[dict]:
    return st.session_state.listas[modulo]


def df_vista(modulo: str) -> pd.DataFrame:
    rows = filas(modulo)
    if not rows:
        return pd.DataFrame(columns=COLUMNAS[modulo] + ["estado"])
    frame = pd.DataFrame(rows)
    frame["estado"] = [
        "Conciliado" if r.get("conciliado") else ("Revisar" if r.get("alerta") else "Pendiente")
        for r in rows
    ]
    return frame[COLUMNAS[modulo] + ["estado"]]


def correr_conciliacion() -> None:
    resultado = conciliar(st.session_state.listas)
    st.session_state.excepciones = resultado["excepciones"]
    st.session_state.corrida = True


def sidebar() -> str:
    with st.sidebar:
        st.markdown("### ◈ Conciliación diaria")
        st.caption("Odoo · Bancos · Tarjetas · Proveedores")
        st.divider()
        seccion = st.radio("Navegación", MENU, label_visibility="collapsed")
        st.divider()
        n_ex = len(st.session_state.excepciones)
        st.metric("Excepciones", n_ex if st.session_state.corrida else "—")
        if st.button("Ejecutar conciliación", type="primary", use_container_width=True):
            correr_conciliacion()
            st.rerun()
        st.caption("Los datos de ejemplo se reinician al recargar. Aún no escribimos en Odoo.")
    return seccion


def pagina_hoy() -> None:
    st.markdown(
        """
        <div class="hero">
          <h1>Revisión diaria contra Odoo</h1>
          <p>Los estados de cuenta (bancos, tarjetas de cada vendedor y reportes de proveedores)
          se cruzan con ventas, compras y gastos de Odoo. Lo que no empató aparece abajo para corregirlo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.dia = st.date_input("Día a revisar", value=st.session_state.dia)
    dia = st.session_state.dia.isoformat()

    if not st.session_state.corrida:
        st.info("Pulsa **Ejecutar conciliación** en el menú. Con los datos de ejemplo verás faltantes, un duplicado de tarjeta y una diferencia de $100.")
        return

    ex = st.session_state.excepciones
    del_dia = [e for e in ex if e["fecha"] == dia]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Excepciones del día", len(del_dia))
    c2.metric("Faltan en Odoo", sum(1 for e in del_dia if e["tipo"] == "Falta en Odoo"))
    c3.metric("Duplicados", sum(1 for e in del_dia if e["tipo"] == "Duplicado"))
    c4.metric("Diferencias", sum(1 for e in del_dia if e["tipo"] == "Diferencia de monto"))

    st.subheader("Qué hay que atender hoy")
    if not del_dia:
        st.success("No hay excepciones en esta fecha. Cambia el día o importa archivos nuevos.")
        return

    tabla = pd.DataFrame(
        [
            {
                "Tipo": e["tipo"],
                "Fuente": e["fuente"],
                "Fecha": e["fecha"],
                "Monto": e["monto"],
                "Detalle": e["detalle"],
                "Qué hacer": e["accion"],
            }
            for e in del_dia
        ]
    )
    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={"Monto": st.column_config.NumberColumn(format="$%.2f")},
    )

    with st.expander("Todas las excepciones (otros días)"):
        otras = [e for e in ex if e["fecha"] != dia]
        if not otras:
            st.caption("No hay más.")
        else:
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Tipo": e["tipo"], "Fecha": e["fecha"], "Detalle": e["detalle"]}
                        for e in otras
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.caption(
        f"Empate automático: mismo monto (±$0.01) y hasta {DIAS_VENTANA} días de diferencia, "
        "priorizando que coincida el nombre del cliente, hotel o proveedor. "
        "Todavía no se crea ni se corrige nada dentro de Odoo: eso será el siguiente paso (API)."
    )


def pagina_modulo(titulo: str, modulo: str, ayuda: str) -> None:
    st.title(titulo)
    st.write(ayuda)
    frame = df_vista(modulo)
    total = float(frame["monto"].sum()) if not frame.empty else 0.0
    pend = frame[frame["estado"] != "Conciliado"] if not frame.empty else frame
    c1, c2, c3 = st.columns(3)
    c1.metric("Movimientos", 0 if frame.empty else len(frame))
    c2.metric("Monto", dinero(total))
    c3.metric("Sin conciliar", 0 if pend.empty else len(pend))
    if frame.empty:
        st.markdown(
            '<div class="empty">Sin movimientos. Cárgalos en Importar o agrégalos abajo.</div>',
            unsafe_allow_html=True,
        )
    else:
        filtro = st.selectbox("Estado", ["Todos", "Pendiente", "Conciliado", "Revisar"], key=f"f_{modulo}")
        vista = frame if filtro == "Todos" else frame[frame["estado"] == filtro]
        st.dataframe(
            vista,
            use_container_width=True,
            hide_index=True,
            column_config={"monto": st.column_config.NumberColumn(format="$%.2f")},
        )
    formulario_alta(modulo)


def formulario_alta(modulo: str) -> None:
    st.subheader("Agregar a mano")
    with st.form(f"alta_{modulo}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        fecha = c1.date_input("Fecha", value=hoy(), key=f"fecha_{modulo}")
        monto = c2.number_input("Monto", min_value=0.01, step=0.01, format="%.2f")
        extra: dict = {}
        if modulo == "odoo":
            extra["tipo"] = c3.selectbox("Tipo Odoo", ["venta", "compra", "gasto"])
            extra["folio"] = st.text_input("Folio / asiento")
            extra["partner"] = st.text_input("Contacto (cliente o proveedor)")
            extra["referencia"] = st.text_input("Referencia / concepto")
            extra["diario"] = st.text_input("Diario", value="Manual")
        elif modulo == "bancos":
            extra["cuenta"] = c3.text_input("Cuenta", value="BBVA ****4521")
            extra["tipo"] = st.selectbox("Tipo", ["abono", "cargo"])
            extra["referencia"] = st.text_input("Referencia bancaria")
            extra["descripcion"] = st.text_input("Descripción")
        elif modulo == "tarjetas":
            extra["vendedor"] = c3.text_input("Vendedor")
            extra["tarjeta"] = st.text_input("Tarjeta")
            extra["comercio"] = st.text_input("Comercio")
            extra["autorizacion"] = st.text_input("Autorización")
        else:
            extra["proveedor"] = c3.text_input("Proveedor")
            extra["folio"] = st.text_input("Folio del proveedor")
            extra["concepto"] = st.text_input("Concepto")
        guardar = st.form_submit_button("Guardar")

    if not guardar:
        return
    opcionales = {"referencia", "autorizacion"}
    faltan = [
        k
        for k, v in extra.items()
        if isinstance(v, str) and not v.strip() and k not in opcionales
    ]
    if faltan:
        st.error("Completa los campos obligatorios.")
        return
    item = {
        "id": f"{modulo[0]}-{uuid4().hex[:6]}",
        "fecha": fecha.isoformat(),
        "monto": float(monto),
        "conciliado": False,
        "match_id": None,
        **{k: (v.strip() if isinstance(v, str) else v) for k, v in extra.items()},
    }
    st.session_state.listas[modulo].append(item)
    st.session_state.corrida = False
    st.success("Guardado. Vuelve a ejecutar la conciliación.")
    st.rerun()


def pagina_manual() -> None:
    st.title("Conciliar a mano")
    st.write("Cuando el automático no empata (nombres distintos, varias partidas), eliges un movimiento externo y un asiento de Odoo.")
    cruce = st.selectbox("Cruce", list(CRUCES.keys()))
    mod_ext, _, reglas = CRUCES[cruce]
    ext = [r for r in _filtra(filas(mod_ext), mod_ext, reglas) if not r.get("conciliado")]
    odoo = [r for r in _filtra(filas("odoo"), "odoo", reglas) if not r.get("conciliado")]
    if not ext or not odoo:
        st.info("No hay pendientes en este cruce. Ejecuta la conciliación o cambia de cruce.")
        return
    c1, c2 = st.columns(2)
    a = c1.selectbox(
        "Externo",
        ext,
        format_func=lambda r: f"{r['fecha']} · ${r['monto']:,.2f} · {r.get('descripcion') or r.get('comercio') or r.get('proveedor')}",
    )
    b = c2.selectbox(
        "Odoo",
        odoo,
        format_func=lambda r: f"{r['folio']} · {r['partner']} · ${r['monto']:,.2f}",
    )
    if st.button("Marcar como conciliados", type="primary"):
        aplicar_match_manual(a, b)
        st.session_state.corrida = False
        st.success("Quedaron ligados en esta sesión. Ejecuta de nuevo la conciliación para refrescar excepciones.")
        st.rerun()


def pagina_importar() -> None:
    st.title("Importar")
    st.write(
        "Por ahora se cargan CSV o Excel. El siguiente paso será leer Odoo en vivo (facturas, pagos y gastos). "
        "No subas archivos con datos reales a GitHub; solo aquí, en tu sesión."
    )
    destino = st.selectbox("Destino", ["Odoo", "Bancos", "Tarjetas", "Proveedores"])
    modulo = destino.lower()
    st.code(", ".join(COLUMNAS[modulo]))
    plantilla = pd.DataFrame(columns=COLUMNAS[modulo]).to_csv(index=False).encode("utf-8")
    st.download_button("Descargar plantilla", data=plantilla, file_name=f"plantilla_{modulo}.csv", mime="text/csv")
    archivo = st.file_uploader("Archivo", type=["csv", "xlsx"])
    if archivo is None:
        st.markdown(
            '<div class="empty">Descarga la plantilla, llénala (o exporta desde Odoo / el banco) y súbela.</div>',
            unsafe_allow_html=True,
        )
        return
    try:
        crudo = pd.read_excel(archivo) if archivo.name.lower().endswith(".xlsx") else pd.read_csv(archivo)
        crudo.columns = [str(c).strip().lower() for c in crudo.columns]
        faltan = [c for c in COLUMNAS[modulo] if c not in crudo.columns]
        if faltan:
            st.error(f"Faltan columnas: {', '.join(faltan)}")
            return
        crudo["monto"] = pd.to_numeric(crudo["monto"], errors="coerce")
        crudo["fecha"] = pd.to_datetime(crudo["fecha"], errors="coerce")
        if crudo["monto"].isna().any() or crudo["fecha"].isna().any():
            st.error("Hay montos o fechas inválidas. Fechas en YYYY-MM-DD.")
            return
        crudo["fecha"] = crudo["fecha"].dt.strftime("%Y-%m-%d")
    except Exception as exc:
        st.error(str(exc))
        return
    st.dataframe(crudo[COLUMNAS[modulo]], use_container_width=True, hide_index=True)
    if st.button(f"Cargar {len(crudo)} fila(s)", type="primary"):
        for _, row in crudo.iterrows():
            item = {
                "id": f"{modulo[0]}-{uuid4().hex[:6]}",
                "conciliado": False,
                "match_id": None,
            }
            for col in COLUMNAS[modulo]:
                item[col] = float(row[col]) if col == "monto" else str(row[col])
            st.session_state.listas[modulo].append(item)
        st.session_state.corrida = False
        st.success("Cargado. Ejecuta la conciliación.")
        st.rerun()


def main() -> None:
    init_state()
    estilos()
    seccion = sidebar()
    if seccion == "Hoy":
        pagina_hoy()
    elif seccion == "Odoo":
        pagina_modulo(
            "Odoo",
            "odoo",
            "Ventas (clientes), compras (hoteles, aerolíneas, operadoras) y gastos. Esta es la base que debe quedar al día.",
        )
    elif seccion == "Bancos":
        pagina_modulo("Bancos", "bancos", "Estados de cuenta: abonos de clientes y cargos a proveedores o comisiones.")
    elif seccion == "Tarjetas":
        pagina_modulo(
            "Tarjetas",
            "tarjetas",
            "Tarjetas de la agencia asignadas a cada vendedor. Cada cargo debería existir como gasto o compra en Odoo.",
        )
    elif seccion == "Proveedores":
        pagina_modulo(
            "Proveedores",
            "proveedores",
            "Lo que el hotel, la aerolínea o el transportista dice que nos facturó. Si no está en Odoo, falta el alta.",
        )
    elif seccion == "Conciliar a mano":
        pagina_manual()
    else:
        pagina_importar()


if __name__ == "__main__":
    main()
