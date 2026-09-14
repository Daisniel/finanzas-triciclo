from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

APP_NAME = "Finanzas del Triciclo"
APP_VERSION = "2.3.0"

# La base de datos se guarda SIEMPRE junto al script durante el desarrollo
# y junto al .exe cuando la aplicación está compilada con PyInstaller.
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

DB_PATH = APP_DIR / "renta_triciclo.db"
BACKUP_DIR = APP_DIR / "backups"
EXPORT_DIR = APP_DIR / "reportes"

# Reglas del negocio originales. No se modifican.
PORCENTAJE_CHOFER = Decimal("0.25")
PORCENTAJE_PROPIETARIO = Decimal("0.25")
MULTIPLO_REDONDEO = Decimal("50")
ANIO_INICIO_CONTROL = 2026

# Tipos de ingreso almacenados en la tabla común de movimientos.
TIPO_INGRESO_TRICICLO = "TRICICLO"
TIPO_INGRESO_OTRO = "OTRO"

CONDUCTORES_INICIALES = ("Conductor 1", "Conductor 2")
CATEGORIAS_GASTO = (
    "General",
    "Reparación",
    "Mantenimiento",
    "Batería / Electricidad",
    "Piezas",
    "Documentación",
    "Otros",
)

COLORES = {
    "fondo": "#111827",
    "sidebar": "#0B1220",
    "superficie": "#1F2937",
    "superficie_2": "#273449",
    "borde": "#374151",
    "texto": "#F3F4F6",
    "texto_secundario": "#9CA3AF",
    "acento": "#3B82F6",
    "acento_hover": "#2563EB",
    "exito": "#22C55E",
    "peligro": "#EF4444",
    "advertencia": "#F59E0B",
    "ingreso_fila": "#143423",
    "gasto_fila": "#3B1D24",
    "mes_actual": "#176B3A",
}

FUENTE = "Segoe UI"
AUMENTO_FUENTE = 1  # Sube toda la interfaz un punto para mejorar la lectura.


def asegurar_carpetas() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
