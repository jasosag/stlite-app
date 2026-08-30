"""
Conciliación financiera — Bancos, Tarjetas, Ventas y Proveedores.
Punto de entrada del sistema. Datos en memoria (se reinician al recargar).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from uuid import uuid4

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Conciliación financiera",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

MENU = [
    "Panel",
    "Bancos",
    "Tarjetas",
    "Ventas",
    "Proveedores",
    "Conciliar",
    "Importar",
]

TOLERANCIA = 0.01
DIAS_VENTANA = 7

COLUMNAS = {
    "bancos": ["fecha", "cuenta", "referencia", "descripcion", "tipo", "monto"],
    "tarjetas": ["fecha", "tarjeta", "comercio", "autorizacion", "monto"],
    "ventas": ["fecha", "folio", "cliente", "forma_pago", "monto"],
    "proveedores": ["fecha", "folio", "proveedor", "concepto", "monto"],
}

TIPOS_CONCILIACION = {
    "Ventas ↔ Bancos (abonos)": ("ventas", "bancos", "abono"),
    "Ventas ↔ Tarjetas": ("ventas", "tarjetas", None),
    "Proveedores ↔ Bancos (cargos)": ("proveedores", "bancos", "cargo"),
    "Proveedores ↔ Tarjetas": ("proveedores", "tarjetas", None),
}


def dinero(valor: float) -> str:
    return f"${valor:,.2f}"


def hoy() -> date:
    return date.today()


def muestra_inicial() -> dict:
    """Datos de ejemplo para que la interfaz se vea llena desde el primer clic."""
    d = hoy()
    return {
        "bancos": [
            {
                "id": "b1",
                "fecha": (d - timedelta(days=9)).isoformat(),
                "cuenta": "BBVA ****4521",
                "referencia": "SPEI-88921",
                "descripcion": "SPEI in Agencia Norte",
                "tipo": "abono",
                "monto": 24500.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "b2",
                "fecha": (d - timedelta(days=7)).isoformat(),
                "cuenta": "BBVA ****4521",
                "referencia": "PAGO-4410",
                "descripcion": "Pago Hotel Palmas",
                "tipo": "cargo",
                "monto": 9800.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "b3",
                "fecha": (d - timedelta(days=4)).isoformat(),
                "cuenta": "BBVA ****4521",
                "referencia": "SPEI-89002",
                "descripcion": "SPEI in Tour escuela",
                "tipo": "abono",
                "monto": 15700.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "b4",
                "fecha": (d - timedelta(days=12)).isoformat(),
                "cuenta": "BBVA ****4521",
                "referencia": "COM-12",
                "descripcion": "Comisión SPEI",
                "tipo": "cargo",
                "monto": 85.00,
                "conciliado": False,
                "match_id": None,
            },
        ],
        "tarjetas": [
            {
                "id": "t1",
                "fecha": (d - timedelta(days=8)).isoformat(),
                "tarjeta": "Visa ****8891",
                "comercio": "POS sucursal — Cliente López",
                "autorizacion": "A88321",
                "monto": 8320.50,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "t2",
                "fecha": (d - timedelta(days=6)).isoformat(),
                "tarjeta": "Visa ****8891",
                "comercio": "Aerolínea MX",
                "autorizacion": "A88402",
                "monto": 4100.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "t3",
                "fecha": (d - timedelta(days=2)).isoformat(),
                "tarjeta": "AMEX ****2204",
                "comercio": "Combustible corporativo",
                "autorizacion": "A89011",
                "monto": 1260.00,
                "conciliado": False,
                "match_id": None,
            },
        ],
        "ventas": [
            {
                "id": "v1",
                "fecha": (d - timedelta(days=10)).isoformat(),
                "folio": "V-1001",
                "cliente": "Agencia Norte",
                "forma_pago": "Transferencia",
                "monto": 24500.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "v2",
                "fecha": (d - timedelta(days=8)).isoformat(),
                "folio": "V-1002",
                "cliente": "Cliente López",
                "forma_pago": "Tarjeta",
                "monto": 8320.50,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "v3",
                "fecha": (d - timedelta(days=5)).isoformat(),
                "folio": "V-1003",
                "cliente": "Tour escuela",
                "forma_pago": "Transferencia",
                "monto": 15800.00,
                "conciliado": False,
                "match_id": None,
            },
        ],
        "proveedores": [
            {
                "id": "p1",
                "fecha": (d - timedelta(days=8)).isoformat(),
                "folio": "P-501",
                "proveedor": "Hotel Palmas",
                "concepto": "Hospedaje grupo",
                "monto": 9800.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "p2",
                "fecha": (d - timedelta(days=6)).isoformat(),
                "folio": "P-502",
                "proveedor": "Aerolínea MX",
                "concepto": "Boletos",
                "monto": 4100.00,
                "conciliado": False,
                "match_id": None,
            },
            {
                "id": "p3",
                "fecha": (d - timedelta(days=3)).isoformat(),
                "folio": "P-503",
                "proveedor": "Transportes Sur",
                "concepto": "Traslados",
                "monto": 3200.00,
                "conciliado": False,
                "match_id": None,
            },
        ],
    }


def init_state() -> None:
    if "listas" not in st.session_state:
        st.session_state.listas = muestra_inicial()
    if "nombre" not in st.session_state:
        st.session_state.nombre = "Conciliación financiera"


def estilos() -> None:
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }
          [data-testid="stSidebar"] { background: #0b1220; }
          [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
          [data-testid="stMetricValue"] { font-size: 1.55rem; }
          .hero {
            background: linear-gradient(135deg, #0f766e 0%, #115e59 55%, #0f172a 100%);
            color: #f8fafc; padding: 1.35rem 1.55rem; border-radius: 16px; margin-bottom: 1.1rem;
          }
          .hero h1 { margin: 0 0 0.3rem 0; font-size: 1.65rem; color: #fff; letter-spacing: -0.02em; }
          .hero p { margin: 0; opacity: 0.92; }
          .empty {
            border: 1px dashed #cbd5e1; border-radius: 12px; padding: 1.8rem 1.4rem;
            text-align: center; color: #64748b; background: #fff;
          }
          .match-ok { background: #ecfdf5; border: 1px solid #99f6e4; border-radius: 10px; padding: 0.7rem 0.9rem; }
          .match-warn { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px; padding: 0.7rem 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def filas(modulo: str) -> list[dict]:
    return st.session_state.listas[modulo]


def df_modulo(modulo: str) -> pd.DataFrame:
    rows = filas(modulo)
    if not rows:
        cols = COLUMNAS[modulo] + ["estado"]
        return pd.DataFrame(columns=cols)
    frame = pd.DataFrame(rows)
    frame["estado"] = frame["conciliado"].map(lambda x: "Conciliado" if x else "Pendiente")
    return frame


def suma(modulo: str, conciliado: bool | None = None) -> float:
    total = 0.0
    for row in filas(modulo):
        if conciliado is None or row["conciliado"] is conciliado:
            total += float(row["monto"])
    return total


def pendiente_count(modulo: str) -> int:
    return sum(1 for row in filas(modulo) if not row["conciliado"])


def etiqueta(row: dict, modulo: str) -> str:
    fecha = row["fecha"]
    monto = dinero(row["monto"])
    estado = "✓" if row["conciliado"] else "○"
    if modulo == "bancos":
        return f"{estado} {fecha} · {row['tipo']} {monto} · {row['descripcion']}"
    if modulo == "tarjetas":
        return f"{estado} {fecha} · {monto} · {row['comercio']}"
    if modulo == "ventas":
        return f"{estado} {fecha} · {row['folio']} · {row['cliente']} · {monto}"
    return f"{estado} {fecha} · {row['folio']} · {row['proveedor']} · {monto}"


def plantilla_csv(modulo: str) -> bytes:
    return pd.DataFrame(columns=COLUMNAS[modulo]).to_csv(index=False).encode("utf-8")


def aplicar_match(a: dict, b: dict) -> None:
    match_id = str(uuid4())[:8]
    a["conciliado"] = True
    b["conciliado"] = True
    a["match_id"] = match_id
    b["match_id"] = match_id


def deshacer_match(match_id: str) -> None:
    for lista in st.session_state.listas.values():
        for row in lista:
            if row.get("match_id") == match_id:
                row["conciliado"] = False
                row["match_id"] = None


def filtrar_banco(rows: list[dict], tipo: str | None) -> list[dict]:
    if not tipo:
        return rows
    return [r for r in rows if r.get("tipo") == tipo]


def candidatos_auto(izq: list[dict], der: list[dict]) -> list[tuple[dict, dict, int]]:
    usados_der: set[str] = set()
    pares: list[tuple[dict, dict, int]] = []
    for a in izq:
        if a["conciliado"]:
            continue
        mejor = None
        mejor_dias = 99
        for b in der:
            if b["conciliado"] or b["id"] in usados_der:
                continue
            if abs(float(a["monto"]) - float(b["monto"])) > TOLERANCIA:
                continue
            delta = abs(
                (datetime.fromisoformat(a["fecha"]) - datetime.fromisoformat(b["fecha"])).days
            )
            if delta <= DIAS_VENTANA and delta < mejor_dias:
                mejor = b
                mejor_dias = delta
        if mejor:
            usados_der.add(mejor["id"])
            pares.append((a, mejor, mejor_dias))
    return pares


def leer_archivo(uploaded) -> pd.DataFrame:
    nombre = uploaded.name.lower()
    if nombre.endswith(".xlsx"):
        return pd.read_excel(uploaded)
    return pd.read_csv(uploaded)


def normalizar_import(df: pd.DataFrame, modulo: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltan = [c for c in COLUMNAS[modulo] if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas: {', '.join(faltan)}")
    out = df[COLUMNAS[modulo]].copy()
    out["monto"] = pd.to_numeric(out["monto"], errors="coerce")
    if out["monto"].isna().any():
        raise ValueError("Hay montos que no son numéricos.")
    out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")
    if out["fecha"].isna().any():
        raise ValueError("Hay fechas inválidas. Usa YYYY-MM-DD.")
    out["fecha"] = out["fecha"].dt.strftime("%Y-%m-%d")
    if modulo == "bancos":
        out["tipo"] = out["tipo"].astype(str).str.lower().str.strip()
        if not out["tipo"].isin(["cargo", "abono"]).all():
            raise ValueError("En Bancos, tipo debe ser cargo o abono.")
    return out


def filas_desde_df(df: pd.DataFrame, modulo: str) -> list[dict]:
    nuevas = []
    prefijo = modulo[0]
    for _, row in df.iterrows():
        item = {"id": f"{prefijo}-{uuid4().hex[:6]}", "conciliado": False, "match_id": None}
        for col in COLUMNAS[modulo]:
            valor = row[col]
            item[col] = float(valor) if col == "monto" else str(valor)
        nuevas.append(item)
    return nuevas


def sidebar() -> str:
    with st.sidebar:
        st.markdown(f"### ◈ {st.session_state.nombre}")
        st.caption("Bancos · Tarjetas · Ventas · Proveedores")
        st.divider()
        seccion = st.radio("Navegación", MENU, label_visibility="collapsed")
        st.divider()
        pendientes = sum(pendiente_count(m) for m in COLUMNAS)
        st.metric("Pendientes", pendientes)
        st.caption("Los datos viven en esta sesión. Recargar la página los reinicia.")
    return seccion


def pagina_panel() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <h1>{st.session_state.nombre}</h1>
          <p>Cruza movimientos de banco y tarjeta con ventas y facturas de proveedores. Empieza en Conciliar o carga tus CSV en Importar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Cómo desplegar esta app en tu Mac o en internet"):
        st.markdown(
            """
