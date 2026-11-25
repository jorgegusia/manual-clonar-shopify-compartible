"""Arma las imágenes de MARCA para Shop / Configuración → Marca / checkout, a partir del logo del tema (sin IA ni costo).
Uso (python3 SIN -I: necesita Pillow del usuario):
  python3 armar_marca_shop.py --logo assets/logo.png --icono assets/favicon-512.png --salida marca-shop/ \
      --productos imagenes-tema/hero1.png,imagenes-tema/hero2.png,imagenes-tema/hero3.png \
      [--main "#0b3bb3"] [--dark "#0a1f5c"]
Genera en --salida:
  logo-fondo-color.png   1200x400  logo sobre el color de marca (para "Logotipo predeterminado" si el logo es claro)
  logo-checkout.png      logo con lo BLANCO pasado al color oscuro (para el checkout, que tiene fondo blanco)
  logo-cuadrado.png      el ícono cuadrado (copia de --icono)
  portada.png            1920x1080 fondo de marca con rayos + logo arriba + hasta 3 productos (PNG sin fondo) abajo
Después: subirlas a Files con upload_videos.py TIENDA <carpeta> <carpeta>/subidas.json IMAGE.
- Configuración → Marca (logo, cuadrado, portada, colores, eslogan, descripción) NO tiene API: la carga el usuario
  eligiendo las imágenes ya subidas en Archivos.
- Logo del checkout: por API (checkoutBrandingUpsert) SOLO en plan Plus o tienda de desarrollo. En Basic/Shopify/Advanced
  lo carga el usuario en Configuración → Checkout → Personalizar → Logotipo.
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--logo", required=True); ap.add_argument("--icono", required=True); ap.add_argument("--salida", required=True)
ap.add_argument("--productos", default=""); ap.add_argument("--main", default="#0b3bb3"); ap.add_argument("--dark", default="#0a1f5c")
a = ap.parse_args()
os.makedirs(a.salida, exist_ok=True)


def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


MAIN, DARK, WHITE = rgb(a.main), rgb(a.dark), (255, 255, 255)


def fondo(W, H, cy=0.6):
    b = Image.new("RGB", (W, H), DARK)
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g); rr = int(max(W, H) * 0.8)
    for r in range(rr, 0, -8):
        gd.ellipse([W / 2 - r, H * cy - r, W / 2 + r, H * cy + r], fill=int(255 * (1 - r / rr) ** 0.6))
    b = Image.composite(Image.new("RGB", (W, H), MAIN), b, g.filter(ImageFilter.GaussianBlur(40)))
    ray = Image.new("L", (W, H), 0); rd = ImageDraw.Draw(ray); cx, c2 = W / 2, H * cy
    for i in range(30):
        a1, a2 = math.radians(i * 12), math.radians(i * 12 + 5)
        rd.polygon([(cx, c2), (cx + 3000 * math.cos(a1), c2 + 3000 * math.sin(a1)),
                    (cx + 3000 * math.cos(a2), c2 + 3000 * math.sin(a2))], fill=24)
    return Image.composite(Image.new("RGB", (W, H), WHITE), b, ray)


def pegar(base, src, bw, bh, cx, bottom):
    p = Image.open(src).convert("RGBA"); p.thumbnail((bw, bh))
    x, y = int(cx - p.width / 2), int(bottom - p.height)
    sh = Image.new("RGBA", p.size, (0, 0, 0, 0)); sh.putalpha(p.split()[3].point(lambda v: int(v * .5)))
    base.paste(Image.new("RGB", p.size, (0, 0, 20)), (x + 12, y + 24), sh.filter(ImageFilter.GaussianBlur(20)))
    base.paste(p, (x, y), p)


logo = Image.open(a.logo).convert("RGBA")
# 1) logo sobre el color de marca
L = Image.new("RGB", (1200, 400), MAIN); lg = logo.copy(); lg.thumbnail((1040, 240))
L.paste(lg, ((1200 - lg.width) // 2, (400 - lg.height) // 2), lg); L.save(os.path.join(a.salida, "logo-fondo-color.png"), optimize=True)
# 2) logo para fondo blanco: blanco -> color oscuro
lc = logo.copy(); px = lc.load()
for y in range(lc.height):
    for x in range(lc.width):
        r, g, b, al = px[x, y]
        if al and r > 200 and g > 200 and b > 200:
            px[x, y] = (*DARK, al)
lc.save(os.path.join(a.salida, "logo-checkout.png"), optimize=True)
# 3) logo cuadrado
Image.open(a.icono).save(os.path.join(a.salida, "logo-cuadrado.png"), optimize=True)
# 4) portada 1920x1080
C = fondo(1920, 1080, 0.7)
lg2 = logo.copy(); lg2.thumbnail((900, 200)); C.paste(lg2, ((1920 - lg2.width) // 2, 70), lg2)
prods = [p for p in a.productos.split(",") if p]
lugares = {1: [(960, 820, 700)], 2: [(620, 760, 620), (1300, 760, 620)], 3: [(400, 620, 560), (1520, 640, 560), (960, 820, 700)]}
for src, (cx, bw, bh) in zip(prods[:3] if len(prods) < 3 else [prods[0], prods[1], prods[2]], lugares.get(min(len(prods), 3), [])):
    pegar(C, src, bw, bh, cx, 1050)
C.save(os.path.join(a.salida, "portada.png"), optimize=True)
print("listo:", sorted(os.listdir(a.salida)))
