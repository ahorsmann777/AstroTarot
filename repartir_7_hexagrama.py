#!/usr/bin/env python3
"""Reparte 7 cartas sobre un hexagrama unicursal con los símbolos de los planetas.

Las 6 cartas exteriores ocupan los vértices y la séptima queda en el centro.
Sobre cada carta se dibuja el símbolo planetario correspondiente.

Autor: Alejandro Horsmann
MIT Licence
"""

import math
import os
import random
import subprocess
import sys

import tkinter as tk
from PIL import Image, ImageTk


BASE = os.path.dirname(os.path.abspath(__file__))
CANDIDATOS = (
    os.path.join(BASE, "Cartas"),
    os.path.join(os.getcwd(), "Cartas"),
    os.path.join(BASE, "astrotarot", "Cartas"),
    os.path.join(os.getcwd(), "astrotarot", "Cartas"),
)

OFFSETS_UI = {
    "margen": 30,
    "barra": 100,
}

COLORES = {
    "fondo": "#f5f0e6",
    "punteo": "#b08968",
    "seccion": "#7a4a2b",
    "circulo": "#4a3020",
}

TAMANO_CARTAS = 7
LADOS = 6
ANG0 = -90.0
ORDEN_HEXAGRAMA = (0, 2, 5, 3, 1, 4, 0)
SIMBOLOS_PLANETAS = ("♄", "♃", "♀", "☽", "☿", "♂")
SIMBOLO_CENTRO = "☉"


def localizar_cartas():
    for carpeta in CANDIDATOS:
        if os.path.isdir(carpeta):
            return carpeta
    print("No se encontró la carpeta 'Cartas'.", file=sys.stderr)
    sys.exit(1)


def tamano_ventana(raiz):
    ancho = raiz.winfo_screenwidth()
    alto = raiz.winfo_screenheight()
    disponible = min(
        ancho - 2 * OFFSETS_UI["margen"],
        alto - 2 * OFFSETS_UI["margen"] - OFFSETS_UI["barra"],
    )
    return max(500, int(disponible))


def volver_al_menu(root):
    ruta = os.path.join(BASE, "menu_inicio.py")
    if os.path.isfile(ruta):
        subprocess.Popen([sys.executable, ruta], cwd=BASE)
    root.destroy()


def construir_geometria(lienzo):
    f = lienzo / 1000.0
    return {
        "lienzo": lienzo,
        "centro": lienzo // 2,
        "ox": 0,
        "oy": 0,
        "r_hexagrama": int(320 * f),
        "l_carta": int(190 * f),
    }


def punto(g, ang, radio):
    a = math.radians(ang)
    return (g["ox"] + g["centro"] + radio * math.cos(a),
            g["oy"] + g["centro"] + radio * math.sin(a))


def vertices_hexagrama(g):
    return [
        punto(g, ANG0 + 360.0 / LADOS * i, g["r_hexagrama"])
        for i in range(LADOS)
    ]


