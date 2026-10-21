"""Modo B (ebooks): copia las secciones eb-* a una carpeta de tema (Horizon u otro) y escribe los JSON
que las usan, con los textos, colores y datos de la LLC de marca.json.
Uso: python3 -I armar_tema.py <marca.json> <carpeta-tema> [carpeta-plantillas]
- carpeta-tema: el tema DUPLICADO bajado con `shopify theme pull` (nunca el publicado).
- carpeta-plantillas: por defecto ../modo-b/plantillas/tema (relativa a este script).
Escribe: sections/eb-*.liquid, templates/index.json, templates/product.json,
         sections/header-group.json y sections/footer-group.json (reemplazan header y footer del tema).
Después: shopify theme push --theme ID --path <carpeta-tema> --only sections/eb-* ... (primero las secciones,
después los JSON: si no, Shopify dice que la sección no existe).
"""
import json
import os
import shutil
import sys

HEAD = "/*\n * Generado por armar_tema.py (modo B). Se puede editar desde el editor del tema.\n */\n"

marca_path, tema = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
plant = sys.argv[3] if len(sys.argv) > 3 else next((d for d in (os.path.join(here, "..", "modo-b", "plantillas", "tema"), os.path.join(here, "..", "plantillas", "tema")) if os.path.isdir(d)), "")
m = json.load(open(marca_path))
t, llc, home = m["tienda"], m["llc"], m["home"]
pal = m.get("paleta", {})
fuentes = m.get("fuentes", {})
img = m.get("imagenes", {})

faltan = [k for k in ("nombre", "codigo_descuento") if not t.get(k)] + \
         [f"llc.{k}" for k in ("nombre", "direccion", "email") if not llc.get(k)] + \
         [f"home.{k}" for k in ("titulo", "intro") if not home.get(k)]
if faltan:
    sys.exit("Faltan datos en marca.json: " + ", ".join(faltan))

os.makedirs(os.path.join(tema, "sections"), exist_ok=True)
os.makedirs(os.path.join(tema, "templates"), exist_ok=True)
for f in sorted(os.listdir(os.path.join(plant, "sections"))):
    shutil.copy(os.path.join(plant, "sections", f), os.path.join(tema, "sections", f))
    print("copiado sections/" + f)


def write(rel, data):
    with open(os.path.join(tema, rel), "w") as fh:
        fh.write(HEAD + json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("escrito " + rel)


def clean(d):
    return {k: v for k, v in d.items() if v not in (None, "")}


pct = t.get("descuento_pct", 15)
header = clean({
    "logo": img.get("logo", ""),
    "menu": "main-menu",
    "announcement_1": t.get("anuncio_1") or f"{pct}% OFF all ebooks — use code {t['codigo_descuento']} at checkout",
    "announcement_2": t.get("anuncio_2") or "Instant digital delivery — read on any device",
    "color_paper": pal.get("paper", "#F4EDEC"),
    "color_ink": pal.get("ink", "#171717"),
    "color_accent": pal.get("accent", "#60241A"),
    "color_muted": pal.get("muted", "#686868"),
    "font_serif": fuentes.get("serif", ""),
    "font_sans": fuentes.get("sans", ""),
})
write("sections/header-group.json", {
    "type": "header", "name": "Header group",
    "sections": {"eb_header": {"type": "eb-header", "settings": header}},
    "order": ["eb_header"],
})

footer = clean({
    "logo": img.get("logo_footer") or img.get("logo", ""),
    "llc_name": llc["nombre"],
    "llc_address": llc["direccion"],
    "email": llc["email"],
    "phone": llc.get("telefono") or "xxx xx xxx",
})
write("sections/footer-group.json", {
    "type": "footer", "name": "Footer group",
    "sections": {"eb_footer": {"type": "eb-footer", "settings": footer}},
    "order": ["eb_footer"],
})

blocks, order = {}, []
for i, f in enumerate(m.get("faq", []), 1):
    bid = f"faq_{i}"
    blocks[bid] = {"type": "faq", "settings": {"question": f["q"], "answer": f"<p>{f['a']}</p>"}}
    order.append(bid)
home_settings = clean({
    "kicker": home.get("kicker", ""),
    "title": home["titulo"],
    "intro": home["intro"],
    "button_label": home.get("boton", "Explore the ebooks"),
    "hero_image": img.get("hero", "") if img.get("hero", "").startswith("shopify://") else "",
    "hero_image_url": img.get("hero", "") if img.get("hero", "").startswith("http") else "",
    "library_kicker": home.get("biblioteca_kicker", ""),
    "library_title": home.get("biblioteca_titulo", ""),
    "library_text": home.get("biblioteca_texto", ""),
    "band_kicker": home.get("banda_kicker", ""),
    "band_text": home.get("banda_texto", ""),
})
write("templates/index.json", {
    "sections": {"eb_home": {"type": "eb-home", "blocks": blocks, "block_order": order, "settings": home_settings}},
    "order": ["eb_home"],
})
write("templates/product.json", {
    "sections": {"main": {"type": "eb-product", "settings": {}}},
    "order": ["main"],
})
if not llc.get("telefono"):
    print("AVISO: no hay teléfono; el footer muestra 'xxx xx xxx'. Pedírselo al usuario.")
print("Listo. Subir primero sections/eb-*.liquid y después los 4 JSON.")
