#!/usr/bin/env python3
#---------------------------------------------------------#
# Este script reparte 36 de las 78 cartas del Tarot       #
# aleatoriamente en los 36 decanatos de la rueda zodiacal.#
# Autor: Alejandro Horsmann                               #
# 22/09/2026                                              #
# MIT Licence                                             #
#---------------------------------------------------------#
import math
import os
import random
import sys

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk


#<=== Ubicación de la carpeta "Cartas" ===>#

BASE = os.path.dirname(os.path.abspath(__file__))
CANDIDATOS = (
    os.path.join(BASE, "Cartas"),
    os.path.join(os.getcwd(), "Cartas"),
    os.path.join(BASE, "astrotarot", "Cartas"),
    os.path.join(os.getcwd(), "astrotarot", "Cartas"),
)

OFFSETS_UI = {
    "margen": 30,          # margen exterior mínimo de la ventana
    "barra": 100,          # alto reservado para botón + contador
    "rejilla_interior": 0.055,   # radio del círculo central (fracción del lienzo)
}


def localizar_cartas():
    for carpeta in CANDIDATOS:
        if os.path.isdir(carpeta):
            return carpeta
    print("No se encontró la carpeta 'Cartas'.", file=sys.stderr)
    sys.exit(1)


def tamano_ventana(raiz):
    """Lienzo cuadrado que cabe en la pantalla dejando márgenes y la barra."""
    ancho = raiz.winfo_screenwidth()
    alto = raiz.winfo_screenheight()
    disponible = min(
        ancho - 2 * OFFSETS_UI["margen"],
        alto - 2 * OFFSETS_UI["margen"] - OFFSETS_UI["barra"],
    )
    return max(500, int(disponible))

#<=== Dibuja rueda ===>#
def construir_geometria(lienzo):
    """Devuelve las medidas de la rueda a escala del lienzo."""
    f = lienzo / 1000.0
    centro = lienzo // 2
    r_circulo = int(455 * f)
    l_carta = int(100 * f)
    r_carta_ext = int(430 * f)
    r_carta_int = r_carta_ext - l_carta
    r_medio = (r_carta_ext + r_carta_int) / 2.0
    return {
        "lienzo": lienzo,
        "centro": centro,
        "ox": 0,
        "oy": 0,
        "r_circulo": r_circulo,
        "r_zodiaco": r_circulo + int(28 * f),
        "r_carta_ext": r_carta_ext,
        "r_carta_int": r_carta_int,
        "l_carta": l_carta,
        "r_medio": r_medio,
        "grueso_desde": int(30 * f),
        "fino_desde": int(55 * f),
        "centro_radio": int(OFFSETS_UI["rejilla_interior"] * lienzo),
    }


COLORES = {
    "fondo": "#f5f0e6",
    "punteo": "#b08968",
    "seccion": "#7a4a2b",
    "circulo": "#4a3020",
}

PASO_GRUESO = 30            # cada cuántos grados va una división gruesa
PASO_FINO = 10              # divisiones finas / punteadas
TAMANO_CARTAS = 36          # cartas que se reparten (una por porción de 10°)
ANG0 = 180.0                # sección 0° en las 9 en punto; antihorario

