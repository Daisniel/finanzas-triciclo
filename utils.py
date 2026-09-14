from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_FLOOR


def fecha_hoy_iso() -> str:
    return date.today().isoformat()


def fecha_hoy_usuario() -> str:
    return date.today().strftime("%d/%m/%Y")


def normalizar_fecha(texto: str) -> str:
    valor = texto.strip()
    if not valor:
        return fecha_hoy_iso()

    valor = valor.replace("-", "/")
    partes = valor.split("/")

    try:
        if len(partes) == 2:
            dia, mes = map(int, partes)
            anio = date.today().year
        elif len(partes) == 3:
            dia, mes, anio = map(int, partes)
            if anio < 100:
                anio += 2000
        else:
            raise ValueError
        return date(anio, mes, dia).isoformat()
    except ValueError as exc:
        raise ValueError(
            "La fecha no es válida. Usa DD/MM, DD/MM/AAAA o déjala vacía."
        ) from exc


def fecha_para_usuario(fecha_iso: str) -> str:
    try:
        return datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return fecha_iso or ""


def parsear_monto(texto: str, permitir_cero: bool = False) -> Decimal:
    valor = texto.strip().replace("$", "").replace(" ", "")
    if not valor:
        raise ValueError("Debes escribir un monto.")

    # Admite 1250.50, 1250,50, 1,250.50 y 1.250,50.
    if "," in valor and "." in valor:
        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "").replace(",", ".")
        else:
            valor = valor.replace(",", "")
    elif "," in valor:
        decimales = len(valor) - valor.rfind(",") - 1
        if decimales in (1, 2):
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")

    try:
        monto = Decimal(valor)
    except InvalidOperation as exc:
        raise ValueError("El monto debe ser un número válido.") from exc

    if not monto.is_finite():
        raise ValueError("El monto debe ser un número finito.")

    monto_entero = monto.to_integral_value()
    if monto != monto_entero:
        raise ValueError("El monto debe ser un número entero, sin centavos.")

    if monto < 0 or (not permitir_cero and monto == 0):
        raise ValueError("El monto debe ser mayor que cero.")

    return monto_entero


def decimal_a_float(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01")))


def formatear_moneda(valor: float | Decimal | int | None) -> str:
    numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    return f"${numero:,.2f}"


def entero_seguro(texto: str, nombre: str = "valor") -> int:
    try:
        return int(texto)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"El {nombre} no es válido.") from exc
