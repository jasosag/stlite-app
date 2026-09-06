"""Normaliza Excel/CSV reales (Odoo, banco, tarjeta, proveedor) a las columnas del sistema."""

from __future__ import annotations

import re
import unicodedata
from io import BytesIO, StringIO

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
    "partner": [
        "partner",
        "cliente",
        "proveedor",
        "empresa",
        "contacto",
        "contact",
        "partner_id",
        "nombre",
        "cliente/proveedor",
        "customer",
        "vendor",
    ],
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


def _raw_bytes(archivo) -> bytes:
    if hasattr(archivo, "getvalue"):
        data = archivo.getvalue()
    else:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
        data = archivo.read()
        if hasattr(archivo, "seek"):
            archivo.seek(0)
    if isinstance(data, str):
        return data.encode("utf-8")
    return bytes(data or b"")


def _decodifica(raw: bytes) -> str:
    """UTF-8 primero; si hay ñ/acentos de Windows, usa cp1252. latin-1 nunca falla."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def _parece_html(raw: bytes) -> bool:
    cabeza = raw.lstrip()[:4096].lower()
    return cabeza.startswith(b"<html") or cabeza.startswith(b"<!doctype") or b"<table" in cabeza


def _tiene_encabezado(df: pd.DataFrame) -> bool:
    cols = " ".join(unicodedata.normalize("NFKC", str(c)).lower() for c in df.columns)
    claves = (
        "fecha",
        "date",
        "deposito",
        "depósito",
        "retiro",
        "cargo",
        "abono",
        "monto",
        "total",
        "importe",
        "descripcion",
        "descripción",
        "concepto",
        "partner",
        "cliente",
        "proveedor",
    )
    return any(k in cols for k in claves)


def _lee_html(raw: bytes) -> pd.DataFrame | None:
    try:
        tablas = pd.read_html(StringIO(_decodifica(raw)))
    except Exception:
        return None
    if not tablas:
        return None
    return max(tablas, key=lambda t: int(t.shape[0]) * int(t.shape[1]))


def _lee_csv(raw: bytes) -> pd.DataFrame:
    texto = _decodifica(raw)
    mejor = None
    mejor_score = -1
    for skip in range(0, 12):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(StringIO(texto), sep=sep, engine="python", skiprows=skip)
            except Exception:
                continue
            if df.shape[1] < 2:
                continue
            score = int(df.shape[1])
            if _tiene_encabezado(df):
                score += 50
            if score > mejor_score:
                mejor, mejor_score = df, score
        if mejor is not None and mejor_score >= 53:
            break
    if mejor is None:
        raise ValueError(
            "No pude leer el CSV. En Excel: Archivo → Guardar como → Libro de Excel (.xlsx) y súbelo así."
        )
    return mejor


def leer_tabla(archivo) -> pd.DataFrame:
    """Lee Excel, CSV Windows-1252 (ñ) o .xls que en realidad es CSV/HTML de banco."""
    raw = _raw_bytes(archivo)
    if not raw.strip():
        raise ValueError("El archivo está vacío.")

    if raw[:2] == b"PK":
        return pd.read_excel(BytesIO(raw), engine="openpyxl")

    if raw[:4] == b"\xd0\xcf\x11\xe0":
        try:
            return pd.read_excel(BytesIO(raw))
        except Exception:
            pass

    if _parece_html(raw):
        html = _lee_html(raw)
        if html is not None and html.shape[1] >= 2:
            return html

    return _lee_csv(raw)


def _limpia_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    nombres = []
    for c in out.columns:
        t = unicodedata.normalize("NFKC", str(c)).replace("\xa0", " ").strip().lower()
        t = " ".join(t.split())
        nombres.append(t)
    out.columns = nombres
    return out.dropna(how="all")


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
    if fechas.isna().all():
        raise ValueError("No pude leer ninguna fecha. Usa YYYY-MM-DD o DD/MM/YYYY.")
    return fechas


def _num(valor) -> float | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if abs(float(valor)) < 0.005:
            return None
        return abs(float(valor))
    s = str(valor).strip()
    if not s or s.lower() in {"nan", "none", "nat", "-", "—", "n/a"}:
        return None
    s = s.replace("$", "").replace("mxn", "").replace("€", "")
    s = s.replace("\xa0", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    n = pd.to_numeric(s, errors="coerce")
    if pd.isna(n) or abs(float(n)) < 0.005:
        return None
    return abs(float(n))


def _infer_tipo_odoo(tipo_dado: str, folio: str, codigo: str) -> str | None:
    if tipo_dado and tipo_dado.lower() not in {"nan", "none", "nat"}:
        return _tipo_odoo(tipo_dado)
    blob = f"{folio} {codigo}".lower()
    if any(x in blob for x in ("inv/", "out_invoice", "venta", "fv-", "customer")):
        return "venta"
    if any(x in blob for x in ("bill/", "in_invoice", "compra", "exp/", "vendor", "fc-")):
        return "compra"
    return None


def _busca_col(df: pd.DataFrame, incluir: tuple[str, ...], excluir: tuple[str, ...] = ()) -> str | None:
    for c in df.columns:
        if any(x in c for x in excluir):
            continue
        if all(p in c for p in incluir):
            return c
    return None


def _montos_odoo(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Ventas en Total; compras en Total de compra. El 0 se ignora; si ambas tienen cifra, se elige por tipo o folio."""
    col_compra = _busca_col(df, ("total", "compra")) or _busca_col(df, ("importe", "compra"))
    col_venta = None
    for nombre in ("total", "monto", "importe", "amount", "amount total", "amount_total"):
        if nombre in df.columns:
            col_venta = nombre
            break
    if col_venta is None:
        col_venta = _busca_col(
            df,
            ("total",),
            ("compra", "impuesto", "tax", "untaxed", "sin impuesto"),
        )
    if col_venta is None and col_compra is None:
        raise ValueError("No encontré columna Total ni Total de compra.")

    montos = []
    tipos = []
    tipo_col = _col(df, "tipo")
    folio_col = _col(df, "folio")
    codigo_col = _col(df, "codigo")
    for i in df.index:
        venta = _num(df.at[i, col_venta]) if col_venta else None
        compra = _num(df.at[i, col_compra]) if col_compra else None
        tipo_dado = str(df.at[i, tipo_col]).strip() if tipo_col else ""
        folio = str(df.at[i, folio_col]).strip() if folio_col else ""
        codigo = str(df.at[i, codigo_col]).strip() if codigo_col else ""
        t = _infer_tipo_odoo(tipo_dado, folio, codigo)

        if compra and not venta:
            montos.append(compra)
            tipos.append(t or "compra")
        elif venta and not compra:
            montos.append(venta)
            tipos.append(t or "venta")
        elif venta and compra:
            if t in {"compra", "gasto"}:
                montos.append(compra)
                tipos.append(t)
            elif t == "venta":
                montos.append(venta)
                tipos.append("venta")
            elif abs(venta - compra) <= 0.05:
                montos.append(venta)
                tipos.append("venta")
            else:
                montos.append(compra)
                tipos.append("compra")
        else:
            montos.append(None)
            tipos.append(t or "compra")
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
            cargo = _num(df.at[i, cargo_c]) or 0.0
            abono = _num(df.at[i, abono_c]) or 0.0
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
        signed = pd.to_numeric(df.at[i, monto_c], errors="coerce")
        if pd.isna(signed):
            parsed = _num(df.at[i, monto_c])
            if parsed is None:
                filas.append((None, None))
                continue
            signed = parsed
        monto = float(signed)
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
        out = out[out["fecha"].notna()].copy()
        out["fecha"] = pd.to_datetime(out["fecha"]).dt.strftime("%Y-%m-%d")
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
        n0 = len(out)
        out = out[out["monto"].notna()]
        out = out[out["fecha"].notna()]
        out = out[out["partner"].astype(str).str.strip().ne("")]
        omitidas = n0 - len(out)
        if out.empty:
            raise ValueError(
                "Ninguna fila de Odoo tuvo fecha, empresa e importe. "
                f"Columnas que vi: {', '.join(df.columns)}"
            )
        out = out.copy()
        out["fecha"] = pd.to_datetime(out["fecha"]).dt.strftime("%Y-%m-%d")
        out["codigo"] = out["codigo"].where(out["codigo"].astype(str).str.len() > 0, out["folio"])
        out.attrs["omitidas"] = int(omitidas)
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