SIMBOLOS_ZODIACO = ("♓", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒")  # una casa adelantada


def punto(g, ang, radio):
    a = math.radians(ang)
    return (g["ox"] + g["centro"] + radio * math.cos(a),
            g["oy"] + g["centro"] + radio * math.sin(a))


class RuedaApp:
    def __init__(self, root, carpeta_cartas):
        self.root = root
        root.title("AstroTarot — Rueda de 36 cartas")
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

        # Cartas base ya redimensionadas (evita re-abrir los JPG).
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

        self.repartir()

    def _cargar(self, path):
        im = Image.open(path).convert("RGB")
        ancho, alto = im.size
        alto_nuevo = self.geo["l_carta"]
        ancho_nuevo = max(1, int(round(alto_nuevo * ancho / alto)))
        return im.resize((ancho_nuevo, alto_nuevo), Image.LANCZOS)

    def preparar(self, base, ang):
        """Recorta la carta en forma de elipse y la rota hacia afuera.

        La elipse evita las esquinas rectangulares, por lo que al rotar no
        queda ningún trozo relleno (blanco) alrededor de la carta.
        """
        max_ancho = max(20, int(math.radians(PASO_FINO) * self.geo["r_medio"] * 0.94))
        im = base
        if im.width > max_ancho:
            factor = max_ancho / im.width
            im = im.resize((max_ancho, max(1, int(im.height * factor))), Image.LANCZOS)

        ancho, alto = im.size
        mascara = Image.new("L", (ancho, alto), 0)
        ImageDraw.Draw(mascara).ellipse([0, 0, ancho - 1, alto - 1], fill=255)

        ang_pil = (-90.0 - ang) % 360.0
        im = im.rotate(ang_pil, expand=True, resample=Image.BICUBIC,
                      fillcolor=COLORES["fondo"])
        mascara = mascara.rotate(ang_pil, expand=True, resample=Image.BICUBIC)
        im.putalpha(mascara)
        return ImageTk.PhotoImage(im)

    def reiniciar_lienzo(self):
        self.fotos = []
        self.canvas.delete("all")

    def dibujar_marco(self):
        g = self.geo
        cx = g["ox"] + g["centro"]
        cy = g["oy"] + g["centro"]
        self.canvas.create_oval(
            cx - g["r_circulo"], cy - g["r_circulo"],
            cx + g["r_circulo"], cy + g["r_circulo"],
            outline=COLORES["circulo"], width=4,
        )
        for paso in range(0, 37):
            ang = ANG0 + PASO_FINO * paso
            if paso % 3 == 0:
                p0 = punto(g, ang, g["grueso_desde"])
                p1 = punto(g, ang, g["r_circulo"] - 2)
                self.canvas.create_line(
                    p0[0], p0[1], p1[0], p1[1],
                    fill=COLORES["seccion"], width=3,
                )
            else:
                p0 = punto(g, ang, g["fino_desde"])
                p1 = punto(g, ang, g["r_circulo"] - 8)
                self.canvas.create_line(
                    p0[0], p0[1], p1[0], p1[1],
                    fill=COLORES["punteo"], width=1, dash=(3, 6),
                )
        self.canvas.create_oval(
            cx - g["centro_radio"], cy - g["centro_radio"],
            cx + g["centro_radio"], cy + g["centro_radio"],
            outline=COLORES["seccion"], width=2, fill=COLORES["fondo"],
        )
        self.dibujar_zodiaco()

    def dibujar_zodiaco(self):
        """Dibuja los 12 símbolos zodiacales fuera del anillo, en el medio de
        cada sección de 30°, comenzando en las 9 en punto y en sentido antihorario."""
        g = self.geo
        tam = max(10, int(20 * (g["lienzo"] / 1000.0)))
        for i, simb in enumerate(SIMBOLOS_ZODIACO):
            ang = ANG0 + PASO_GRUESO / 2.0 - PASO_GRUESO * i
            x, y = punto(g, ang, g["r_zodiaco"])
            self.canvas.create_text(
                x, y, text=simb, font=("DejaVu Sans", tam, "bold"),
                fill=COLORES["seccion"],
            )

    def repartir(self):
        self.elegidas = random.sample(self.cartas, TAMANO_CARTAS)
        self.reparto += 1
        self.actualizar_info()
        self.redibujar()

    def redibujar(self):
        """Redibuja la rueda completa conservando el reparto actual."""
        if not self.elegidas:
            return
        self.reiniciar_lienzo()
        self.dibujar_marco()

        for indice, path in enumerate(self.elegidas):
            ang = ANG0 + PASO_FINO * indice + PASO_FINO / 2.0
            foto = self.preparar(self.base[path], ang)
            self.fotos.append(foto)
            x, y = punto(self.geo, ang, self.geo["r_medio"])
            self.canvas.create_image(x, y, image=foto, anchor="center")

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
    RuedaApp(root, carpeta)
    root.mainloop()


if __name__ == "__main__":
    main()
