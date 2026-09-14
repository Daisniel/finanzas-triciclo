from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "demo.db"
DEST = ROOT / "renta_triciclo.db"
BACKUP_DIR = ROOT / "backups"

if not SOURCE.exists():
    raise SystemExit("No se encontró data/demo.db")

if DEST.exists():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup = BACKUP_DIR / f"renta_triciclo_before_demo_{stamp}.db"
    shutil.copy2(DEST, backup)
    print(f"Copia de seguridad creada: {backup}")

shutil.copy2(SOURCE, DEST)
print(f"Base demo restaurada: {DEST}")
