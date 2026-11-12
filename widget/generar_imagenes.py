"""python3 widget/generar_imagenes.py · Logos de ejemplo (color plano, sin dependencias). Reemplázalos por los tuyos
con los mismos nombres y tamaños: Kommo los exige así."""
import struct, zlib
TAMANOS = {"logo.png": (130, 100), "logo_min.png": (84, 84), "logo_small.png": (108, 108),
           "logo_medium.png": (240, 84), "logo_main.png": (400, 272), "slideshow_1_es.png": (1200, 800)}
def png(ancho, alto, rgb=(47, 107, 255)):
    fila = b"\x00" + bytes(rgb) * ancho
    datos = zlib.compress(fila * alto, 9)
    trozo = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)) + \
        trozo(b"IDAT", datos) + trozo(b"IEND", b"")
import os, subprocess
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images"))
for nombre, (w, h) in TAMANOS.items():
    open(nombre, "wb").write(png(w, h))
# Kommo pide el slideshow en JPG: en Mac se convierte con sips (en Linux: convert de ImageMagick).
subprocess.run(["sips", "-s", "format", "jpeg", "slideshow_1_es.png", "--out", "slideshow_1_es.jpg"], capture_output=True)
os.remove("slideshow_1_es.png")
