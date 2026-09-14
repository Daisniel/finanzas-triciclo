from __future__ import annotations

import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from decimal import Decimal
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable

from config import (
    ANIO_INICIO_CONTROL,
    APP_NAME,
    APP_VERSION,
    AUMENTO_FUENTE,
    CATEGORIAS_GASTO,
    COLORES,
    DB_PATH,
    FUENTE,
    MULTIPLO_REDONDEO,
    PORCENTAJE_CHOFER,
    PORCENTAJE_PROPIETARIO,
    TIPO_INGRESO_OTRO,
    TIPO_INGRESO_TRICICLO,
)
from services import (
    actualizar_gasto,
    actualizar_ingreso,
    agregar_conductor,
    calcular_reparto,
    cambiar_estado_conductor,
    crear_copia_seguridad,
    exportar_base_datos,
    eliminar_registro,
    exportar_excel,
    importar_base_datos,
    existe_balance_inicial,
    obtener_conductores,
    obtener_estadisticas_globales,
    obtener_estadisticas_mes,
    obtener_ganancia_conductor,
    obtener_movimientos,
    obtener_registro,
    obtener_resumen_anual,
    registrar_balance_inicial,
    registrar_gasto,
    registrar_ingreso,
    registrar_otro_ingreso,
)
from utils import (
    fecha_hoy_usuario,
    fecha_para_usuario,
    formatear_moneda,
    normalizar_fecha,
    parsear_monto,
)