class HexagramaApp:
    def __init__(self, root, carpeta_cartas):
        self.root = root
        root.title("AstroTarot — Hexagrama unicursal de 7 cartas")
        root.configure(bg=COLORES["fondo"])
        root.resizable(True, True)
        root.minsize(500, 500)

        lienzo_ini = tamano_ventana(root)
        self.geo = construir_geometria(lienzo_ini)
        g = self.geo

        self.cartas = sorted(
            os.path.join(carpeta_cartas, f)
            for f in os.listdir(carpeta_cartas)
            if f.lower().endswith(".jpg")
        )
        if not self.cartas:
            print("La carpeta 'Cartas' no contiene imágenes JPG.", file=sys.stderr)
            sys.exit(1)

        self.base = {path: self._cargar(path) for path in self.cartas}
        self.fotos = []
        self.reparto = 0
        self.elegidas = []
        self._after_id = None
        self._ultimo_tamano = (g["lienzo"], g["lienzo"])

        self.canvas = tk.Canvas(
            root, width=g["lienzo"], height=g["lienzo"],
            bg=COLORES["fondo"], highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=(10, 0), expand=True, fill="both")
        self.canvas.bind("<Configure>", self.reprogramar_rediseno)

        fila = tk.Frame(root, bg=COLORES["fondo"])
        fila.pack(pady=10)

        self.info = tk.Label(fila, text="", font=("Helvetica", 12), bg=COLORES["fondo"])
        self.info.pack(side="left", padx=20)

        self.boton = tk.Button(
            fila,
            text="Repartir",
            font=("Helvetica", 16, "bold"),
            bg=COLORES["seccion"],
            fg="white",
            activebackground="#5d3820",
            activeforeground="white",
            padx=26,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self.repartir,
        )
        self.boton.pack(side="left", padx=20)

        self.boton_salir = tk.Button(
            fila,
            text="Salir",
            font=("Helvetica", 14, "bold"),
            bg=COLORES["circulo"],
            fg="white",
            activebackground=COLORES["seccion"],
            activeforeground="white",
            padx=20,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=lambda: volver_al_menu(self.root),
        )
        self.boton_salir.pack(side="left", padx=(0, 20))

        self.repartir()

    def _cargar(self, path):
        im = Image.open(path).convert("RGB")
        ancho, alto = im.size
        alto_nuevo = self.geo["l_carta"]
        ancho_nuevo = max(1, int(round(alto_nuevo * ancho / alto)))
        return im.resize((ancho_nuevo, alto_nuevo), Image.LANCZOS)

    def _preparar(self, base):
        return ImageTk.PhotoImage(base.convert("RGBA"))

    def reiniciar_lienzo(self):
        self.fotos = []
        self.canvas.delete("all")

    def dibujar_hexagrama(self):
        vertices = vertices_hexagrama(self.geo)
        coords = []
        for indice in ORDEN_HEXAGRAMA:
            coords.extend(vertices[indice])
        self.canvas.create_line(
            *coords,
            fill=COLORES["seccion"],
            width=3,
            capstyle="round",
            joinstyle="round",
        )

    def dibujar_planetas(self):
        g = self.geo
        f = g["lienzo"] / 1000.0
        tam = max(14, int(34 * f))
        radio = max(14, int(24 * f))
        posiciones = [
            (punto(g, ANG0 + 360.0 / LADOS * i, g["r_hexagrama"]), simbolo)
            for i, simbolo in enumerate(SIMBOLOS_PLANETAS)
        ]
        posiciones.append(
            ((g["ox"] + g["centro"], g["oy"] + g["centro"]), SIMBOLO_CENTRO)
        )
        for (x, y), simbolo in posiciones:
            self.canvas.create_oval(
                x - radio, y - radio, x + radio, y + radio,
                fill=COLORES["fondo"], outline=COLORES["seccion"], width=1,
            )
            self.canvas.create_text(
                x, y, text=simbolo,
                font=("DejaVu Sans", tam, "bold"),
                fill=COLORES["seccion"],
            )

    def repartir(self):
        self.elegidas = random.sample(self.cartas, TAMANO_CARTAS)
        self.reparto += 1
        self.actualizar_info()
        self.redibujar()

    def redibujar(self):
        if not self.elegidas:
            return
        self.reiniciar_lienzo()
        self.dibujar_hexagrama()

        for indice in range(LADOS):
            ang = ANG0 + 360.0 / LADOS * indice
            foto = self._preparar(self.base[self.elegidas[indice]])
            self.fotos.append(foto)
            x, y = punto(self.geo, ang, self.geo["r_hexagrama"])
            self.canvas.create_image(x, y, image=foto, anchor="center")

        foto = self._preparar(self.base[self.elegidas[LADOS]])
        self.fotos.append(foto)
        self.canvas.create_image(
            self.geo["centro"], self.geo["centro"],
            image=foto, anchor="center",
        )

        self.dibujar_planetas()

    def actualizar_info(self):
        self.info.config(
            text=f"Reparto {self.reparto}  ·  {TAMANO_CARTAS} cartas de {len(self.cartas)}"
        )

    def _establecer_geometria(self, ancho, alto):
        lienzo = max(1, min(ancho, alto))
        g = construir_geometria(lienzo)
        g["ox"] = (ancho - lienzo) // 2
        g["oy"] = (alto - lienzo) // 2
        self.geo = g

    def reprogramar_rediseno(self, event=None):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(120, self.aplicar_rediseno)

    def aplicar_rediseno(self):
        self._after_id = None
        ancho = self.canvas.winfo_width()
        alto = self.canvas.winfo_height()
        if ancho < 2 or alto < 2:
            return
        if (ancho, alto) == self._ultimo_tamano:
            return
        self._ultimo_tamano = (ancho, alto)
        self._establecer_geometria(ancho, alto)
        self.base = {path: self._cargar(path) for path in self.cartas}
        self.redibujar()


def main():
    carpeta = localizar_cartas()
    root = tk.Tk()
    HexagramaApp(root, carpeta)
    root.mainloop()


if __name__ == "__main__":
    main()
