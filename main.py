from __future__ import annotations

import traceback
from tkinter import messagebox

from database import inicializar_base_de_datos
from ui import AppFinanzas


def main() -> None:
    try:
        inicializar_base_de_datos()
        app = AppFinanzas()
        app.mainloop()
    except Exception as exc:
        traceback.print_exc()
        try:
            messagebox.showerror(
                "Error inesperado",
                f"La aplicación no pudo iniciarse:\n\n{exc}",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
