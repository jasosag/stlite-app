"""Pruebas del lector de Excel/CSV (incluye Windows-1252 con ñ)."""

from io import BytesIO

from importar import leer_tabla, normalizar


class _Archivo(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


def test_csv_windows1252_con_ene():
    texto = (
        "Fecha,Cuenta,Descripción,Depósito,Retiro,Código\n"
        "06/09/2026,012,Pago señor López INV/2026/001,1500.50,,INV/2026/001\n"
        "06/09/2026,012,Comisión año,,25.00,\n"
    )
    crudo = texto.encode("cp1252")
    assert b"\xf1" in crudo  # ñ en Windows, no UTF-8

    # Así fallaba la app en la nube: pandas asume UTF-8.
    try:
        import pandas as pd

        pd.read_csv(BytesIO(crudo))
        raise AssertionError("pandas UTF-8 no debió leer este CSV")
    except UnicodeDecodeError as exc:
        assert "0xf1" in str(exc) or "utf-8" in str(exc).lower()

    tabla = leer_tabla(_Archivo(crudo, "estado.csv"))
    listo = normalizar(tabla, "bancos")
    assert len(listo) == 2
    assert listo.iloc[0]["monto"] == 1500.50
    assert listo.iloc[0]["tipo"] == "abono"
    assert "López" in listo.iloc[0]["descripcion"]
    assert listo.iloc[1]["tipo"] == "cargo"
    assert listo.iloc[1]["monto"] == 25.00


def test_xls_que_en_realidad_es_csv():
    texto = "Fecha,Depósito,Retiro,Descripción\n01/09/2026,200.00,,Abono niño\n"
    tabla = leer_tabla(_Archivo(texto.encode("cp1252"), "estado.xls"))
    listo = normalizar(tabla, "bancos")
    assert len(listo) == 1
    assert listo.iloc[0]["monto"] == 200.0


def test_csv_utf8_con_acentos():
    texto = "Fecha,Depósito,Retiro,Descripción\n02/09/2026,,80.00,Comisión\n"
    tabla = leer_tabla(_Archivo(texto.encode("utf-8"), "banco.csv"))
    listo = normalizar(tabla, "bancos")
    assert len(listo) == 1
    assert listo.iloc[0]["tipo"] == "cargo"


if __name__ == "__main__":
    test_csv_windows1252_con_ene()
    test_xls_que_en_realidad_es_csv()
    test_csv_utf8_con_acentos()
    print("ok")