En la Terminal de Cursor, dentro de la carpeta del proyecto, pega:

```bash
chmod +x iniciar.sh && ./iniciar.sh
```

Luego abre [http://localhost:8517](http://localhost:8517). Para apagarla: `Ctrl+C`.

Para publicarla en internet: sube el proyecto a GitHub y crea la app en [share.streamlit.io](https://share.streamlit.io) eligiendo el archivo `app.py`.
            """
        )

    bloques = [
        ("Bancos", "bancos"),
        ("Tarjetas", "tarjetas"),
        ("Ventas", "ventas"),
        ("Proveedores", "proveedores"),
    ]
    cols = st.columns(4)
    for col, (titulo, modulo) in zip(cols, bloques):
        total = suma(modulo)
        pend = suma(modulo, False)
        n_pend = pendiente_count(modulo)
        col.metric(titulo, dinero(total), f"{n_pend} pendientes · {dinero(pend)}")

    st.subheader("Qué falta por conciliar")
    resumen = pd.DataFrame(
        [
            {
                "Módulo": titulo,
                "Movimientos": len(filas(modulo)),
                "Pendientes": pendiente_count(modulo),
                "Monto pendiente": suma(modulo, False),
                "Monto conciliado": suma(modulo, True),
            }
            for titulo, modulo in bloques
        ]
    )
    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Monto pendiente": st.column_config.NumberColumn(format="$%.2f"),
            "Monto conciliado": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

    st.info(
        "Con los datos de ejemplo, **Conciliar → Sugerir coincidencias** debe empatar "
        "V-1001 con el SPEI de Agencia Norte, V-1002 con el cargo POS, "
        "Hotel Palmas con el cargo bancario y Aerolínea MX con la tarjeta."
    )


def tabla_modulo(modulo: str) -> None:
    frame = df_modulo(modulo)
    if frame.empty:
        st.markdown(
            '<div class="empty">No hay movimientos. Cárgalos en <strong>Importar</strong> o agrégalos abajo.</div>',
            unsafe_allow_html=True,
        )
        return
    visibles = COLUMNAS[modulo] + ["estado"]
    filtro = st.selectbox("Estado", ["Todos", "Pendiente", "Conciliado"], key=f"filtro_{modulo}")
    vista = frame[visibles]
    if filtro != "Todos":
        vista = vista[vista["estado"] == filtro]
    if vista.empty:
        st.info("Ningún movimiento con ese filtro.")
        return
    st.dataframe(
        vista,
        use_container_width=True,
        hide_index=True,
        column_config={"monto": st.column_config.NumberColumn(format="$%.2f")},
    )


def formulario_alta(modulo: str) -> None:
    st.subheader("Agregar movimiento")
    with st.form(f"alta_{modulo}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        fecha = c1.date_input("Fecha", value=hoy(), key=f"f_{modulo}")
        monto = c2.number_input("Monto", min_value=0.01, step=0.01, format="%.2f")
        extra: dict = {}
        if modulo == "bancos":
            extra["cuenta"] = c3.text_input("Cuenta", value="BBVA ****4521")
            extra["tipo"] = st.selectbox("Tipo", ["abono", "cargo"])
            extra["referencia"] = st.text_input("Referencia")
            extra["descripcion"] = st.text_input("Descripción")
        elif modulo == "tarjetas":
            extra["tarjeta"] = c3.text_input("Tarjeta", value="Visa ****8891")
            extra["comercio"] = st.text_input("Comercio")
            extra["autorizacion"] = st.text_input("Autorización")
        elif modulo == "ventas":
            extra["folio"] = c3.text_input("Folio")
            extra["cliente"] = st.text_input("Cliente")
            extra["forma_pago"] = st.selectbox("Forma de pago", ["Transferencia", "Tarjeta", "Efectivo"])
        else:
            extra["folio"] = c3.text_input("Folio")
            extra["proveedor"] = st.text_input("Proveedor")
            extra["concepto"] = st.text_input("Concepto")
        guardar = st.form_submit_button("Guardar", type="primary")

    if not guardar:
        return

    obligatorios = [v for k, v in extra.items() if k not in {"referencia", "autorizacion"}]
    if any(isinstance(v, str) and not v.strip() for v in obligatorios):
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
    st.success("Movimiento guardado.")
    st.rerun()


def pagina_modulo(titulo: str, modulo: str, ayuda: str) -> None:
    st.title(titulo)
    st.write(ayuda)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", dinero(suma(modulo)))
    c2.metric("Pendiente", dinero(suma(modulo, False)))
    c3.metric("Conciliado", dinero(suma(modulo, True)))
    tabla_modulo(modulo)
    st.download_button(
        "Descargar plantilla CSV",
        data=plantilla_csv(modulo),
        file_name=f"plantilla_{modulo}.csv",
        mime="text/csv",
        key=f"dl_{modulo}",
    )
    formulario_alta(modulo)


def pagina_conciliar() -> None:
    st.title("Conciliar")
    st.write(
        "El sistema sugiere parejas con el **mismo monto** y fecha a no más de "
        f"{DIAS_VENTANA} días. Tú confirmas o concilias a mano."
    )

    tipo = st.selectbox("Cruce", list(TIPOS_CONCILIACION.keys()))
    mod_izq, mod_der, tipo_banco = TIPOS_CONCILIACION[tipo]
    izq = filas(mod_izq)
    der = filtrar_banco(filas(mod_der), tipo_banco)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(mod_izq.capitalize())
        pend_izq = [r for r in izq if not r["conciliado"]]
        st.caption(f"{len(pend_izq)} pendientes")
        if pend_izq:
            st.dataframe(
                pd.DataFrame(pend_izq)[COLUMNAS[mod_izq]],
                use_container_width=True,
                hide_index=True,
                column_config={"monto": st.column_config.NumberColumn(format="$%.2f")},
            )
        else:
            st.success("Nada pendiente en este lado.")
    with col_b:
        st.subheader(mod_der.capitalize() + (f" · {tipo_banco}" if tipo_banco else ""))
        pend_der = [r for r in der if not r["conciliado"]]
        st.caption(f"{len(pend_der)} pendientes")
        if pend_der:
            st.dataframe(
                pd.DataFrame(pend_der)[COLUMNAS[mod_der]],
                use_container_width=True,
                hide_index=True,
                column_config={"monto": st.column_config.NumberColumn(format="$%.2f")},
            )
        else:
            st.success("Nada pendiente en este lado.")

    sugeridos = candidatos_auto(izq, der)
    st.subheader("Sugerencias")
    if not sugeridos:
        st.markdown(
            '<div class="empty">No hay coincidencias de monto en la ventana de fechas. Prueba otro cruce o concilia a mano.</div>',
            unsafe_allow_html=True,
        )
    else:
        for a, b, dias in sugeridos:
            st.markdown(
                f'<div class="match-ok"><strong>{dinero(a["monto"])}</strong> · '
                f'{etiqueta(a, mod_izq)}<br/>↔ {etiqueta(b, mod_der)}'
                f'<br/><span style="opacity:.75">Separadas {dias} día(s)</span></div>',
                unsafe_allow_html=True,
            )
        if st.button(f"Aceptar {len(sugeridos)} coincidencia(s)", type="primary"):
            for a, b, _ in sugeridos:
                if not a["conciliado"] and not b["conciliado"]:
                    aplicar_match(a, b)
            st.success("Coincidencias conciliadas.")
            st.rerun()

    st.divider()
    st.subheader("Conciliar a mano")
    c1, c2 = st.columns(2)
    opciones_izq = [r for r in izq if not r["conciliado"]]
    opciones_der = [r for r in der if not r["conciliado"]]
    if not opciones_izq or not opciones_der:
        st.caption("Necesitas al menos un pendiente de cada lado.")
        return

    sel_a = c1.selectbox(
        mod_izq.capitalize(),
        opciones_izq,
        format_func=lambda r: etiqueta(r, mod_izq),
        key="manual_a",
    )
    sel_b = c2.selectbox(
        mod_der.capitalize(),
        opciones_der,
        format_func=lambda r: etiqueta(r, mod_der),
        key="manual_b",
    )
    diff = abs(float(sel_a["monto"]) - float(sel_b["monto"]))
    if diff > TOLERANCIA:
        st.markdown(
            f'<div class="match-warn">Los montos no coinciden: diferencia {dinero(diff)}. '
            "Puedes forzar la conciliación si así lo decides.</div>",
            unsafe_allow_html=True,
        )
    if st.button("Conciliar selección"):
        aplicar_match(sel_a, sel_b)
        st.success("Movimientos conciliados.")
        st.rerun()

    st.divider()
    st.subheader("Deshacer un cruce")
    ids = sorted(
        {
            r["match_id"]
            for lista in st.session_state.listas.values()
            for r in lista
            if r.get("match_id")
        }
    )
    if not ids:
        st.caption("Aún no hay cruces confirmados.")
        return
    elegido = st.selectbox("match_id", ids)
    if st.button("Deshacer"):
        deshacer_match(elegido)
        st.success(f"Se revirtió el cruce {elegido}.")
        st.rerun()


def pagina_importar() -> None:
    st.title("Importar")
    st.write("Sube un CSV o Excel (.xlsx) con las columnas de la plantilla. Las filas se agregan a las de ejemplo.")

    modulo_nombre = st.selectbox(
        "Destino",
        ["Bancos", "Tarjetas", "Ventas", "Proveedores"],
    )
    modulo = modulo_nombre.lower()
    st.code(", ".join(COLUMNAS[modulo]), language=None)

    st.download_button(
        "Descargar plantilla",
        data=plantilla_csv(modulo),
        file_name=f"plantilla_{modulo}.csv",
        mime="text/csv",
    )

    archivo = st.file_uploader("Archivo", type=["csv", "xlsx"], key="uploader")
    if archivo is None:
        st.markdown(
            '<div class="empty">Aún no hay archivo. Descarga la plantilla, llénala y súbela aquí.</div>',
            unsafe_allow_html=True,
        )
        return

    try:
        crudo = leer_archivo(archivo)
        listo = normalizar_import(crudo, modulo)
    except Exception as exc:
        st.error(str(exc))
        return

    st.dataframe(listo, use_container_width=True, hide_index=True)
    if st.button(f"Cargar {len(listo)} fila(s) a {modulo_nombre}", type="primary"):
        st.session_state.listas[modulo].extend(filas_desde_df(listo, modulo))
        st.success(f"Se cargaron {len(listo)} movimientos.")
        st.rerun()


def main() -> None:
    init_state()
    estilos()
    seccion = sidebar()
    if seccion == "Panel":
        pagina_panel()
    elif seccion == "Bancos":
        pagina_modulo(
            "Bancos",
            "bancos",
            "Estados de cuenta: abonos (entradas) y cargos (salidas).",
        )
    elif seccion == "Tarjetas":
        pagina_modulo(
            "Tarjetas",
            "tarjetas",
            "Cargos de tarjetas corporativas o cobros con terminal.",
        )
    elif seccion == "Ventas":
        pagina_modulo(
            "Ventas",
            "ventas",
            "Facturas o notas de venta que deben aparecer en banco o tarjeta.",
        )
    elif seccion == "Proveedores":
        pagina_modulo(
            "Proveedores",
            "proveedores",
            "Facturas por pagar o ya pagadas que debes cruzar con la salida de dinero.",
        )
    elif seccion == "Conciliar":
        pagina_conciliar()
    else:
        pagina_importar()


if __name__ == "__main__":
    main()
