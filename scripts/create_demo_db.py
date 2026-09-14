"""Create the synthetic SQLite database used by the public portfolio demo."""
from __future__ import annotations

import sqlite3
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "demo.db"
MULTIPLE = Decimal("50")


def split_income(total: int) -> tuple[float, float, float]:
    amount = Decimal(total)
    driver = (
        (amount * Decimal("0.25") / MULTIPLE)
        .to_integral_value(rounding=ROUND_FLOOR)
        * MULTIPLE
    )
    owner = (
        (amount * Decimal("0.25") / MULTIPLE)
        .to_integral_value(rounding=ROUND_FLOOR)
        * MULTIPLE
    )
    vehicle = amount - driver - owner
    return float(vehicle), float(driver), float(owner)


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Fecha TEXT NOT NULL,
            Conductor TEXT NOT NULL,
            Ingreso_Total REAL NOT NULL CHECK (Ingreso_Total >= 0),
            Parte_Triciclo REAL NOT NULL,
            Parte_Chofer REAL NOT NULL,
            Parte_Propietario REAL NOT NULL,
            Parte_Otro REAL NOT NULL DEFAULT 0,
            Tipo_Ingreso TEXT NOT NULL DEFAULT 'TRICICLO',
            Es_Balance_Inicial INTEGER NOT NULL DEFAULT 0,
            Nota TEXT DEFAULT '',
            Creado_En TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Fecha TEXT NOT NULL,
            Monto REAL NOT NULL CHECK (Monto >= 0),
            Comentario TEXT,
            Categoria TEXT NOT NULL DEFAULT 'General',
            Creado_En TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE conductores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
            Activo INTEGER NOT NULL DEFAULT 1,
            Creado_En TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE configuracion (
            Clave TEXT PRIMARY KEY,
            Valor TEXT NOT NULL
        );

        CREATE INDEX idx_ingresos_fecha ON ingresos(Fecha);
        CREATE INDEX idx_gastos_fecha ON gastos(Fecha);
        CREATE INDEX idx_ingresos_conductor ON ingresos(Conductor);
        CREATE INDEX idx_ingresos_tipo ON ingresos(Tipo_Ingreso);
        """
    )

    for name, active in (
        ("Conductor 1", 1),
        ("Conductor 2", 1),
        ("Conductor 3", 0),
    ):
        conn.execute(
            "INSERT INTO conductores (Nombre, Activo, Creado_En) VALUES (?, ?, ?)",
            (name, active, "2026-01-01 08:00:00"),
        )

    conn.execute(
        """
        INSERT INTO ingresos (
            Fecha, Conductor, Ingreso_Total, Parte_Triciclo, Parte_Chofer,
            Parte_Propietario, Parte_Otro, Tipo_Ingreso, Es_Balance_Inicial,
            Nota, Creado_En
        ) VALUES (
            '2026-01-01', 'BALANCE INICIAL', 15000, 0, 0, 15000,
            0, 'TRICICLO', 1, 'Saldo inicial de demostración',
            '2026-01-01 08:00:00'
        )
        """
    )

    incomes = [
        ("2026-01-05", "Conductor 1", 8200, "Turno regular"),
        ("2026-01-08", "Conductor 2", 9600, ""),
        ("2026-01-18", "Conductor 1", 7450, ""),
        ("2026-02-03", "Conductor 2", 10100, ""),
        ("2026-02-11", "Conductor 1", 8900, ""),
        ("2026-02-22", "Conductor 2", 6800, ""),
        ("2026-03-02", "Conductor 1", 11250, ""),
        ("2026-03-14", "Conductor 2", 9300, ""),
        ("2026-03-28", "Conductor 1", 7700, ""),
        ("2026-04-06", "Conductor 2", 10450, ""),
        ("2026-04-15", "Conductor 1", 8600, ""),
        ("2026-04-26", "Conductor 2", 9850, ""),
        ("2026-05-04", "Conductor 1", 12100, ""),
        ("2026-05-13", "Conductor 2", 8150, ""),
        ("2026-05-25", "Conductor 1", 10900, ""),
        ("2026-06-07", "Conductor 2", 9400, ""),
        ("2026-06-16", "Conductor 1", 10200, ""),
        ("2026-06-29", "Conductor 2", 11750, ""),
        ("2026-07-05", "Conductor 1", 8800, ""),
        ("2026-07-12", "Conductor 2", 10600, ""),
        ("2026-07-24", "Conductor 1", 12500, ""),
        ("2026-08-03", "Conductor 2", 9700, ""),
        ("2026-08-14", "Conductor 1", 11400, ""),
        ("2026-08-27", "Conductor 2", 8350, ""),
        ("2026-09-02", "Conductor 1", 10800, ""),
        ("2026-09-07", "Conductor 2", 9200, ""),
        ("2026-09-11", "Conductor 1", 13150, "Semana de alta demanda"),
    ]
    for date, driver, total, note in incomes:
        vehicle, driver_share, owner = split_income(total)
        conn.execute(
            """
            INSERT INTO ingresos (
                Fecha, Conductor, Ingreso_Total, Parte_Triciclo,
                Parte_Chofer, Parte_Propietario, Parte_Otro, Tipo_Ingreso,
                Es_Balance_Inicial, Nota, Creado_En
            ) VALUES (?, ?, ?, ?, ?, ?, 0, 'TRICICLO', 0, ?, ?)
            """,
            (
                date,
                driver,
                total,
                vehicle,
                driver_share,
                owner,
                note,
                f"{date} 18:00:00",
            ),
        )

    for date, total, note in (
        ("2026-03-20", 3500, "Venta de accesorio usado"),
        ("2026-06-10", 5000, "Ingreso extraordinario de demostración"),
        ("2026-09-09", 2800, "Venta menor"),
    ):
        conn.execute(
            """
            INSERT INTO ingresos (
                Fecha, Conductor, Ingreso_Total, Parte_Triciclo,
                Parte_Chofer, Parte_Propietario, Parte_Otro, Tipo_Ingreso,
                Es_Balance_Inicial, Nota, Creado_En
            ) VALUES (?, '', ?, 0, 0, 0, ?, 'OTRO', 0, ?, ?)
            """,
            (date, total, total, note, f"{date} 12:00:00"),
        )

    expenses = [
        ("2026-01-10", 1800, "Mantenimiento", "Servicio preventivo"),
        ("2026-01-22", 950, "General", "Insumos operativos"),
        ("2026-02-15", 2600, "Piezas", "Cambio de pieza de desgaste"),
        ("2026-03-08", 1200, "Batería / Electricidad", "Revisión eléctrica"),
        ("2026-03-25", 700, "General", "Limpieza y consumibles"),
        ("2026-04-18", 3200, "Reparación", "Reparación menor"),
        ("2026-05-09", 1450, "Documentación", "Trámite administrativo"),
        ("2026-05-21", 900, "General", "Insumos"),
        ("2026-06-19", 2750, "Mantenimiento", "Mantenimiento programado"),
        ("2026-07-16", 4100, "Piezas", "Repuesto mecánico"),
        ("2026-08-08", 1600, "General", "Gastos operativos"),
        ("2026-08-30", 2200, "Reparación", "Ajuste y reparación"),
        ("2026-09-06", 1950, "Mantenimiento", "Servicio preventivo"),
    ]
    for date, total, category, note in expenses:
        conn.execute(
            """
            INSERT INTO gastos (Fecha, Monto, Comentario, Categoria, Creado_En)
            VALUES (?, ?, ?, ?, ?)
            """,
            (date, total, note, category, f"{date} 20:00:00"),
        )

    conn.commit()
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    print(f"Demo database created: {DB_PATH}")
    print(f"Integrity check: {result}")


if __name__ == "__main__":
    main()
