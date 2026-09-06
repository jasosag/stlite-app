"""Normaliza Excel/CSV reales (Odoo, banco, tarjeta, proveedor) a las columnas del sistema."""

from __future__ import annotations

import pandas as pd

ALIASES = {
    "fecha": [
        "fecha",
        "date",
        "fecha factura",
        "invoice date",
        "bill date",
        "posting date",
        "fecha operacion",
        "fecha operación",
        "fecha de operacion",
        "value date",
        "transaction date",
    ],
    "monto": [
        "monto",
        "total",
        "amount",
        "amount_total",
        "amount total",
        "importe",
        "importe mxn",
        "cargo/abono",
        "total signed",
        "amount_total_signed",
        "total de compra",
        "total compra",
    ],
    "tipo": ["tipo", "type", "move_type", "move type", "invoice type", "tipo de movimiento", "tipo de documento"],
    "codigo": [
        "codigo",
        "código",
        "codigo odoo",
        "código odoo",
        "clave",
        "key",
        "id odoo",
        "odoo",
        "codigo conciliacion",
        "código conciliación",
    ],
    "partner": ["partner", "cliente", "proveedor", "empresa", "contacto", "contact", "partner_id"],
    "referencia": ["referencia", "ref", "concepto", "communication", "payment_reference", "memo"],
    "diario": ["diario", "journal", "journal_id"],
    "cuenta": ["cuenta", "account", "clabe", "product"],
    "descripcion": ["descripcion", "descripción", "description", "detalle", "concepto", "narrativa"],
    "referencia_banco": ["referencia", "ref", "referencia bancaria", "tracking key"],
    "vendedor": ["vendedor", "seller", "empleado", "titular", "card holder"],
    "tarjeta": ["tarjeta", "card", "ultimos 4", "últimos 4", "mask"],
    "comercio": ["comercio", "merchant", "establecimiento", "descripcion", "descripción"],
    "autorizacion": ["autorizacion", "autorización", "auth", "authorization"],
    "proveedor": ["proveedor", "vendor", "supplier", "empresa", "hotel"],
    "concepto": ["concepto", "descripcion", "descripción", "description", "detalle"],
    "cargo": ["cargo", "cargos", "retiro", "retiros", "debit", "debits", "withdrawals"],
    "abono": [
        "abono",
        "abonos",
        "deposito",
        "depósito",
        "depositos",
        "depósitos",
        "credit",
        "credits",
        "deposits",
    ],
}

TIPO_ODOO = {
    "venta": "venta",
    "ventas": "venta",
    "out_invoice": "venta",
    "out_refund": "venta",
    "customer invoice": "venta",
    "factura cliente": "venta",
    "compra": "compra",
    "compras": "compra",
    "in_invoice": "compra",
    "in_refund": "compra",
    "vendor bill": "compra",
    "factura proveedor": "compra",
    "gasto": "gasto",
    "gastos": "gasto",
    "expense": "gasto",
    "hr_expense": "gasto",
}


def _limpia_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [" ".join(str(c).strip().lower().split()) for c in out.columns]
    return out


def _col(df: pd.DataFrame, clave: str) -> str | None:
    for alias in ALIASES.get(clave, [clave]):
        if alias in df.columns:
            return alias
    return None


def _serie(df: pd.DataFrame, clave: str, default: str = "") -> pd.Series:
    col = _col(df, clave)
    if col is None:
        return pd.Series([default] * len(df), index=df.index)
    return df[col].fillna(default).astype(str).str.strip()


def _fechas(df: pd.DataFrame) -> pd.Series:
    col = _col(df, "fecha")
    if col is None:
        raise ValueError("No encontré una columna de fecha. Renómbrala a 'fecha'.")
    fechas = pd.to_datetime(df[col], errors="coerce", format="mixed")
    if fechas.isna().any():
        fechas2 = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        fechas = fechas.fillna(fechas2)
    if fechas.isna().any():
        malas = int(fechas.isna().sum())
        raise ValueError(f"Hay {malas} fecha(s) que no pude leer. Usa YYYY-MM-DD o DD/MM/YYYY.")
    return fechas.dt.strftime("%Y-%m-%d")


def _num(valor) -> float | None:
    n = pd.to_numeric(valor, errors="coerce")
    if pd.isna(n):
        return None
    return abs(float(n))


