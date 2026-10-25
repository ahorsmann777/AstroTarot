#!/usr/bin/env python3
"""Rueda de 12 secciones de 30 grados con una carta aleatoria y números romanos.

Deriva de repartir_12_signos.py, sustituyendo los símbolos zodiacales por los
números romanos del I al XII.

Autor: Alejandro Horsmann
MIT Licence
"""

import tkinter as tk

from repartir_12_signos import (
    ANG0,
    COLORES,
    PASO_SECCION,
    RuedaDoceApp,
    localizar_cartas,
    punto,
)

NUMEROS_ROMANOS = ("I", "II", "III", "IV", "V", "VI",
                   "VII", "VIII", "IX", "X", "XI", "XII")


class RuedaNumeradaApp(RuedaDoceApp):
    def __init__(self, root, carpeta_cartas):
        super().__init__(root, carpeta_cartas)
        root.title("AstroTarot — Rueda de 12 cartas numeradas")

    def dibujar_zodiaco(self):
        g = self.geo
        tam = max(10, int(20 * (g["lienzo"] / 1000.0)))
        for i, numero in enumerate(NUMEROS_ROMANOS):
            ang = ANG0 + PASO_SECCION / 2.0 - PASO_SECCION * i
            x, y = punto(g, ang, g["r_zodiaco"])
            self.canvas.create_text(
                x, y, text=numero, font=("DejaVu Sans", tam, "bold"),
                fill=COLORES["seccion"],
            )


def main():
    carpeta = localizar_cartas()
    root = tk.Tk()
    RuedaNumeradaApp(root, carpeta)
    root.mainloop()


if __name__ == "__main__":
    main()