def obtener_ruta_recurso(nombre_archivo: str) -> Path:
    """
    Devuelve la ruta correcta de un recurso tanto en Visual Studio Code
    como dentro de una aplicación compilada con PyInstaller.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / nombre_archivo

    return Path(__file__).resolve().parent / nombre_archivo


MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

NOMBRE_TIPO_INGRESO = {
    TIPO_INGRESO_TRICICLO: "Trabajo del triciclo",
    TIPO_INGRESO_OTRO: "Otro ingreso",
}
TIPOS_INGRESO = list(NOMBRE_TIPO_INGRESO.values())


def tipo_ingreso_desde_nombre(nombre: str) -> str:
    for tipo, etiqueta in NOMBRE_TIPO_INGRESO.items():
        if etiqueta == nombre:
            return tipo
    return TIPO_INGRESO_TRICICLO


def nombre_tipo_ingreso(tipo: str | None) -> str:
    return NOMBRE_TIPO_INGRESO.get(tipo or TIPO_INGRESO_TRICICLO, "Trabajo del triciclo")


def fuente(tamano: int, *estilos: str) -> tuple:
    """Devuelve una fuente ampliada de forma uniforme en toda la interfaz."""
    return (FUENTE, tamano + AUMENTO_FUENTE, *estilos)


def lista_anios() -> list[str]:
    """Muestra los años desde que comenzó el control y añade el siguiente."""
    anio_actual = date.today().year
    anio_final = max(anio_actual + 1, ANIO_INICIO_CONTROL)
    return [str(y) for y in range(ANIO_INICIO_CONTROL, anio_final + 1)]


class AyudaEmergente:
    """Muestra una explicación breve al dejar el puntero sobre un control."""

    def __init__(self, widget: tk.Widget, texto: str, demora: int = 550) -> None:
        self.widget = widget
        self.texto = texto
        self.demora = demora
        self._tarea: str | None = None
        self._ventana: tk.Toplevel | None = None
        self._vincular(widget)
        setattr(widget, "_ayuda_emergente", self)

    def _vincular(self, widget: tk.Widget) -> None:
        widget.bind("<Enter>", self._programar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")
        widget.bind("<ButtonPress>", self._ocultar, add="+")
        for hijo in widget.winfo_children():
            self._vincular(hijo)

    def _programar(self, _evento=None) -> None:
        self._cancelar_tarea()
        self._tarea = self.widget.after(self.demora, self._mostrar)

    def _cancelar_tarea(self) -> None:
        if self._tarea is not None:
            self.widget.after_cancel(self._tarea)
            self._tarea = None

    def _mostrar(self) -> None:
        if self._ventana is not None or not self.texto:
            return
        x = self.widget.winfo_pointerx() + 16
        y = self.widget.winfo_pointery() + 18
        self._ventana = tk.Toplevel(self.widget)
        self._ventana.wm_overrideredirect(True)
        self._ventana.wm_geometry(f"+{x}+{y}")
        etiqueta = tk.Label(
            self._ventana,
            text=self.texto,
            justify="left",
            wraplength=380,
            bg="#FFF7D6",
            fg="#1F2937",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=8,
            font=fuente(9),
        )
        etiqueta.pack()

    def _ocultar(self, _evento=None) -> None:
        self._cancelar_tarea()
        if self._ventana is not None:
            self._ventana.destroy()
            self._ventana = None


class AyudaEncabezadosTreeview:
    """Ayuda emergente para los encabezados de una tabla Treeview."""

    def __init__(self, tree: ttk.Treeview, descripciones: dict[str, str]) -> None:
        self.tree = tree
        self.descripciones = descripciones
        self._columna_actual: str | None = None
        self._ayuda: AyudaEmergente | None = None
        self._tarea: str | None = None
        self._ventana: tk.Toplevel | None = None
        setattr(tree, "_ayuda_encabezados", self)
        tree.bind("<Motion>", self._movimiento, add="+")
        tree.bind("<Leave>", self._ocultar, add="+")

    def _movimiento(self, evento) -> None:
        if self.tree.identify_region(evento.x, evento.y) != "heading":
            self._ocultar()
            return

        identificador = self.tree.identify_column(evento.x)
        try:
            indice = int(identificador.removeprefix("#")) - 1
            columna = str(self.tree["columns"][indice])
        except (ValueError, IndexError):
            self._ocultar()
            return

        if columna == self._columna_actual:
            return

        self._ocultar()
        self._columna_actual = columna
        if columna in self.descripciones:
            self._tarea = self.tree.after(550, lambda: self._mostrar(columna))

    def _mostrar(self, columna: str) -> None:
        texto = self.descripciones.get(columna, "")
        if not texto:
            return
        x = self.tree.winfo_pointerx() + 16
        y = self.tree.winfo_pointery() + 18
        self._ventana = tk.Toplevel(self.tree)
        self._ventana.wm_overrideredirect(True)
        self._ventana.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._ventana,
            text=texto,
            justify="left",
            wraplength=400,
            bg="#FFF7D6",
            fg="#1F2937",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=8,
            font=fuente(9),
        ).pack()

    def _ocultar(self, _evento=None) -> None:
        if self._tarea is not None:
            self.tree.after_cancel(self._tarea)
            self._tarea = None
        if self._ventana is not None:
            self._ventana.destroy()
            self._ventana = None
        self._columna_actual = None


class AppFinanzas(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self._configurar_icono()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1360x820")
        self.minsize(1120, 680)
        self.configure(bg=COLORES["fondo"])

        self._configurar_estilos()
        self._crear_layout()
        self._crear_paginas()
        self._configurar_atajos()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(100, self._comprobar_primera_ejecucion)
        self.after(200, lambda: self.mostrar_pagina("inicio"))


    def _configurar_icono(self) -> None:
        """Configura el icono de la ventana y de la barra de tareas."""
        try:
            ruta_icono = obtener_ruta_recurso("logo.ico")
            if ruta_icono.exists():
                self.iconbitmap(str(ruta_icono))

            if sys.platform == "win32":
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "triciclo.finanzas.negocio.v2"
                )
        except Exception as exc:
            print(f"No se pudo cargar el icono: {exc}")

    def _configurar_estilos(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("App.TFrame", background=COLORES["fondo"])
        style.configure("Sidebar.TFrame", background=COLORES["sidebar"])
        style.configure("Surface.TFrame", background=COLORES["superficie"])
        style.configure("Surface2.TFrame", background=COLORES["superficie_2"])

        style.configure(
            "App.TLabel",
            background=COLORES["fondo"],
            foreground=COLORES["texto"],
            font=fuente(10),
        )
        style.configure(
            "Muted.TLabel",
            background=COLORES["fondo"],
            foreground=COLORES["texto_secundario"],
            font=fuente(9),
        )
        style.configure(
            "Surface.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["texto"],
            font=fuente(10),
        )
        style.configure(
            "SurfaceMuted.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["texto_secundario"],
            font=fuente(9),
        )
        style.configure(
            "PageTitle.TLabel",
            background=COLORES["fondo"],
            foreground=COLORES["texto"],
            font=fuente(22, "bold"),
        )
        style.configure(
            "CardValue.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["texto"],
            font=fuente(22, "bold"),
        )
        style.configure(
            "CardTitle.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["texto_secundario"],
            font=fuente(10, "bold"),
        )
        style.configure(
            "SuccessValue.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["exito"],
            font=fuente(22, "bold"),
        )
        style.configure(
            "DangerValue.TLabel",
            background=COLORES["superficie"],
            foreground=COLORES["peligro"],
            font=fuente(22, "bold"),
        )

        style.configure(
            "Primary.TButton",
            background=COLORES["acento"],
            foreground="white",
            borderwidth=0,
            padding=(14, 9),
            font=fuente(10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", COLORES["acento_hover"])],
        )

        style.configure(
            "Secondary.TButton",
            background=COLORES["superficie_2"],
            foreground=COLORES["texto"],
            borderwidth=0,
            padding=(12, 8),
            font=fuente(10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", COLORES["borde"])],
        )

        style.configure(
            "Danger.TButton",
            background=COLORES["peligro"],
            foreground="white",
            borderwidth=0,
            padding=(12, 8),
            font=fuente(10, "bold"),
        )

        style.configure(
            "Sidebar.TButton",
            background=COLORES["sidebar"],
            foreground=COLORES["texto_secundario"],
            borderwidth=0,
            padding=(18, 13),
            anchor="w",
            font=fuente(10),
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", COLORES["superficie"])],
            foreground=[("active", COLORES["texto"])],
        )
        style.configure(
            "SidebarActive.TButton",
            background=COLORES["acento"],
            foreground="white",
            borderwidth=0,
            padding=(18, 13),
            anchor="w",
            font=fuente(10, "bold"),
        )

        style.configure(
            "App.TEntry",
            fieldbackground=COLORES["superficie_2"],
            foreground=COLORES["texto"],
            insertcolor=COLORES["texto"],
            bordercolor=COLORES["borde"],
            lightcolor=COLORES["borde"],
            darkcolor=COLORES["borde"],
            padding=8,
        )
        style.configure(
            "App.TCombobox",
            fieldbackground=COLORES["superficie_2"],
            background=COLORES["superficie_2"],
            foreground=COLORES["texto"],
            arrowcolor=COLORES["texto"],
            bordercolor=COLORES["borde"],
            padding=6,
        )
        style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COLORES["superficie_2"])],
            foreground=[("readonly", COLORES["texto"])],
            selectbackground=[("readonly", COLORES["superficie_2"])],
            selectforeground=[("readonly", COLORES["texto"])],
        )

        style.configure(
            "App.Treeview",
            background=COLORES["superficie"],
            fieldbackground=COLORES["superficie"],
            foreground=COLORES["texto"],
            rowheight=34,
            borderwidth=0,
            font=fuente(9),
        )
        style.configure(
            "App.Treeview.Heading",
            background=COLORES["superficie_2"],
            foreground=COLORES["texto"],
            relief="flat",
            font=fuente(9, "bold"),
            padding=7,
        )
        style.map(
            "App.Treeview",
            background=[("selected", COLORES["acento"])],
            foreground=[("selected", "white")],
        )

        style.configure(
            "App.TCheckbutton",
            background=COLORES["fondo"],
            foreground=COLORES["texto"],
            font=fuente(10),
        )

    def _crear_layout(self) -> None:
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=235)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        marca = tk.Frame(self.sidebar, bg=COLORES["sidebar"], height=92)
        marca.pack(fill="x")
        marca.pack_propagate(False)

        tk.Label(
            marca,
            text="TRICICLO",
            bg=COLORES["sidebar"],
            fg=COLORES["texto"],
            font=fuente(17, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 0))
        tk.Label(
            marca,
            text="Control financiero",
            bg=COLORES["sidebar"],
            fg=COLORES["texto_secundario"],
            font=fuente(9),
        ).pack(anchor="w", padx=20, pady=(2, 0))

        self.botones_menu: dict[str, ttk.Button] = {}
        opciones = [
            ("inicio", "  Inicio"),
            ("nuevo", "  Nuevo movimiento"),
            ("movimientos", "  Movimientos"),
            ("resumen", "  Resumen anual"),
            ("configuracion", "  Configuración"),
        ]
        for clave, texto in opciones:
            boton = ttk.Button(
                self.sidebar,
                text=texto,
                style="Sidebar.TButton",
                command=lambda c=clave: self.mostrar_pagina(c),
            )
            boton.pack(fill="x", padx=10, pady=3)
            self.botones_menu[clave] = boton

        ttk.Label(
            self.sidebar,
            text=f"Versión {APP_VERSION}",
            style="SurfaceMuted.TLabel",
        ).pack(side="bottom", anchor="w", padx=20, pady=18)

        self.area = ttk.Frame(self, style="App.TFrame")
        self.area.pack(side="left", expand=True, fill="both")

        self.contenedor_paginas = ttk.Frame(self.area, style="App.TFrame")
        self.contenedor_paginas.pack(expand=True, fill="both")

        self.status_var = tk.StringVar(value="Listo")
        barra = tk.Label(
            self.area,
            textvariable=self.status_var,
            bg=COLORES["superficie"],
            fg=COLORES["texto_secundario"],
            anchor="w",
            padx=14,
            pady=6,
            font=fuente(9),
        )
        barra.pack(side="bottom", fill="x")

    def _crear_paginas(self) -> None:
        self.paginas: dict[str, PaginaBase] = {
            "inicio": PaginaInicio(self.contenedor_paginas, self),
            "nuevo": PaginaNuevoMovimiento(self.contenedor_paginas, self),
            "movimientos": PaginaMovimientos(self.contenedor_paginas, self),
            "resumen": PaginaResumenAnual(self.contenedor_paginas, self),
            "configuracion": PaginaConfiguracion(self.contenedor_paginas, self),
        }
        for pagina in self.paginas.values():
            pagina.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _configurar_atajos(self) -> None:
        self.bind_all("<Control-i>", lambda _e: self.mostrar_pagina("nuevo"))
        self.bind_all("<Control-g>", lambda _e: self.mostrar_pagina("nuevo", "gasto"))
        self.bind_all("<Control-f>", lambda _e: self.mostrar_pagina("movimientos"))
        self.bind_all("<F5>", lambda _e: self.refrescar_todo())

    def _comprobar_primera_ejecucion(self) -> None:
        if existe_balance_inicial():
            return

        monto = simpledialog.askstring(
            "Primera ejecución",
            "Introduce el monto inicial disponible.\n\n"
            "Este registro se guardará como saldo inicial y se asignará "
            "completamente al propietario.",
            parent=self,
        )
        if monto is None:
            messagebox.showwarning(
                "Configuración cancelada",
                "El saldo inicial es obligatorio. La aplicación se cerrará.",
                parent=self,
            )
            self.destroy()
            return

        try:
            valor = parsear_monto(monto, permitir_cero=True)
            registrar_balance_inicial(date.today().isoformat(), valor)
            self.notificar("Saldo inicial registrado correctamente.")
            self.refrescar_todo()
        except ValueError as exc:
            messagebox.showerror("Dato incorrecto", str(exc), parent=self)
            self.after(200, self._comprobar_primera_ejecucion)

    def mostrar_pagina(self, nombre: str, modo: str | None = None) -> None:
        pagina = self.paginas[nombre]
        pagina.tkraise()
        pagina.al_mostrar()

        if nombre == "nuevo" and modo:
            pagina.seleccionar_modo(modo)

        for clave, boton in self.botones_menu.items():
            boton.configure(
                style="SidebarActive.TButton" if clave == nombre else "Sidebar.TButton"
            )

    def refrescar_todo(self) -> None:
        for pagina in self.paginas.values():
            pagina.refrescar()

    def notificar(self, mensaje: str) -> None:
        self.status_var.set(mensaje)
        self.after(4500, lambda: self.status_var.set("Listo"))

    def _cerrar(self) -> None:
        self.destroy()


class PaginaBase(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app

    def al_mostrar(self) -> None:
        self.refrescar()

    def refrescar(self) -> None:
        pass

    def encabezado(self, titulo: str, subtitulo: str = "") -> ttk.Frame:
        frame = ttk.Frame(self, style="App.TFrame")
        frame.pack(fill="x", padx=28, pady=(24, 16))
        ttk.Label(frame, text=titulo, style="PageTitle.TLabel").pack(anchor="w")
        if subtitulo:
            ttk.Label(frame, text=subtitulo, style="Muted.TLabel").pack(
                anchor="w", pady=(4, 0)
            )
        return frame


class Tarjeta(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        titulo: str,
        valor: tk.StringVar,
        estilo_valor: str = "CardValue.TLabel",
        detalle: tk.StringVar | None = None,
        ayuda: str | None = None,
    ) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=18)
        ttk.Label(self, text=titulo, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(self, textvariable=valor, style=estilo_valor).pack(
            anchor="w", pady=(6, 2)
        )
        if detalle is not None:
            ttk.Label(
                self, textvariable=detalle, style="SurfaceMuted.TLabel"
            ).pack(anchor="w")
        if ayuda:
            AyudaEmergente(self, ayuda)


class PaginaInicio(PaginaBase):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, app)
        cabecera = self.encabezado(
            "Inicio",
            "Resumen del negocio y movimientos recientes.",
        )
        ttk.Button(
            cabecera,
            text="+ Ingreso",
            style="Primary.TButton",
            command=lambda: app.mostrar_pagina("nuevo", "ingreso"),
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            cabecera,
            text="+ Gasto",
            style="Secondary.TButton",
            command=lambda: app.mostrar_pagina("nuevo", "gasto"),
        ).pack(side="right")

        self.vars = {
            "balance": tk.StringVar(value="$0.00"),
            "ingresos_mes": tk.StringVar(value="$0.00"),
            "gastos_mes": tk.StringVar(value="$0.00"),
            "resultado_mes": tk.StringVar(value="$0.00"),
            "triciclo": tk.StringVar(value="$0.00"),
            "propietario": tk.StringVar(value="$0.00"),
            "otros": tk.StringVar(value="$0.00"),
            "choferes": tk.StringVar(value="$0.00"),
        }

        cards = ttk.Frame(self, style="App.TFrame")
        cards.pack(fill="x", padx=28)
        for col in range(4):
            cards.grid_columnconfigure(col, weight=1, uniform="cards")

        Tarjeta(
            cards,
            "Balance disponible",
            self.vars["balance"],
            "SuccessValue.TLabel",
            ayuda=(
                "Dinero disponible del negocio: parte acumulada del triciclo "
                "más parte del propietario y otros ingresos completos, incluido "
                "el saldo inicial, menos todos los gastos registrados. Los "
                "salarios ya se separan al registrar cada ingreso."
            ),
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        Tarjeta(
            cards,
            "Ingresos del mes",
            self.vars["ingresos_mes"],
            ayuda=(
                "Suma de todos los ingresos brutos registrados durante el mes "
                "actual, antes de repartir las partes del conductor, propietario "
                "y triciclo."
            ),
        ).grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        Tarjeta(
            cards,
            "Gastos del mes",
            self.vars["gastos_mes"],
            "DangerValue.TLabel",
            ayuda="Suma de todos los gastos registrados durante el mes actual.",
        ).grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        Tarjeta(
            cards,
            "Resultado del mes",
            self.vars["resultado_mes"],
            ayuda=(
                "Dinero disponible generado este mes por el triciclo y por otros "
                "ingresos, más la parte del propietario, menos los gastos del "
                "mismo mes. No incluye el saldo acumulado ni los salarios."
            ),
        ).grid(row=0, column=3, sticky="nsew", padx=(8, 0), pady=8)

        secundarias = ttk.Frame(self, style="App.TFrame")
        secundarias.pack(fill="x", padx=28)
        for col in range(4):
            secundarias.grid_columnconfigure(col, weight=1, uniform="secondary")

        Tarjeta(
            secundarias,
            "Acumulado del triciclo",
            self.vars["triciclo"],
            ayuda=(
                "Suma histórica de todas las partes asignadas al triciclo. Es el "
                "resto que queda después de separar las partes redondeadas del "
                "conductor y del propietario."
            ),
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        Tarjeta(
            secundarias,
            "Acumulado del propietario",
            self.vars["propietario"],
            ayuda=(
                "Suma histórica de la parte del propietario en cada ingreso, más "
                "el saldo inicial registrado en la primera ejecución."
            ),
        ).grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        Tarjeta(
            secundarias,
            "Otros ingresos acumulados",
            self.vars["otros"],
            ayuda=(
                "Suma de los ingresos que no provienen del trabajo del triciclo. "
                "Se consideran disponibles completos y no generan salario."
            ),
        ).grid(row=0, column=2, sticky="nsew", padx=8, pady=8)
        Tarjeta(
            secundarias,
            "Salarios acumulados",
            self.vars["choferes"],
            ayuda=(
                "Suma de las partes asignadas a todos los conductores en los "
                "ingresos registrados. No forma parte del balance disponible."
            ),
        ).grid(row=0, column=3, sticky="nsew", padx=(8, 0), pady=8)

        consulta = ttk.Frame(self, style="Surface.TFrame", padding=14)
        consulta.pack(fill="x", padx=28, pady=(8, 0))

        ttk.Label(
            consulta,
            text="Ganancia por conductor",
            style="CardTitle.TLabel",
        ).pack(side="left", padx=(0, 18))

        self.sal_conductor = ttk.Combobox(
            consulta,
            state="readonly",
            width=15,
            style="App.TCombobox",
        )
        self.sal_conductor.pack(side="left", padx=(0, 8))

        self.sal_mes = ttk.Combobox(
            consulta,
            values=MESES,
            state="readonly",
            width=12,
            style="App.TCombobox",
        )
        self.sal_mes.set(MESES[date.today().month - 1])
        self.sal_mes.pack(side="left", padx=(0, 8))

        self.sal_anio = ttk.Combobox(
            consulta,
            values=lista_anios(),
            state="readonly",
            width=7,
            style="App.TCombobox",
        )
        self.sal_anio.set(str(date.today().year))
        self.sal_anio.pack(side="left", padx=(0, 16))

        self.salario_conductor_var = tk.StringVar(value="$0.00")
        self.salario_detalle_var = tk.StringVar(value="Sin movimientos")

        tk.Label(
            consulta,
            textvariable=self.salario_conductor_var,
            bg=COLORES["superficie"],
            fg=COLORES["exito"],
            font=fuente(17, "bold"),
        ).pack(side="left", padx=(0, 12))
        ttk.Label(
            consulta,
            textvariable=self.salario_detalle_var,
            style="SurfaceMuted.TLabel",
        ).pack(side="left")

        for combo in (self.sal_conductor, self.sal_mes, self.sal_anio):
            combo.bind(
                "<<ComboboxSelected>>",
                lambda _e: self._actualizar_ganancia_conductor(),
            )

        AyudaEmergente(
            consulta,
            "Muestra la parte del chofer asignada al conductor seleccionado "
            "durante el mes y año elegidos. También indica cuántos ingresos "
            "trabajó y cuánto dinero bruto generaron esos registros.",
        )

        inferior = ttk.Frame(self, style="App.TFrame")
        inferior.pack(expand=True, fill="both", padx=28, pady=(10, 24))
        inferior.grid_columnconfigure(0, weight=3)
        inferior.grid_columnconfigure(1, weight=2)
        inferior.grid_rowconfigure(0, weight=1)

        frame_tabla = ttk.Frame(inferior, style="Surface.TFrame", padding=14)
        frame_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(
            frame_tabla, text="Últimos movimientos", style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 10))

        columnas = ("fecha", "tipo", "detalle", "monto")
        self.tree = ttk.Treeview(
            frame_tabla,
            columns=columnas,
            show="headings",
            style="App.Treeview",
            height=8,
        )
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("detalle", text="Detalle")
        self.tree.heading("monto", text="Monto")
        self.tree.column("fecha", width=90, anchor="center")
        self.tree.column("tipo", width=75, anchor="center")
        self.tree.column("detalle", width=240)
        self.tree.column("monto", width=105, anchor="e")
        self.tree.pack(expand=True, fill="both")
        self.tree.tag_configure("ingreso", background=COLORES["ingreso_fila"])
        self.tree.tag_configure("gasto", background=COLORES["gasto_fila"])

        frame_grafica = ttk.Frame(inferior, style="Surface.TFrame", padding=14)
        frame_grafica.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(
            frame_grafica, text="Ingresos y gastos del año", style="CardTitle.TLabel"
        ).pack(anchor="w")
        self.canvas = tk.Canvas(
            frame_grafica,
            bg=COLORES["superficie"],
            highlightthickness=0,
            height=245,
        )
        self.canvas.pack(expand=True, fill="both", pady=(10, 0))
        self.canvas.bind("<Configure>", lambda _e: self._dibujar_grafica())

    def refrescar(self) -> None:
        stats = obtener_estadisticas_globales()
        ahora = date.today()
        mes = obtener_estadisticas_mes(ahora.year, ahora.month)

        self.vars["balance"].set(formatear_moneda(stats["balance"]))
        self.vars["ingresos_mes"].set(formatear_moneda(mes["ingresos"]))
        self.vars["gastos_mes"].set(formatear_moneda(mes["gastos"]))
        self.vars["resultado_mes"].set(formatear_moneda(mes["resultado"]))
        self.vars["triciclo"].set(formatear_moneda(stats["total_triciclo"]))
        self.vars["propietario"].set(formatear_moneda(stats["total_propietario"]))
        self.vars["otros"].set(formatear_moneda(stats["total_otros"]))
        self.vars["choferes"].set(formatear_moneda(stats["total_chofer"]))

        conductores = obtener_conductores(solo_activos=False)
        self.sal_conductor.configure(values=conductores)
        if conductores and self.sal_conductor.get() not in conductores:
            self.sal_conductor.set(conductores[0])
        anios_disponibles = lista_anios()
        self.sal_anio.configure(values=anios_disponibles)
        if self.sal_anio.get() not in anios_disponibles:
            self.sal_anio.set(str(date.today().year))
        self._actualizar_ganancia_conductor()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for mov in obtener_movimientos(limite=8):
            monto = mov["Entrada"] if mov["Tipo"] == "Ingreso" else mov["Gastos"]
            detalle = mov["Conductor"] or mov["Detalle"]
            self.tree.insert(
                "",
                "end",
                values=(
                    fecha_para_usuario(mov["Fecha"]),
                    mov["Tipo"],
                    detalle,
                    formatear_moneda(monto),
                ),
                tags=(mov["Tipo"].lower(),),
            )

        self._dibujar_grafica()

    def _actualizar_ganancia_conductor(self) -> None:
        conductor = self.sal_conductor.get()
        if not conductor:
            self.salario_conductor_var.set("$0.00")
            self.salario_detalle_var.set("No hay conductores registrados")
            return

        try:
            anio = int(self.sal_anio.get())
            mes = MESES.index(self.sal_mes.get()) + 1
        except (ValueError, TypeError):
            return

        datos = obtener_ganancia_conductor(conductor, anio, mes)
        self.salario_conductor_var.set(formatear_moneda(datos["salario"]))

        cantidad = int(datos["registros"])
        palabra = "ingreso" if cantidad == 1 else "ingresos"
        self.salario_detalle_var.set(
            f"{cantidad} {palabra} · Bruto generado: "
            f"{formatear_moneda(datos['ingreso_bruto'])}"
        )

    def _dibujar_grafica(self) -> None:
        if not self.winfo_exists():
            return
        canvas = self.canvas
        canvas.delete("all")
        ancho = max(canvas.winfo_width(), 300)
        alto = max(canvas.winfo_height(), 220)
        resumen = obtener_resumen_anual(date.today().year)
        maximo = max(
            [float(r["ingreso_bruto"]) for r in resumen]
            + [float(r["gastos"]) for r in resumen]
            + [1.0]
        )

        margen_x, margen_y = 28, 28
        base = alto - 34
        espacio = (ancho - 2 * margen_x) / 12
        ancho_barra = max(4, espacio * 0.25)

        canvas.create_line(
            margen_x, base, ancho - margen_x, base, fill=COLORES["borde"]
        )

        for i, fila in enumerate(resumen):
            centro = margen_x + espacio * i + espacio / 2
            h_ing = (float(fila["ingreso_bruto"]) / maximo) * (alto - 80)
            h_gas = (float(fila["gastos"]) / maximo) * (alto - 80)

            canvas.create_rectangle(
                centro - ancho_barra - 1,
                base - h_ing,
                centro - 1,
                base,
                fill=COLORES["acento"],
                outline="",
            )
            canvas.create_rectangle(
                centro + 1,
                base - h_gas,
                centro + ancho_barra + 1,
                base,
                fill=COLORES["peligro"],
                outline="",
            )
            canvas.create_text(
                centro,
                base + 12,
                text=MESES[i][:3],
                fill=COLORES["texto_secundario"],
                font=fuente(8),
            )

        canvas.create_rectangle(
            margen_x, 8, margen_x + 10, 18, fill=COLORES["acento"], outline=""
        )
        canvas.create_text(
            margen_x + 16,
            13,
            text="Ingresos",
            fill=COLORES["texto_secundario"],
            anchor="w",
            font=fuente(8),
        )
        canvas.create_rectangle(
            margen_x + 78,
            8,
            margen_x + 88,
            18,
            fill=COLORES["peligro"],
            outline="",
        )
        canvas.create_text(
            margen_x + 94,
            13,
            text="Gastos",
            fill=COLORES["texto_secundario"],
            anchor="w",
            font=fuente(8),
        )


class PaginaNuevoMovimiento(PaginaBase):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, app)
        self.encabezado(
            "Nuevo movimiento",
            "Registra ingresos y gastos con una vista previa antes de guardar.",
        )

        selector = ttk.Frame(self, style="App.TFrame")
        selector.pack(fill="x", padx=28)
        self.btn_ingreso = ttk.Button(
            selector,
            text="Ingreso",
            style="Primary.TButton",
            command=lambda: self.seleccionar_modo("ingreso"),
        )
        self.btn_ingreso.pack(side="left")
        self.btn_gasto = ttk.Button(
            selector,
            text="Gasto",
            style="Secondary.TButton",
            command=lambda: self.seleccionar_modo("gasto"),
        )
        self.btn_gasto.pack(side="left", padx=8)

        self.contenido = ttk.Frame(self, style="App.TFrame")
        self.contenido.pack(expand=True, fill="both", padx=28, pady=18)

        self.modo = "ingreso"
        self._crear_formulario_ingreso()
        self._crear_formulario_gasto()
        self.seleccionar_modo("ingreso")

    def _crear_formulario_ingreso(self) -> None:
        self.frame_ingreso = ttk.Frame(
            self.contenido, style="Surface.TFrame", padding=24
        )
        self.frame_ingreso.columnconfigure(0, weight=3)
        self.frame_ingreso.columnconfigure(1, weight=2)
        self.frame_ingreso.rowconfigure(0, weight=1)

        formulario = ttk.Frame(self.frame_ingreso, style="Surface.TFrame")
        formulario.grid(row=0, column=0, sticky="nsew", padx=(0, 28))

        ttk.Label(formulario, text="Fecha", style="Surface.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.ing_fecha = ttk.Entry(formulario, style="App.TEntry", width=24)
        self.ing_fecha.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.ing_fecha.insert(0, fecha_hoy_usuario())

        ttk.Label(formulario, text="Tipo de ingreso", style="Surface.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.ing_tipo = ttk.Combobox(
            formulario,
            values=TIPOS_INGRESO,
            state="readonly",
            style="App.TCombobox",
        )
        self.ing_tipo.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self.ing_tipo.set(nombre_tipo_ingreso(TIPO_INGRESO_TRICICLO))
        self.ing_tipo.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._actualizar_tipo_ingreso(),
        )

        self.lbl_ing_conductor = ttk.Label(
            formulario, text="Conductor", style="Surface.TLabel"
        )
        self.lbl_ing_conductor.grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.ing_conductor = ttk.Combobox(
            formulario, state="readonly", style="App.TCombobox"
        )
        self.ing_conductor.grid(row=5, column=0, sticky="ew", pady=(0, 16))

        self.lbl_ing_monto = ttk.Label(
            formulario, text="Monto total", style="Surface.TLabel"
        )
        self.lbl_ing_monto.grid(row=6, column=0, sticky="w", pady=(0, 6))
        self.ing_monto = ttk.Entry(formulario, style="App.TEntry")
        self.ing_monto.grid(row=7, column=0, sticky="ew", pady=(0, 16))
        self.ing_monto.bind("<KeyRelease>", lambda _e: self._actualizar_preview())

        ttk.Label(formulario, text="Nota opcional", style="Surface.TLabel").grid(
            row=8, column=0, sticky="w", pady=(0, 6)
        )
        self.ing_nota = tk.Text(
            formulario,
            height=4,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            font=fuente(10),
            padx=8,
            pady=8,
        )
        self.ing_nota.grid(row=9, column=0, sticky="ew")

        botones = ttk.Frame(formulario, style="Surface.TFrame")
        botones.grid(row=10, column=0, sticky="ew", pady=(22, 0))
        ttk.Button(
            botones,
            text="Guardar ingreso",
            style="Primary.TButton",
            command=self._guardar_ingreso,
        ).pack(side="left")
        ttk.Button(
            botones,
            text="Limpiar",
            style="Secondary.TButton",
            command=self._limpiar_ingreso,
        ).pack(side="left", padx=8)

        preview = ttk.Frame(self.frame_ingreso, style="Surface2.TFrame", padding=22)
        preview.grid(row=0, column=1, sticky="nsew")
        self.lbl_preview = ttk.Label(
            preview,
            text="Vista previa del reparto",
            style="Surface.TLabel",
        )
        self.lbl_preview.pack(anchor="w")
        self.lbl_preview_ayuda = tk.Label(
            preview,
            text="Se mantiene tu regla: 25 % chofer y 25 % propietario, "
                 "ambos redondeados hacia abajo al múltiplo de 50. "
                 "El resto pertenece al triciclo.",
            bg=COLORES["superficie_2"],
            fg=COLORES["texto_secundario"],
            justify="left",
            wraplength=300,
            font=fuente(9),
        )
        self.lbl_preview_ayuda.pack(anchor="w", pady=(8, 18))

        self.prev_chofer = tk.StringVar(value="$0.00")
        self.prev_propietario = tk.StringVar(value="$0.00")
        self.prev_triciclo = tk.StringVar(value="$0.00")
        self.prev_otro = tk.StringVar(value="$0.00")

        self._fila_preview(preview, "Chofer", self.prev_chofer)
        self._fila_preview(preview, "Propietario", self.prev_propietario)
        self._fila_preview(preview, "Triciclo", self.prev_triciclo)
        self.fila_prev_otro = self._fila_preview(
            preview, "Disponible (otro ingreso)", self.prev_otro
        )
        self.fila_prev_otro.pack_forget()

    def _fila_preview(
        self, parent: tk.Widget, etiqueta: str, variable: tk.StringVar
    ) -> tk.Frame:
        fila = tk.Frame(parent, bg=COLORES["superficie_2"])
        fila.pack(fill="x", pady=8)
        tk.Label(
            fila,
            text=etiqueta,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto_secundario"],
            font=fuente(10),
        ).pack(side="left")
        tk.Label(
            fila,
            textvariable=variable,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            font=fuente(14, "bold"),
        ).pack(side="right")
        return fila

    def _crear_formulario_gasto(self) -> None:
        self.frame_gasto = ttk.Frame(
            self.contenido, style="Surface.TFrame", padding=24
        )
        self.frame_gasto.columnconfigure(0, weight=1)

        ttk.Label(self.frame_gasto, text="Fecha", style="Surface.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self.gas_fecha = ttk.Entry(self.frame_gasto, style="App.TEntry", width=28)
        self.gas_fecha.grid(row=1, column=0, sticky="w", pady=(0, 16))
        self.gas_fecha.insert(0, fecha_hoy_usuario())

        ttk.Label(self.frame_gasto, text="Monto", style="Surface.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.gas_monto = ttk.Entry(self.frame_gasto, style="App.TEntry", width=28)
        self.gas_monto.grid(row=3, column=0, sticky="w", pady=(0, 16))

        ttk.Label(self.frame_gasto, text="Categoría", style="Surface.TLabel").grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )
        self.gas_categoria = ttk.Combobox(
            self.frame_gasto,
            values=CATEGORIAS_GASTO,
            state="readonly",
            style="App.TCombobox",
            width=26,
        )
        self.gas_categoria.grid(row=5, column=0, sticky="w", pady=(0, 16))
        self.gas_categoria.set(CATEGORIAS_GASTO[0])

        ttk.Label(
            self.frame_gasto, text="Comentario", style="Surface.TLabel"
        ).grid(row=6, column=0, sticky="w", pady=(0, 6))
        self.gas_comentario = tk.Text(
            self.frame_gasto,
            height=6,
            width=60,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            font=fuente(10),
            padx=8,
            pady=8,
        )
        self.gas_comentario.grid(row=7, column=0, sticky="ew")

        botones = ttk.Frame(self.frame_gasto, style="Surface.TFrame")
        botones.grid(row=8, column=0, sticky="w", pady=(22, 0))
        ttk.Button(
            botones,
            text="Guardar gasto",
            style="Primary.TButton",
            command=self._guardar_gasto,
        ).pack(side="left")
        ttk.Button(
            botones,
            text="Limpiar",
            style="Secondary.TButton",
            command=self._limpiar_gasto,
        ).pack(side="left", padx=8)

    def seleccionar_modo(self, modo: str) -> None:
        self.modo = modo
        self.frame_ingreso.pack_forget()
        self.frame_gasto.pack_forget()

        if modo == "ingreso":
            self.frame_ingreso.pack(expand=True, fill="both")
            self.btn_ingreso.configure(style="Primary.TButton")
            self.btn_gasto.configure(style="Secondary.TButton")
            self.ing_monto.focus_set()
        else:
            self.frame_gasto.pack(expand=True, fill="both")
            self.btn_ingreso.configure(style="Secondary.TButton")
            self.btn_gasto.configure(style="Primary.TButton")
            self.gas_monto.focus_set()

    def refrescar(self) -> None:
        conductores = obtener_conductores()
        self.ing_conductor.configure(values=conductores)
        if (
            self.tipo_ingreso_seleccionado() == TIPO_INGRESO_TRICICLO
            and conductores
            and self.ing_conductor.get() not in conductores
        ):
            self.ing_conductor.set(conductores[0])
        self._actualizar_tipo_ingreso()

    def tipo_ingreso_seleccionado(self) -> str:
        return tipo_ingreso_desde_nombre(self.ing_tipo.get())

    def _actualizar_tipo_ingreso(self) -> None:
        tipo = self.tipo_ingreso_seleccionado()
        es_otro = tipo == TIPO_INGRESO_OTRO

        self.ing_conductor.configure(state="disabled" if es_otro else "readonly")
        if es_otro:
            self.ing_conductor.set("")
            self.lbl_ing_monto.configure(text="Monto recibido")
            self.lbl_preview.configure(text="Aplicación del monto")
            self.lbl_preview_ayuda.configure(
                text=(
                    "Este ingreso no se reparte entre conductor, propietario ni "
                    "triciclo. El monto completo queda disponible para la economía."
                )
            )
            self.fila_prev_otro.pack(fill="x", pady=8)
        else:
            self.lbl_ing_monto.configure(text="Monto total")
            self.lbl_preview.configure(text="Vista previa del reparto")
            self.lbl_preview_ayuda.configure(
                text=(
                    "Se mantiene tu regla: 25 % chofer y 25 % propietario, ambos "
                    "redondeados hacia abajo al múltiplo de 50. El resto pertenece "
                    "al triciclo."
                )
            )
            self.fila_prev_otro.pack_forget()

        self._actualizar_preview()

    def _actualizar_preview(self) -> None:
        try:
            monto = parsear_monto(self.ing_monto.get())
            if self.tipo_ingreso_seleccionado() == TIPO_INGRESO_OTRO:
                reparto = {
                    "chofer": Decimal("0"),
                    "propietario": Decimal("0"),
                    "triciclo": Decimal("0"),
                    "otro": monto,
                }
            else:
                reparto = calcular_reparto(monto)
                reparto["otro"] = Decimal("0")
        except ValueError:
            reparto = {
                "chofer": Decimal("0"),
                "propietario": Decimal("0"),
                "triciclo": Decimal("0"),
                "otro": Decimal("0"),
            }

        self.prev_chofer.set(formatear_moneda(reparto["chofer"]))
        self.prev_propietario.set(formatear_moneda(reparto["propietario"]))
        self.prev_triciclo.set(formatear_moneda(reparto["triciclo"]))
        self.prev_otro.set(formatear_moneda(reparto["otro"]))

    def _guardar_ingreso(self) -> None:
        try:
            fecha = normalizar_fecha(self.ing_fecha.get())
            monto = parsear_monto(self.ing_monto.get())
            conductor = self.ing_conductor.get()
            nota = self.ing_nota.get("1.0", "end").strip()
            if self.tipo_ingreso_seleccionado() == TIPO_INGRESO_OTRO:
                registrar_otro_ingreso(fecha, monto, nota)
            else:
                registrar_ingreso(fecha, conductor, monto, nota)
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)
            return

        self._limpiar_ingreso()
        self.app.refrescar_todo()
        self.app.notificar("Ingreso registrado correctamente.")
        self.ing_monto.focus_set()

    def _guardar_gasto(self) -> None:
        try:
            fecha = normalizar_fecha(self.gas_fecha.get())
            monto = parsear_monto(self.gas_monto.get())
            categoria = self.gas_categoria.get()
            comentario = self.gas_comentario.get("1.0", "end").strip()
            registrar_gasto(fecha, monto, categoria, comentario)
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)
            return

        self._limpiar_gasto()
        self.app.refrescar_todo()
        self.app.notificar("Gasto registrado correctamente.")
        self.gas_monto.focus_set()

    def _limpiar_ingreso(self) -> None:
        self.ing_fecha.delete(0, "end")
        self.ing_fecha.insert(0, fecha_hoy_usuario())
        self.ing_monto.delete(0, "end")
        self.ing_nota.delete("1.0", "end")
        self.ing_tipo.set(nombre_tipo_ingreso(TIPO_INGRESO_TRICICLO))
        self._actualizar_tipo_ingreso()
        self._actualizar_preview()

    def _limpiar_gasto(self) -> None:
        self.gas_fecha.delete(0, "end")
        self.gas_fecha.insert(0, fecha_hoy_usuario())
        self.gas_monto.delete(0, "end")
        self.gas_categoria.set(CATEGORIAS_GASTO[0])
        self.gas_comentario.delete("1.0", "end")


class PaginaMovimientos(PaginaBase):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, app)
        cabecera = self.encabezado(
            "Movimientos",
            "Filtra, busca, edita y elimina registros.",
        )
        ttk.Button(
            cabecera,
            text="Exportar Excel",
            style="Primary.TButton",
            command=self._exportar,
        ).pack(side="right")

        filtros = ttk.Frame(self, style="Surface.TFrame", padding=12)
        filtros.pack(fill="x", padx=28)

        anio_actual = date.today().year
        ttk.Label(filtros, text="Año", style="Surface.TLabel").pack(
            side="left", padx=(0, 5)
        )
        self.combo_anio = ttk.Combobox(
            filtros,
            values=lista_anios(),
            state="readonly",
            width=7,
            style="App.TCombobox",
        )
        self.combo_anio.set(str(anio_actual))
        self.combo_anio.pack(side="left", padx=(0, 10))

        ttk.Label(filtros, text="Mes", style="Surface.TLabel").pack(
            side="left", padx=(0, 5)
        )
        self.combo_mes = ttk.Combobox(
            filtros,
            values=["Todos"] + MESES,
            state="readonly",
            width=12,
            style="App.TCombobox",
        )
        self.combo_mes.set(MESES[date.today().month - 1])
        self.combo_mes.pack(side="left", padx=(0, 10))

        ttk.Label(filtros, text="Tipo", style="Surface.TLabel").pack(
            side="left", padx=(0, 5)
        )
        self.combo_tipo = ttk.Combobox(
            filtros,
            values=["Todos", "Ingresos", "Gastos"],
            state="readonly",
            width=10,
            style="App.TCombobox",
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.pack(side="left", padx=(0, 10))

        ttk.Label(filtros, text="Conductor", style="Surface.TLabel").pack(
            side="left", padx=(0, 5)
        )
        self.combo_conductor = ttk.Combobox(
            filtros,
            state="readonly",
            width=13,
            style="App.TCombobox",
        )
        self.combo_conductor.set("Todos")
        self.combo_conductor.pack(side="left", padx=(0, 10))

        self.busqueda = ttk.Entry(filtros, style="App.TEntry", width=24)
        self.busqueda.pack(side="left", padx=(0, 8))
        self.busqueda.bind("<Return>", lambda _e: self.refrescar())

        ttk.Button(
            filtros,
            text="Buscar",
            style="Primary.TButton",
            command=self.refrescar,
        ).pack(side="left")

        tabla_frame = ttk.Frame(self, style="App.TFrame")
        tabla_frame.pack(expand=True, fill="both", padx=28, pady=14)

        columnas = (
            "fecha", "tipo", "entrada", "conductor", "triciclo",
            "propietario", "salario", "otros", "gasto", "detalle",
        )
        self.tree = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            style="App.Treeview",
        )
        encabezados = {
            "fecha": "Fecha",
            "tipo": "Tipo",
            "entrada": "Entrada",
            "conductor": "Conductor",
            "triciclo": "Triciclo",
            "propietario": "Propietario",
            "salario": "Salario",
            "otros": "Otros",
            "gasto": "Gasto",
            "detalle": "Detalle",
        }
        anchos = {
            "fecha": 100, "tipo": 85, "entrada": 105,
            "conductor": 90, "triciclo": 90, "propietario": 95,
            "salario": 90, "otros": 90, "gasto": 90, "detalle": 240,
        }

        for col in columnas:
            self.tree.heading(
                col,
                text=encabezados[col],
                command=lambda c=col: self._ordenar(c, False),
            )
            self.tree.column(
                col,
                width=anchos[col],
                anchor="w" if col == "detalle" else "center",
            )

        scroll_y = ttk.Scrollbar(
            tabla_frame, orient="vertical", command=self.tree.yview
        )
        scroll_x = ttk.Scrollbar(
            tabla_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("ingreso", background=COLORES["ingreso_fila"])
        self.tree.tag_configure("gasto", background=COLORES["gasto_fila"])
        self.tree.bind("<Double-1>", lambda _e: self._editar())
        AyudaEncabezadosTreeview(
            self.tree,
            {
                "fecha": "La tabla se muestra por fecha ascendente: los movimientos más antiguos aparecen arriba.",
                "tipo": "Indica si la fila corresponde a un ingreso o a un gasto; además se diferencia por el color.",
                "entrada": "Monto bruto recibido antes de realizar el reparto.",
                "triciclo": "Parte del ingreso que queda para el triciclo después del reparto.",
                "propietario": "Parte redondeada asignada al propietario.",
                "salario": "Parte redondeada asignada al conductor.",
                "otros": "Monto completo de un ingreso que no proviene del trabajo del triciclo.",
                "gasto": "Monto del gasto registrado.",
                "detalle": "Nota del ingreso o categoría y comentario del gasto.",
            },
        )

        acciones = ttk.Frame(self, style="App.TFrame")
        acciones.pack(fill="x", padx=28, pady=(0, 20))
        ttk.Button(
            acciones,
            text="Editar seleccionado",
            style="Secondary.TButton",
            command=self._editar,
        ).pack(side="left")
        ttk.Button(
            acciones,
            text="Eliminar seleccionado",
            style="Danger.TButton",
            command=self._eliminar,
        ).pack(side="left", padx=8)

        leyenda = tk.Frame(acciones, bg=COLORES["fondo"])
        leyenda.pack(side="left", padx=(18, 0))
        tk.Label(
            leyenda, text="  Ingreso  ", bg=COLORES["ingreso_fila"],
            fg=COLORES["texto"], font=fuente(9), padx=6, pady=3
        ).pack(side="left", padx=(0, 6))
        tk.Label(
            leyenda, text="  Gasto  ", bg=COLORES["gasto_fila"],
            fg=COLORES["texto"], font=fuente(9), padx=6, pady=3
        ).pack(side="left")

        self.total_var = tk.StringVar(value="0 movimientos")
        ttk.Label(
            acciones, textvariable=self.total_var, style="Muted.TLabel"
        ).pack(side="right")

    def refrescar(self) -> None:
        conductores = ["Todos"] + obtener_conductores()
        self.combo_conductor.configure(values=conductores)
        if self.combo_conductor.get() not in conductores:
            self.combo_conductor.set("Todos")

        for item in self.tree.get_children():
            self.tree.delete(item)

        anio = int(self.combo_anio.get())
        mes = None if self.combo_mes.get() == "Todos" else MESES.index(
            self.combo_mes.get()
        ) + 1

        movimientos = obtener_movimientos(
            anio=anio,
            mes=mes,
            tipo=self.combo_tipo.get(),
            conductor=self.combo_conductor.get(),
            busqueda=self.busqueda.get(),
            ascendente=True,
        )

        for mov in movimientos:
            self.tree.insert(
                "",
                "end",
                iid=f"{mov['Tipo']}-{mov['ID_Numero']}",
                values=(
                    fecha_para_usuario(mov["Fecha"]),
                    mov["Tipo"],
                    formatear_moneda(mov["Entrada"]) if mov["Entrada"] is not None else "",
                    mov["Conductor"],
                    formatear_moneda(mov["Triciclo"]) if mov["Triciclo"] is not None else "",
                    formatear_moneda(mov["Propietario"]) if mov["Propietario"] is not None else "",
                    formatear_moneda(mov["Salario"]) if mov["Salario"] is not None else "",
                    formatear_moneda(mov["Otros"]) if mov["Otros"] is not None else "",
                    formatear_moneda(mov["Gastos"]) if mov["Gastos"] is not None else "",
                    mov["Detalle"],
                ),
                tags=(mov["Tipo"].lower(),),
            )

        self.total_var.set(f"{len(movimientos)} movimientos")

    def _seleccion(self) -> tuple[str, int] | None:
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo(
                "Selecciona un registro",
                "Selecciona una fila de la tabla.",
                parent=self,
            )
            return None

        tipo, numero = seleccion[0].split("-", 1)
        return tipo, int(numero)

    def _editar(self) -> None:
        seleccion = self._seleccion()
        if not seleccion:
            return
        tipo, numero = seleccion
        VentanaEdicion(self.app, tipo, numero, self.app.refrescar_todo)

    def _eliminar(self) -> None:
        seleccion = self._seleccion()
        if not seleccion:
            return
        tipo, numero = seleccion

        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar definitivamente el registro {tipo} #{numero}?",
            parent=self,
        ):
            return

        try:
            eliminar_registro(tipo, numero)
        except Exception as exc:
            messagebox.showerror("No se pudo eliminar", str(exc), parent=self)
            return

        self.app.refrescar_todo()
        self.app.notificar("Registro eliminado.")

    def _exportar(self) -> None:
        try:
            ruta = exportar_excel()
        except Exception as exc:
            messagebox.showerror("Error al exportar", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Exportación completada",
            f"El archivo se guardó en:\n{ruta}",
            parent=self,
        )

    def _ordenar(self, columna: str, descendente: bool) -> None:
        datos = [(self.tree.set(item, columna), item) for item in self.tree.get_children("")]

        def clave(par):
            texto = par[0]
            if columna == "fecha":
                try:
                    dia, mes, anio = map(int, texto.split("/"))
                    return anio, mes, dia
                except (TypeError, ValueError):
                    return 0, 0, 0

            valor = texto.replace("$", "").replace(",", "")
            try:
                return float(valor)
            except ValueError:
                return texto.lower()

        datos.sort(key=clave, reverse=descendente)
        for indice, (_, item) in enumerate(datos):
            self.tree.move(item, "", indice)

        self.tree.heading(
            columna,
            command=lambda: self._ordenar(columna, not descendente),
        )


class PaginaResumenAnual(PaginaBase):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, app)
        cabecera = self.encabezado(
            "Resumen anual",
            "Evolución mensual del saldo, ingresos, salarios y gastos.",
        )

        anio_actual = date.today().year
        self.combo_anio = ttk.Combobox(
            cabecera,
            values=lista_anios(),
            state="readonly",
            width=8,
            style="App.TCombobox",
        )
        self.combo_anio.set(str(anio_actual))
        self.combo_anio.pack(side="right")
        self.combo_anio.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())

        tabla_frame = ttk.Frame(self, style="App.TFrame")
        tabla_frame.pack(expand=True, fill="both", padx=28, pady=(0, 14))

        columnas = (
            "mes", "inicial", "bruto", "disponible",
            "otros", "salarios", "gastos", "final",
        )
        self.tree = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            style="App.Treeview",
        )
        textos = {
            "mes": "Mes",
            "inicial": "Balance inicial",
            "bruto": "Ingreso bruto",
            "disponible": "Disponible generado",
            "otros": "Otros ingresos",
            "salarios": "Salarios",
            "gastos": "Gastos",
            "final": "Saldo final",
        }
        for col in columnas:
            self.tree.heading(col, text=textos[col])
            self.tree.column(
                col,
                width=150 if col != "mes" else 110,
                anchor="center",
            )
        self.tree.pack(expand=True, fill="both")
        self.tree.tag_configure(
            "mes_actual",
            background=COLORES["mes_actual"],
            foreground=COLORES["texto"],
            font=fuente(9, "bold"),
        )
        AyudaEncabezadosTreeview(
            self.tree,
            {
                "inicial": (
                    "Dinero disponible al comenzar el mes: saldo acumulado del "
                    "triciclo y propietario menos los gastos anteriores. En enero "
                    "también arrastra el saldo de años previos."
                ),
                "bruto": (
                    "Suma de todos los ingresos del mes antes de separar las partes "
                    "del conductor, propietario y triciclo."
                ),
                "disponible": (
                    "Suma de la parte del triciclo, del propietario y de los otros "
                    "ingresos generados durante el mes. No incluye salarios."
                ),
                "otros": (
                    "Suma de los ingresos externos al trabajo del triciclo. El monto "
                    "completo queda disponible y no genera salario."
                ),
                "salarios": "Total asignado a los conductores durante el mes.",
                "gastos": "Suma de todos los gastos registrados durante el mes.",
                "final": (
                    "Saldo inicial del mes más todo el dinero disponible generado, "
                    "menos los gastos del mes."
                ),
            },
        )

        resumen = ttk.Frame(self, style="App.TFrame")
        resumen.pack(fill="x", padx=28, pady=(0, 24))
        for col in range(4):
            resumen.grid_columnconfigure(col, weight=1, uniform="cierre")

        self.cierre_vars = {
            "bruto": tk.StringVar(value="$0.00"),
            "salarios": tk.StringVar(value="$0.00"),
            "gastos": tk.StringVar(value="$0.00"),
            "final": tk.StringVar(value="$0.00"),
        }
        Tarjeta(
            resumen,
            "Ingresos brutos del año",
            self.cierre_vars["bruto"],
            ayuda=(
                "Suma de todos los ingresos brutos registrados en el año, antes de "
                "realizar cualquier reparto."
            ),
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        Tarjeta(
            resumen,
            "Salarios del año",
            self.cierre_vars["salarios"],
            ayuda="Suma de todas las partes asignadas a los conductores durante el año.",
        ).grid(row=0, column=1, sticky="nsew", padx=8)
        Tarjeta(
            resumen,
            "Gastos del año",
            self.cierre_vars["gastos"],
            "DangerValue.TLabel",
            ayuda="Suma de todos los gastos registrados dentro del año seleccionado.",
        ).grid(row=0, column=2, sticky="nsew", padx=8)
        Tarjeta(
            resumen,
            "Saldo al cierre",
            self.cierre_vars["final"],
            "SuccessValue.TLabel",
            ayuda=(
                "Dinero disponible al terminar diciembre: saldo arrastrado, más las "
                "partes del triciclo, propietario y otros ingresos, menos todos los gastos."
            ),
        ).grid(row=0, column=3, sticky="nsew", padx=(8, 0))

    def refrescar(self) -> None:
        anio = int(self.combo_anio.get())
        resumen = obtener_resumen_anual(anio)

        for item in self.tree.get_children():
            self.tree.delete(item)

        ahora = date.today()
        for fila in resumen:
            mes_numero = int(fila["mes"])
            tags = ()
            if anio == ahora.year and mes_numero == ahora.month:
                tags = ("mes_actual",)

            self.tree.insert(
                "",
                "end",
                values=(
                    MESES[mes_numero - 1],
                    formatear_moneda(fila["saldo_inicial"]),
                    formatear_moneda(fila["ingreso_bruto"]),
                    formatear_moneda(fila["disponible"]),
                    formatear_moneda(fila["otros"]),
                    formatear_moneda(fila["salarios"]),
                    formatear_moneda(fila["gastos"]),
                    formatear_moneda(fila["saldo_final"]),
                ),
                tags=tags,
            )

        self.cierre_vars["bruto"].set(
            formatear_moneda(sum(float(f["ingreso_bruto"]) for f in resumen))
        )
        self.cierre_vars["salarios"].set(
            formatear_moneda(sum(float(f["salarios"]) for f in resumen))
        )
        self.cierre_vars["gastos"].set(
            formatear_moneda(sum(float(f["gastos"]) for f in resumen))
        )

        meses_transcurridos = [
            fila for fila in resumen if not bool(fila.get("es_futuro"))
        ]
        saldo_cierre = (
            meses_transcurridos[-1]["saldo_final"]
            if meses_transcurridos
            else 0
        )
        self.cierre_vars["final"].set(formatear_moneda(saldo_cierre))


class PaginaConfiguracion(PaginaBase):
    def __init__(self, parent: tk.Widget, app: AppFinanzas) -> None:
        super().__init__(parent, app)
        self.encabezado(
            "Configuración",
            "Conductores, copias de seguridad y reglas del negocio.",
        )

        columnas = ttk.Frame(self, style="App.TFrame")
        columnas.pack(expand=True, fill="both", padx=28, pady=(0, 24))
        columnas.grid_columnconfigure(0, weight=1)
        columnas.grid_columnconfigure(1, weight=1)
        columnas.grid_rowconfigure(0, weight=1)

        panel_cond = ttk.Frame(columnas, style="Surface.TFrame", padding=20)
        panel_cond.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(
            panel_cond, text="Conductores", style="CardTitle.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            panel_cond,
            text="Puedes agregar conductores o desactivarlos sin borrar su historial.",
            style="SurfaceMuted.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        self.lista = tk.Listbox(
            panel_cond,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            selectbackground=COLORES["acento"],
            selectforeground="white",
            relief="flat",
            height=12,
            font=fuente(10),
        )
        self.lista.pack(expand=True, fill="both")

        acciones = ttk.Frame(panel_cond, style="Surface.TFrame")
        acciones.pack(fill="x", pady=(14, 0))
        ttk.Button(
            acciones,
            text="Agregar",
            style="Primary.TButton",
            command=self._agregar,
        ).pack(side="left")
        ttk.Button(
            acciones,
            text="Desactivar",
            style="Secondary.TButton",
            command=self._desactivar,
        ).pack(side="left", padx=8)

        panel_reglas = ttk.Frame(columnas, style="Surface.TFrame", padding=20)
        panel_reglas.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ttk.Label(
            panel_reglas, text="Reglas del reparto", style="CardTitle.TLabel"
        ).pack(anchor="w")
        texto_reglas = (
            f"Chofer: {PORCENTAJE_CHOFER * 100:.0f} % del ingreso.\n"
            f"Propietario: {PORCENTAJE_PROPIETARIO * 100:.0f} % del ingreso.\n"
            f"Redondeo: hacia abajo al múltiplo de {MULTIPLO_REDONDEO:.0f}.\n"
            "Triciclo: recibe todo el monto restante.\n"
            "Saldo inicial: se asigna completamente al propietario."
        )
        tk.Label(
            panel_reglas,
            text=texto_reglas,
            bg=COLORES["superficie"],
            fg=COLORES["texto"],
            justify="left",
            font=fuente(11),
            pady=16,
        ).pack(anchor="w")

        ttk.Separator(panel_reglas).pack(fill="x", pady=12)

        ttk.Label(
            panel_reglas,
            text="Protección de datos",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(0, 10))

        ttk.Button(
            panel_reglas,
            text="Crear copia de seguridad",
            style="Primary.TButton",
            command=self._backup,
        ).pack(anchor="w", fill="x")

        ttk.Button(
            panel_reglas,
            text="Exportar base de datos",
            style="Secondary.TButton",
            command=self._exportar_base,
        ).pack(anchor="w", fill="x", pady=(8, 0))

        ttk.Button(
            panel_reglas,
            text="Importar base de datos",
            style="Secondary.TButton",
            command=self._importar_base,
        ).pack(anchor="w", fill="x", pady=(8, 0))

        ttk.Label(
            panel_reglas,
            text=(
                "La copia automática se guarda en 'backups'. Exportar permite "
                "elegir otra ubicación. Al importar, el programa valida el "
                "archivo y guarda primero una copia de la base actual."
            ),
            style="SurfaceMuted.TLabel",
            wraplength=430,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

    def refrescar(self) -> None:
        self.lista.delete(0, "end")
        for nombre in obtener_conductores():
            self.lista.insert("end", nombre)

    def _agregar(self) -> None:
        nombre = simpledialog.askstring(
            "Nuevo conductor",
            "Nombre del conductor:",
            parent=self,
        )
        if nombre is None:
            return
        try:
            agregar_conductor(nombre)
        except Exception as exc:
            messagebox.showerror("No se pudo agregar", str(exc), parent=self)
            return
        self.app.refrescar_todo()
        self.app.notificar("Conductor agregado.")

    def _desactivar(self) -> None:
        seleccion = self.lista.curselection()
        if not seleccion:
            messagebox.showinfo(
                "Selecciona un conductor",
                "Selecciona el conductor que deseas desactivar.",
                parent=self,
            )
            return
        nombre = self.lista.get(seleccion[0])
        if not messagebox.askyesno(
            "Desactivar conductor",
            f"¿Desactivar a {nombre}?\n\nSu historial no se borrará.",
            parent=self,
        ):
            return
        cambiar_estado_conductor(nombre, False)
        self.app.refrescar_todo()
        self.app.notificar("Conductor desactivado.")

    def _backup(self) -> None:
        try:
            ruta = crear_copia_seguridad()
        except Exception as exc:
            messagebox.showerror("No se pudo crear la copia", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Copia creada",
            f"La copia de seguridad se guardó en:\n{ruta}",
            parent=self,
        )

    def _exportar_base(self) -> None:
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar base de datos",
            initialdir=str(DB_PATH.parent),
            initialfile=f"renta_triciclo_{date.today().isoformat()}.db",
            defaultextension=".db",
            filetypes=[
                ("Base de datos SQLite", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not ruta:
            return

        try:
            destino = exportar_base_datos(Path(ruta))
        except Exception as exc:
            messagebox.showerror(
                "No se pudo exportar",
                str(exc),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Base exportada",
            f"Se creó una copia completa en:\n{destino}",
            parent=self,
        )

    def _importar_base(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar base de datos",
            initialdir=str(DB_PATH.parent),
            filetypes=[
                ("Base de datos SQLite", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not ruta:
            return

        confirmar = messagebox.askyesno(
            "Importar base de datos",
            "La base seleccionada sustituirá los datos actuales.\n\n"
            "Antes del reemplazo se creará automáticamente una copia de "
            "seguridad de la base vigente. ¿Deseas continuar?",
            parent=self,
        )
        if not confirmar:
            return

        try:
            respaldo = importar_base_datos(Path(ruta))
        except Exception as exc:
            messagebox.showerror(
                "No se pudo importar",
                str(exc),
                parent=self,
            )
            return

        self.app.refrescar_todo()
        self.app.notificar("Base de datos importada correctamente.")

        mensaje = "La base de datos fue importada y actualizada correctamente."
        if respaldo:
            mensaje += f"\n\nCopia automática de la base anterior:\n{respaldo}"
        messagebox.showinfo("Importación completada", mensaje, parent=self)

        if not existe_balance_inicial():
            self.app.after(150, self.app._comprobar_primera_ejecucion)


class VentanaEdicion(tk.Toplevel):
    def __init__(
        self,
        parent: AppFinanzas,
        tipo: str,
        id_numero: int,
        al_guardar: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.parent = parent
        self.tipo = tipo
        self.id_numero = id_numero
        self.al_guardar = al_guardar
        self.registro = obtener_registro(tipo, id_numero)

        self.title(f"Editar {tipo.lower()} #{id_numero}")
        self.geometry("520x650")
        self.resizable(False, False)
        self.configure(bg=COLORES["fondo"])
        self.transient(parent)
        self.grab_set()

        if not self.registro:
            messagebox.showerror(
                "Registro no encontrado",
                "El registro ya no existe.",
                parent=self,
            )
            self.destroy()
            return

        if tipo == "Ingreso" and self.registro["Es_Balance_Inicial"]:
            messagebox.showinfo(
                "Saldo protegido",
                "El saldo inicial está protegido para evitar modificaciones accidentales.",
                parent=self,
            )
            self.destroy()
            return

        frame = ttk.Frame(self, style="Surface.TFrame", padding=24)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=f"Editar {tipo.lower()} #{id_numero}",
            style="CardTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 18))

        if tipo == "Ingreso":
            self._form_ingreso(frame)
        else:
            self._form_gasto(frame)

    def _campo(self, frame: ttk.Frame, fila: int, texto: str) -> ttk.Entry:
        ttk.Label(frame, text=texto, style="Surface.TLabel").grid(
            row=fila, column=0, sticky="w", pady=(0, 5)
        )
        entry = ttk.Entry(frame, style="App.TEntry")
        entry.grid(row=fila + 1, column=0, sticky="ew", pady=(0, 14))
        return entry

    def _form_ingreso(self, frame: ttk.Frame) -> None:
        self.fecha = self._campo(frame, 1, "Fecha")
        self.fecha.insert(0, fecha_para_usuario(self.registro["Fecha"]))

        ttk.Label(frame, text="Tipo de ingreso", style="Surface.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 5)
        )
        self.tipo_ingreso = ttk.Combobox(
            frame,
            values=TIPOS_INGRESO,
            state="readonly",
            style="App.TCombobox",
        )
        self.tipo_ingreso.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        self.tipo_ingreso.set(
            nombre_tipo_ingreso(self.registro.get("Tipo_Ingreso"))
        )
        self.tipo_ingreso.bind(
            "<<ComboboxSelected>>",
            lambda _e: self._actualizar_tipo_ingreso(),
        )

        self.lbl_conductor = ttk.Label(
            frame, text="Conductor", style="Surface.TLabel"
        )
        self.lbl_conductor.grid(row=5, column=0, sticky="w", pady=(0, 5))
        self.conductor = ttk.Combobox(
            frame,
            values=obtener_conductores(),
            state="readonly",
            style="App.TCombobox",
        )
        self.conductor.grid(row=6, column=0, sticky="ew", pady=(0, 14))
        self.conductor.set(self.registro["Conductor"] or "")

        self.monto = self._campo(frame, 7, "Monto total")
        self.monto.insert(0, str(self.registro["Ingreso_Total"]))

        ttk.Label(frame, text="Nota", style="Surface.TLabel").grid(
            row=9, column=0, sticky="w", pady=(0, 5)
        )
        self.nota = tk.Text(
            frame,
            height=5,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            font=fuente(10),
        )
        self.nota.grid(row=10, column=0, sticky="ew")
        self.nota.insert("1.0", self.registro.get("Nota") or "")

        ttk.Button(
            frame,
            text="Guardar cambios",
            style="Primary.TButton",
            command=self._guardar_ingreso,
        ).grid(row=11, column=0, sticky="w", pady=(20, 0))
        self._actualizar_tipo_ingreso()

    def _tipo_ingreso_seleccionado(self) -> str:
        return tipo_ingreso_desde_nombre(self.tipo_ingreso.get())

    def _actualizar_tipo_ingreso(self) -> None:
        if self._tipo_ingreso_seleccionado() == TIPO_INGRESO_OTRO:
            self.conductor.set("")
            self.conductor.configure(state="disabled")
            self.lbl_conductor.configure(text="Conductor (no aplica)")
        else:
            self.conductor.configure(state="readonly")
            self.lbl_conductor.configure(text="Conductor")

    def _form_gasto(self, frame: ttk.Frame) -> None:
        self.fecha = self._campo(frame, 1, "Fecha")
        self.fecha.insert(0, fecha_para_usuario(self.registro["Fecha"]))

        self.monto = self._campo(frame, 3, "Monto")
        self.monto.insert(0, str(self.registro["Monto"]))

        ttk.Label(frame, text="Categoría", style="Surface.TLabel").grid(
            row=5, column=0, sticky="w", pady=(0, 5)
        )
        self.categoria = ttk.Combobox(
            frame,
            values=CATEGORIAS_GASTO,
            state="readonly",
            style="App.TCombobox",
        )
        self.categoria.grid(row=6, column=0, sticky="ew", pady=(0, 14))
        self.categoria.set(self.registro.get("Categoria") or "General")

        ttk.Label(frame, text="Comentario", style="Surface.TLabel").grid(
            row=7, column=0, sticky="w", pady=(0, 5)
        )
        self.comentario = tk.Text(
            frame,
            height=5,
            bg=COLORES["superficie_2"],
            fg=COLORES["texto"],
            insertbackground=COLORES["texto"],
            relief="flat",
            font=fuente(10),
        )
        self.comentario.grid(row=8, column=0, sticky="ew")
        self.comentario.insert("1.0", self.registro.get("Comentario") or "")

        ttk.Button(
            frame,
            text="Guardar cambios",
            style="Primary.TButton",
            command=self._guardar_gasto,
        ).grid(row=9, column=0, sticky="w", pady=(20, 0))

    def _guardar_ingreso(self) -> None:
        try:
            actualizar_ingreso(
                self.id_numero,
                normalizar_fecha(self.fecha.get()),
                self.conductor.get(),
                parsear_monto(self.monto.get()),
                self.nota.get("1.0", "end").strip(),
                self._tipo_ingreso_seleccionado(),
            )
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)
            return
        self.al_guardar()
        self.parent.notificar("Ingreso actualizado.")
        self.destroy()

    def _guardar_gasto(self) -> None:
        try:
            actualizar_gasto(
                self.id_numero,
                normalizar_fecha(self.fecha.get()),
                parsear_monto(self.monto.get()),
                self.categoria.get(),
                self.comentario.get("1.0", "end").strip(),
            )
        except Exception as exc:
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)
            return
        self.al_guardar()
        self.parent.notificar("Gasto actualizado.")
        self.destroy()