def _montos_odoo(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Ventas suelen venir en Total; compras en Total de compra. Si hay ambas, se usa la que tenga número."""
    col_compra = None
    for nombre in ("total de compra", "total compra", "importe de compra", "importe compra"):
        if nombre in df.columns:
            col_compra = nombre
            break
    col_venta = None
    for nombre in ("total", "monto", "importe", "amount", "amount total", "amount_total"):
        if nombre in df.columns:
            col_venta = nombre
            break
    if col_venta is None and col_compra is None:
        raise ValueError("No encontré columna Total ni Total de compra.")

    montos = []
    tipos = []
    tipo_col = _col(df, "tipo")
    for i in df.index:
        venta = _num(df.at[i, col_venta]) if col_venta else None
        compra = _num(df.at[i, col_compra]) if col_compra else None
        tipo_dado = str(df.at[i, tipo_col]).strip() if tipo_col else ""
        if compra and not venta:
            montos.append(compra)
            tipos.append(_tipo_odoo(tipo_dado) if tipo_dado else "compra")
        elif venta and not compra:
            montos.append(venta)
            tipos.append(_tipo_odoo(tipo_dado) if tipo_dado else "venta")
        elif venta and compra:
            if tipo_dado:
                t = _tipo_odoo(tipo_dado)
                montos.append(compra if t in {"compra", "gasto"} else venta)
                tipos.append(t)
            else:
                raise ValueError(
                    f"Fila {i + 2}: hay valor en Total y en Total de compra. Deja uno vacío o pon la columna Tipo."
                )
        else:
            montos.append(None)
            tipos.append(_tipo_odoo(tipo_dado) if tipo_dado else "compra")
    return pd.Series(tipos, index=df.index), pd.Series(montos, index=df.index)


def _tipo_odoo(valor: str) -> str:
    clave = str(valor or "").strip().lower()
    if clave in TIPO_ODOO:
        return TIPO_ODOO[clave]
    if "venta" in clave or "cliente" in clave or "out_" in clave:
        return "venta"
    if "compra" in clave or "proveedor" in clave or "in_" in clave:
        return "compra"
    if "gasto" in clave or "expense" in clave:
        return "gasto"
    return "compra"


def _bancos_monto_tipo(df: pd.DataFrame) -> pd.DataFrame:
    cargo_c = _col(df, "cargo")
    abono_c = _col(df, "abono")
    monto_c = _col(df, "monto")
    tipo_c = _col(df, "tipo")
    filas = []
    for i in df.index:
        if cargo_c and abono_c:
            cargo = pd.to_numeric(df.at[i, cargo_c], errors="coerce")
            abono = pd.to_numeric(df.at[i, abono_c], errors="coerce")
            cargo = 0.0 if pd.isna(cargo) else abs(float(cargo))
            abono = 0.0 if pd.isna(abono) else abs(float(abono))
            if cargo > 0 and abono == 0:
                filas.append(("cargo", cargo))
            elif abono > 0 and cargo == 0:
                filas.append(("abono", abono))
            elif cargo == 0 and abono == 0:
                filas.append((None, None))
            else:
                raise ValueError(f"Fila {i + 2}: cargo y abono tienen valor. Deja uno en cero.")
            continue
        if monto_c is None:
            raise ValueError("Necesito 'monto' o un par 'cargo' y 'abono'.")
        monto = pd.to_numeric(df.at[i, monto_c], errors="coerce")
        if pd.isna(monto):
            filas.append((None, None))
            continue
        monto = float(monto)
        tipo = str(df.at[i, tipo_c]).strip().lower() if tipo_c else ""
        if tipo in {"cargo", "retiro", "debit"}:
            filas.append(("cargo", abs(monto)))
        elif tipo in {"abono", "deposito", "depósito", "credit"}:
            filas.append(("abono", abs(monto)))
        elif monto < 0:
            filas.append(("cargo", abs(monto)))
        else:
            filas.append(("abono", abs(monto)))
    tipos = [t for t, m in filas]
    montos = [m for t, m in filas]
    return pd.DataFrame({"tipo": tipos, "monto": montos}, index=df.index)


def normalizar(df: pd.DataFrame, modulo: str) -> pd.DataFrame:
    df = _limpia_cols(df)
    fechas = _fechas(df)
    if modulo == "bancos":
        ta = _bancos_monto_tipo(df)
        out = pd.DataFrame(
            {
                "fecha": fechas,
                "cuenta": _serie(df, "cuenta", "cuenta 1"),
                "referencia": _serie(df, "referencia_banco"),
                "descripcion": _serie(df, "descripcion"),
                "codigo": _serie(df, "codigo"),
                "tipo": ta["tipo"],
                "monto": ta["monto"],
            }
        )
        out = out.dropna(subset=["tipo", "monto"])
    elif modulo == "odoo":
        tipos, montos = _montos_odoo(df)
        out = pd.DataFrame(
            {
                "fecha": fechas,
                "tipo": tipos,
                "folio": _serie(df, "folio", "S/F"),
                "codigo": _serie(df, "codigo"),
                "partner": _serie(df, "partner"),
                "referencia": _serie(df, "referencia"),
                "diario": _serie(df, "diario", "Odoo"),
                "monto": montos,
            }
        )
        if out["partner"].eq("").any():
            raise ValueError("Hay filas de Odoo sin cliente/proveedor (partner).")
        if out["monto"].isna().any():
            raise ValueError("Hay filas de Odoo sin Total ni Total de compra.")
        out["codigo"] = out["codigo"].where(out["codigo"].str.len() > 0, out["folio"])
    elif modulo == "tarjetas":
        col_m = _col(df, "monto")
        if col_m is None:
            raise ValueError("No encontré columna de monto en tarjetas.")
        out = pd.DataFrame(
            {
                "fecha": fechas,
                "vendedor": _serie(df, "vendedor", "Sin asignar"),
                "tarjeta": _serie(df, "tarjeta", "Tarjeta"),
                "comercio": _serie(df, "comercio"),
                "autorizacion": _serie(df, "autorizacion"),
                "codigo": _serie(df, "codigo"),
                "monto": pd.to_numeric(df[col_m], errors="coerce").abs(),
            }
        )
        if out["comercio"].eq("").any():
            raise ValueError("Hay cargos de tarjeta sin comercio/descripción.")
        if out["monto"].isna().any():
            raise ValueError("Hay montos de tarjeta inválidos.")
    else:
        col_m = _col(df, "monto")
        if col_m is None:
            raise ValueError("No encontré columna de monto en proveedores.")
        out = pd.DataFrame(
            {
                "fecha": fechas,
                "proveedor": _serie(df, "proveedor"),
                "folio": _serie(df, "folio", "S/F"),
                "codigo": _serie(df, "codigo"),
                "concepto": _serie(df, "concepto"),
                "monto": pd.to_numeric(df[col_m], errors="coerce").abs(),
            }
        )
        if out["proveedor"].eq("").any():
            raise ValueError("Hay filas sin nombre de proveedor.")
        if out["monto"].isna().any():
            raise ValueError("Hay montos de proveedor inválidos.")
    return out.reset_index(drop=True)
