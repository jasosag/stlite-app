"""Datos de ejemplo de una agencia de viajes + asientos tipo Odoo.

El campo codigo es el identificador de Odoo que también se captura
en bancos, tarjetas y proveedores.
"""

from __future__ import annotations

from datetime import date, timedelta


def _d(dias: int) -> str:
    return (date.today() - timedelta(days=dias)).isoformat()


def muestra_inicial() -> dict:
    return {
        "odoo": [
            {
                "id": "o1",
                "fecha": _d(0),
                "tipo": "venta",
                "folio": "INV/2026/1001",
                "codigo": "INV/2026/1001",
                "partner": "Agencia Norte",
                "referencia": "Tour Cancún familia Pérez",
                "diario": "Clientes",
                "monto": 24500.00,
            },
            {
                "id": "o2",
                "fecha": _d(0),
                "tipo": "compra",
                "folio": "BILL/2026/0501",
                "codigo": "BILL/2026/0501",
                "partner": "Hotel Palmas",
                "referencia": "Hospedaje grupo 12 pax",
                "diario": "Proveedores",
                "monto": 9800.00,
            },
            {
                "id": "o3",
                "fecha": _d(0),
                "tipo": "gasto",
                "folio": "EXP/2026/0310",
                "codigo": "EXP/2026/0310",
                "partner": "Aerolínea MX",
                "referencia": "Boletos reemitidos — Ana López",
                "diario": "Gastos tarjeta",
                "monto": 4100.00,
            },
            {
                "id": "o4",
                "fecha": _d(0),
                "tipo": "venta",
                "folio": "INV/2026/1003",
                "codigo": "INV/2026/1003",
                "partner": "Tour escuela",
                "referencia": "Paquete Puebla",
                "diario": "Clientes",
                "monto": 15800.00,
            },
            {
                "id": "o5",
                "fecha": _d(1),
                "tipo": "compra",
                "folio": "BILL/2026/0498",
                "codigo": "BILL/2026/0498",
                "partner": "Operadora Caribe",
                "referencia": "Traslados aeropuerto",
                "diario": "Proveedores",
                "monto": 3200.00,
            },
        ],
        "bancos": [
            {
                "id": "b1",
                "fecha": _d(0),
                "cuenta": "BBVA ****4521",
                "codigo": "INV/2026/1001",
                "referencia": "SPEI-88921",
                "descripcion": "SPEI in Agencia Norte",
                "tipo": "abono",
                "monto": 24500.00,
            },
            {
                "id": "b2",
                "fecha": _d(0),
                "cuenta": "BBVA ****4521",
                "codigo": "BILL/2026/0501",
                "referencia": "PAGO-4410",
                "descripcion": "Pago Hotel Palmas",
                "tipo": "cargo",
                "monto": 9800.00,
            },
            {
                "id": "b3",
                "fecha": _d(0),
                "cuenta": "BBVA ****4521",
                "codigo": "INV/2026/1003",
                "referencia": "SPEI-89002",
                "descripcion": "SPEI in Tour escuela",
                "tipo": "abono",
                "monto": 15700.00,
            },
            {
                "id": "b4",
                "fecha": _d(1),
                "cuenta": "BBVA ****4521",
                "codigo": "",
                "referencia": "COM-12",
                "descripcion": "Comisión SPEI",
                "tipo": "cargo",
                "monto": 85.00,
            },
        ],
        "tarjetas": [
            {
                "id": "t1",
                "fecha": _d(0),
                "vendedor": "Ana López",
                "tarjeta": "Visa ****8891",
                "comercio": "Aerolínea MX",
                "autorizacion": "A88402",
                "codigo": "EXP/2026/0310",
                "monto": 4100.00,
            },
            {
                "id": "t2",
                "fecha": _d(0),
                "vendedor": "Ana López",
                "tarjeta": "Visa ****8891",
                "comercio": "Aerolínea MX",
                "autorizacion": "A88402",
                "codigo": "EXP/2026/0310",
                "monto": 4100.00,
            },
            {
                "id": "t3",
                "fecha": _d(0),
                "vendedor": "Carlos Ruiz",
                "tarjeta": "AMEX ****2204",
                "comercio": "Combustible corporativo",
                "autorizacion": "A89011",
                "codigo": "",
                "monto": 1260.00,
            },
            {
                "id": "t4",
                "fecha": _d(1),
                "vendedor": "Marisol Peña",
                "tarjeta": "Visa ****1022",
                "comercio": "POS sucursal — Cliente López",
                "autorizacion": "A88321",
                "codigo": "",
                "monto": 8320.50,
            },
        ],
        "proveedores": [
            {
                "id": "p1",
                "fecha": _d(0),
                "proveedor": "Hotel Palmas",
                "folio": "HP-7781",
                "codigo": "BILL/2026/0501",
                "concepto": "Hospedaje grupo 12 pax",
                "monto": 9800.00,
            },
            {
                "id": "p2",
                "fecha": _d(0),
                "proveedor": "Aerolínea MX",
                "folio": "AMX-22019",
                "codigo": "EXP/2026/0310",
                "concepto": "Boletos reemitidos",
                "monto": 4100.00,
            },
            {
                "id": "p3",
                "fecha": _d(0),
                "proveedor": "Transportes Sur",
                "folio": "TS-440",
                "codigo": "",
                "concepto": "Camioneta grupo escuela",
                "monto": 2750.00,
            },
            {
                "id": "p4",
                "fecha": _d(1),
                "proveedor": "Operadora Caribe",
                "folio": "OC-91",
                "codigo": "BILL/2026/0498",
                "concepto": "Traslados aeropuerto",
                "monto": 3200.00,
            },
        ],
    }
