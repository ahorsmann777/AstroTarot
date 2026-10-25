#!/usr/bin/env python3
"""Menú gráfico de inicio para elegir uno de los repartos de AstroTarot.

Autor: Alejandro Horsmann
MIT Licence
"""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox


BASE = os.path.dirname(os.path.abspath(__file__))

COLORES = {
    "fondo": "#f5f0e6",
    "opcion": "#fffaf2",
    "opcion_activa": "#efe1cf",
    "borde": "#d9c7b2",
    "seccion": "#7a4a2b",
    "circulo": "#4a3020",
    "deshabilitado": "#9c8f83",
}

PROGRAMAS = (
    (
        "Rueda de 36 cartas",
        "36 decanatos · una carta cada 10°",
        "repartir_36_decanatos.py",
    ),
    (
        "Rueda de 12 cartas",
        "12 secciones · signos zodiacales",
        "repartir_12_signos.py",
    ),
    (
        "Rueda de 12 cartas numeradas",
        "12 secciones · números romanos",
        "repartir_12_casas.py",
    ),
    (
        "Hexagrama unicursal",
        "7 cartas · símbolos planetarios",
        "repartir_7_hexagrama.py",
    ),
)


class MenuInicio:
    def __init__(self, root):
        self.root = root
        self.opciones = []
        root.title("AstroTarot — Menú de inicio")
        root.configure(bg=COLORES["fondo"])
        root.resizable(False, False)
        self._centrar(640, 590)
        self._crear_interfaz()

    def _centrar(self, ancho, alto):
        x = (self.root.winfo_screenwidth() - ancho) // 2
        y = (self.root.winfo_screenheight() - alto) // 2
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _crear_interfaz(self):
        contenedor = tk.Frame(self.root, bg=COLORES["fondo"], padx=40, pady=28)
        contenedor.pack(fill="both", expand=True)

        tk.Label(
            contenedor,
            text="AstroTarot",
            font=("Helvetica", 28, "bold"),
            bg=COLORES["fondo"],
            fg=COLORES["circulo"],
        ).pack()
        tk.Label(
            contenedor,
            text="Elige una operación",
            font=("Helvetica", 12),
            bg=COLORES["fondo"],
            fg=COLORES["seccion"],
        ).pack(pady=(0, 22))

        for titulo, descripcion, archivo in PROGRAMAS:
            self.opciones.append(
                self._crear_opcion(contenedor, titulo, descripcion, archivo)
            )

        tk.Button(
            contenedor,
            text="Salir",
            font=("Helvetica", 11),
            bg=COLORES["fondo"],
            fg=COLORES["seccion"],
            activebackground=COLORES["fondo"],
            activeforeground=COLORES["circulo"],
            relief="flat",
            cursor="hand2",
            command=self.root.destroy,
        ).pack(pady=(16, 0))

    def _crear_opcion(self, padre, titulo, descripcion, archivo):
        ruta = os.path.join(BASE, archivo)
        disponible = os.path.isfile(ruta)
        fondo = COLORES["opcion"] if disponible else "#eee8e0"
        color_texto = COLORES["circulo"] if disponible else COLORES["deshabilitado"]

        marco = tk.Frame(
            padre, bg=fondo, highlightbackground=COLORES["borde"],
            highlightthickness=1, cursor="hand2" if disponible else "arrow",
        )
        marco.pack(fill="x", pady=6)

        contenido = tk.Frame(marco, bg=fondo, padx=18, pady=12)
        contenido.pack(fill="x")

        etiqueta_titulo = tk.Label(
            contenido,
            text=titulo,
            font=("Helvetica", 14, "bold"),
            bg=fondo,
            fg=color_texto,
            anchor="w",
        )
        etiqueta_titulo.pack(fill="x")

        etiqueta_desc = tk.Label(
            contenido,
            text=descripcion if disponible else "Archivo no encontrado",
            font=("Helvetica", 10),
            bg=fondo,
            fg=COLORES["seccion"] if disponible else COLORES["deshabilitado"],
            anchor="w",
        )
        etiqueta_desc.pack(fill="x")

        flecha = tk.Label(
            contenido,
            text="›",
            font=("Helvetica", 22, "bold"),
            bg=fondo,
            fg=color_texto,
        )
        flecha.place(relx=1.0, rely=0.5, anchor="e", x=-4)

        widgets = (marco, contenido, etiqueta_titulo, etiqueta_desc, flecha)
        opcion = {
            "marco": marco,
            "widgets": widgets,
            "archivo": archivo,
            "disponible": disponible,
        }

        if disponible:
            for widget in widgets:
                widget.bind("<Button-1>", lambda event, a=archivo: self.abrir(a))
                widget.bind(
                    "<Enter>",
                    lambda event, o=opcion: self._resaltar(o, True),
                )
                widget.bind(
                    "<Leave>",
                    lambda event, o=opcion: self._resaltar(o, False),
                )
        return opcion

    def _resaltar(self, opcion, activa):
        if not opcion["disponible"]:
            return
        color = COLORES["opcion_activa"] if activa else COLORES["opcion"]
        for widget in opcion["widgets"]:
            widget.configure(bg=color)

    def abrir(self, archivo):
        ruta = os.path.join(BASE, archivo)
        if not os.path.isfile(ruta):
            messagebox.showerror(
                "AstroTarot",
                f"No se encontró el programa:\n{archivo}",
                parent=self.root,
            )
            return
        try:
            subprocess.Popen([sys.executable, ruta], cwd=BASE)
        except OSError as error:
            messagebox.showerror(
                "AstroTarot",
                f"No se pudo iniciar el programa:\n{error}",
                parent=self.root,
            )
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    MenuInicio(root)
    root.mainloop()


if __name__ == "__main__":
    main()
