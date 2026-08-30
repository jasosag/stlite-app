"""Motor de conciliación diaria: Odoo contra bancos, tarjetas y proveedores."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

TOLERANCIA = 0.01
DIAS_VENTANA = 5

CRUCES = {
    "Bancos abonos ↔ Odoo ventas": ("bancos", "odoo", {"tipo_banco": "abono", "tipo_odoo": "venta"}),
    "Bancos cargos ↔ Odoo compras/gastos": ("bancos", "odoo", {"tipo_banco": "cargo", "tipo_odoo": ("compra", "gasto")}),
    "Tarjetas ↔ Odoo gastos/compras": ("tarjetas", "odoo", {"tipo_odoo": ("gasto", "compra")}),
    "Proveedores ↔ Odoo compras/gastos": ("proveedores", "odoo", {"tipo_odoo": ("compra", "gasto")}),
}


def _norm(texto: str) -> str:
    t = str(texto or "").lower().strip()
    return t.translate(str.maketrans("áéíóúüñ", "aeiouun"))


def _fecha(row: dict) -> datetime:
    return datetime.fromisoformat(str(row["fecha"]))


def _monto_igual(a: float, b: float) -> bool:
    return abs(float(a) - float(b)) <= TOLERANCIA


def _dias(a: dict, b: dict) -> int:
    return abs((_fecha(a) - _fecha(b)).days)


def _etiqueta_odoo(row: dict) -> str:
    return f"{row['folio']} · {row['tipo']} · {row['partner']} · ${row['monto']:,.2f}"


def _etiqueta_ext(row: dict, modulo: str) -> str:
    monto = f"${row['monto']:,.2f}"
    if modulo == "bancos":
        return f"{row['tipo']} {monto} · {row['descripcion']}"
    if modulo == "tarjetas":
        return f"{row['vendedor']} · {row['comercio']} · {monto}"
    return f"{row['proveedor']} · {row['folio']} · {monto}"


def _filtra(rows: list[dict], modulo: str, reglas: dict) -> list[dict]:
    out = list(rows)
    if modulo == "bancos" and reglas.get("tipo_banco"):
        out = [r for r in out if r.get("tipo") == reglas["tipo_banco"]]
    if modulo == "odoo" and reglas.get("tipo_odoo"):
        tipos = reglas["tipo_odoo"]
        if isinstance(tipos, str):
            tipos = (tipos,)
        out = [r for r in out if r.get("tipo") in tipos]
    return out


def _pareja_texto(ext: dict, odoo: dict, modulo: str) -> float:
    """0 = nada en común, 1 = mismo partner/comercio en el texto."""
    blob_ext = " ".join(
        str(ext.get(k, ""))
        for k in ("descripcion", "comercio", "proveedor", "partner", "referencia", "concepto")
    )
    blob_odoo = f"{odoo.get('partner', '')} {odoo.get('referencia', '')}"
    ne, no = _norm(blob_ext), _norm(blob_odoo)
    if not ne or not no:
        return 0.0
    tokens = [t for t in no.split() if len(t) >= 4]
    if not tokens:
        return 0.3 if ne[:8] in no or no[:8] in ne else 0.0
    hits = sum(1 for t in tokens if t in ne)
    return hits / len(tokens)


def detectar_duplicados(rows: list[dict], modulo: str) -> list[dict]:
    vistos: dict[tuple, list[dict]] = {}
    for row in rows:
        clave = (
            row.get("fecha"),
            round(float(row["monto"]), 2),
            _norm(str(row.get("autorizacion") or row.get("referencia") or row.get("folio") or "")),
        )
        vistos.setdefault(clave, []).append(row)
    hallazgos = []
    for grupo in vistos.values():
        if len(grupo) < 2:
            continue
        ids = [g["id"] for g in grupo]
        hallazgos.append(
            {
                "id": f"dup-{uuid4().hex[:6]}",
                "tipo": "Duplicado",
                "fuente": modulo,
                "fecha": grupo[0]["fecha"],
                "monto": float(grupo[0]["monto"]),
                "detalle": f"{len(grupo)} movimientos iguales: " + " | ".join(_etiqueta_ext(g, modulo) for g in grupo),
                "accion": "Revisar en el estado de cuenta y no registrar dos veces en Odoo.",
                "ids": ids,
            }
        )
    return hallazgos


def _sugerir_cruce(ext: list[dict], odoo: list[dict], modulo: str) -> list[tuple[dict, dict, int, str]]:
    usados_o: set[str] = set()
    usados_e: set[str] = set()
    pares: list[tuple[dict, dict, int, str]] = []
    candidatos: list[tuple[float, int, dict, dict]] = []
    for e in ext:
        if e.get("conciliado"):
            continue
        for o in odoo:
            dias = _dias(e, o)
            if dias > DIAS_VENTANA:
                continue
            igual = _monto_igual(e["monto"], o["monto"])
            texto = _pareja_texto(e, o, modulo)
            if igual:
                score = 2.0 + texto - dias * 0.05
            elif texto >= 0.5 and abs(float(e["monto"]) - float(o["monto"])) <= 200:
                score = 0.8 + texto - dias * 0.05
            else:
                continue
            candidatos.append((score, dias, e, o))
    candidatos.sort(key=lambda x: -x[0])
    for score, dias, e, o in candidatos:
        if e["id"] in usados_e or o["id"] in usados_o:
            continue
        if _monto_igual(e["monto"], o["monto"]):
            clase = "ok"
        else:
            clase = "diff"
        usados_e.add(e["id"])
        usados_o.add(o["id"])
        pares.append((e, o, dias, clase))
    return pares


def conciliar(listas: dict) -> dict:
    """Marca conciliados y devuelve excepciones (faltantes, duplicados, diferencias)."""
    for lista in listas.values():
        for row in lista:
            row["conciliado"] = False
            row["match_id"] = None
            row["matches"] = []
            row["alerta"] = None

    excepciones: list[dict] = []
    for modulo in ("bancos", "tarjetas", "proveedores"):
        excepciones.extend(detectar_duplicados(listas[modulo], modulo))

    ids_duplicados = {i for ex in excepciones if ex["tipo"] == "Duplicado" for i in ex["ids"]}
    ids_duplicados_secundarios = set()
    for ex in excepciones:
        if ex["tipo"] == "Duplicado" and len(ex["ids"]) > 1:
            ids_duplicados_secundarios.update(ex["ids"][1:])

    for nombre, (mod_ext, _, reglas) in CRUCES.items():
        ext = [
            r
            for r in _filtra(listas[mod_ext], mod_ext, reglas)
            if r["id"] not in ids_duplicados_secundarios
        ]
        odoo = _filtra(listas["odoo"], "odoo", reglas)
        for e, o, dias, clase in _sugerir_cruce(ext, odoo, mod_ext):
            if clase == "ok":
                mid = str(uuid4())[:8]
                e["conciliado"] = True
                e["match_id"] = mid
                o["matches"].append(mid)
                o["match_id"] = mid
                o["conciliado"] = True
            else:
                diff = abs(float(e["monto"]) - float(o["monto"]))
                excepciones.append(
                    {
                        "id": f"dif-{uuid4().hex[:6]}",
                        "tipo": "Diferencia de monto",
                        "fuente": nombre,
                        "fecha": e["fecha"],
                        "monto": diff,
                        "detalle": (
                            f"{_etiqueta_ext(e, mod_ext)}  ↔  {_etiqueta_odoo(o)} "
                            f"(separados {dias} día(s), diferencia ${diff:,.2f})"
                        ),
                        "accion": "Revisar comisión, descuento o error de captura en Odoo.",
                        "ids": [e["id"], o["id"]],
                    }
                )
                e["alerta"] = "diferencia"
                o["alerta"] = "diferencia"

    for row in listas["bancos"]:
        if not row["conciliado"] and row.get("alerta") != "diferencia":
            if row["tipo"] == "abono":
                accion = "Puede faltar una venta o un cobro en Odoo."
            else:
                accion = "Puede faltar una compra, un gasto o está sin conciliar a propósito (comisión)."
            excepciones.append(
                {
                    "id": f"fo-{row['id']}",
                    "tipo": "Falta en Odoo",
                    "fuente": "bancos",
                    "fecha": row["fecha"],
                    "monto": float(row["monto"]),
                    "detalle": _etiqueta_ext(row, "bancos"),
                    "accion": accion,
                    "ids": [row["id"]],
                }
            )
    for row in listas["tarjetas"]:
        if row["conciliado"] or row["id"] in ids_duplicados:
            continue
        if row.get("alerta") == "diferencia":
            continue
        excepciones.append(
            {
                "id": f"fo-{row['id']}",
                "tipo": "Falta en Odoo",
                "fuente": "tarjetas",
                "fecha": row["fecha"],
                "monto": float(row["monto"]),
                "detalle": _etiqueta_ext(row, "tarjetas"),
                "accion": "Registrar el gasto o la compra del vendedor en Odoo.",
                "ids": [row["id"]],
            }
        )
    for row in listas["proveedores"]:
        if row["conciliado"] or row.get("alerta") == "diferencia":
            continue
        excepciones.append(
            {
                "id": f"fo-{row['id']}",
                "tipo": "Falta en Odoo",
                "fuente": "proveedores",
                "fecha": row["fecha"],
                "monto": float(row["monto"]),
                "detalle": _etiqueta_ext(row, "proveedores"),
                "accion": "Alta de factura de proveedor en Odoo (account.move compra).",
                "ids": [row["id"]],
            }
        )
    for row in listas["odoo"]:
        if row["conciliado"] or row.get("alerta") == "diferencia":
            continue
        excepciones.append(
            {
                "id": f"ff-{row['id']}",
                "tipo": "Falta en banco/tarjeta/proveedor",
                "fuente": "odoo",
                "fecha": row["fecha"],
                "monto": float(row["monto"]),
                "detalle": _etiqueta_odoo(row),
                "accion": "Está en Odoo pero no apareció en el estado de cuenta importado. Esperar el corte o revisar archivo.",
                "ids": [row["id"]],
            }
        )

    excepciones.sort(key=lambda x: (x["fecha"], x["tipo"]))
    return {"excepciones": excepciones}


def aplicar_match_manual(a: dict, b: dict) -> None:
    mid = str(uuid4())[:8]
    a["conciliado"] = True
    b["conciliado"] = True
    a["match_id"] = mid
    b["match_id"] = mid
    a["alerta"] = None
    b["alerta"] = None
