from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from config import CONDUCTORES_INICIALES, DB_PATH, asegurar_carpetas


class Conexion(sqlite3.Connection):
    """Conexión que también se cierra al salir de un bloque with."""

    def __exit__(self, exc_type, exc_value, traceback):
        resultado = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return resultado


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, factory=Conexion)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def transaccion() -> Iterator[sqlite3.Connection]:
    conn = conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _columnas(conn: sqlite3.Connection, tabla: str) -> set[str]:
    return {fila["name"] for fila in conn.execute(f"PRAGMA table_info({tabla})")}


def _agregar_columna_si_falta(
    conn: sqlite3.Connection,
    tabla: str,
    nombre: str,
    definicion: str,
) -> None:
    if nombre not in _columnas(conn, tabla):
        conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")


def inicializar_base_de_datos() -> None:
    asegurar_carpetas()

    with transaccion() as conn:
        # Se conservan los nombres y columnas principales del proyecto original
        # para facilitar el uso futuro de una base de datos existente.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now', 'localtime')),
                Conductor TEXT NOT NULL,
                Ingreso_Total REAL NOT NULL CHECK (Ingreso_Total >= 0),
                Parte_Triciclo REAL NOT NULL,
                Parte_Chofer REAL NOT NULL,
                Parte_Propietario REAL NOT NULL,
                Parte_Otro REAL NOT NULL DEFAULT 0,
                Tipo_Ingreso TEXT NOT NULL DEFAULT 'TRICICLO'
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now', 'localtime')),
                Monto REAL NOT NULL CHECK (Monto >= 0),
                Comentario TEXT
            )
            """
        )

        # Migraciones seguras para bases creadas con la versión anterior.
        _agregar_columna_si_falta(
            conn, "ingresos", "Es_Balance_Inicial", "INTEGER NOT NULL DEFAULT 0"
        )
        _agregar_columna_si_falta(conn, "ingresos", "Nota", "TEXT DEFAULT ''")
        _agregar_columna_si_falta(
            conn,
            "ingresos",
            "Creado_En",
            "TEXT NOT NULL DEFAULT ''",
        )
        _agregar_columna_si_falta(
            conn, "ingresos", "Parte_Otro", "REAL NOT NULL DEFAULT 0"
        )
        _agregar_columna_si_falta(
            conn,
            "ingresos",
            "Tipo_Ingreso",
            "TEXT NOT NULL DEFAULT 'TRICICLO'",
        )

        _agregar_columna_si_falta(
            conn, "gastos", "Categoria", "TEXT NOT NULL DEFAULT 'General'"
        )
        _agregar_columna_si_falta(
            conn,
            "gastos",
            "Creado_En",
            "TEXT NOT NULL DEFAULT ''",
        )

        # Reconoce el saldo inicial de una base creada por el proyecto original.
        conn.execute(
            """
            UPDATE ingresos
            SET Es_Balance_Inicial = 1
            WHERE Conductor = 'BALANCE INICIAL'
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conductores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
                Activo INTEGER NOT NULL DEFAULT 1,
                Creado_En TEXT NOT NULL DEFAULT (
                    strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracion (
                Clave TEXT PRIMARY KEY,
                Valor TEXT NOT NULL
            )
            """
        )

        for nombre in CONDUCTORES_INICIALES:
            conn.execute(
                "INSERT OR IGNORE INTO conductores (Nombre, Activo) VALUES (?, 1)",
                (nombre,),
            )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos(Fecha)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(Fecha)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ingresos_conductor ON ingresos(Conductor)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ingresos_tipo ON ingresos(Tipo_Ingreso)"
        )
