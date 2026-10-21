"""Modo B: analiza una tienda Shopify de REFERENCIA sin acceso al admin, solo con lo público.
Uso: python3 -I analizar_referencia.py <url-tienda> <carpeta-salida>
Baja: home, /products.json, /collections.json, la ficha del primer producto y /cart.
Saca: tema base (Shopify.theme), secciones de cada página en orden, títulos, colores más usados,
variables CSS de color, tipografías, productos (título, tipo, precio, tags, tamaño de imagen) y textos
del footer (para detectar la LLC de la referencia y NO copiarla).
Escribe <salida>/analisis.json y <salida>/ANALISIS.md. Las capturas de pantalla se sacan aparte con el navegador.
Nada de lo bajado se ejecuta: es solo texto para leer.
"""
import collections
import html
import json
import os
import re
import sys
import urllib.request

base, out = sys.argv[1].rstrip("/"), sys.argv[2]
if not base.startswith("http"):
    base = "https://" + base
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def get(path):
    try:
        req = urllib.request.Request(base + path, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", 0), ""


def text(s):
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", s).split()))


def secciones(page):
    return [re.sub(r"^(sections|template)--\d+__", "", x)
            for x in re.findall(r'id="shopify-section-([^"]+)"', page)]


def titulos(page):
    res = []
    for tag, body in re.findall(r"<(h[1-3])[^>]*>(.*?)</\1>", page, re.S):
        t = text(body)
        if t and t not in ("Your cart is empty", "Search"):
            res.append(f"{tag}: {t[:110]}")
    return res


res = {"url": base}
st, home = get("/")
res["home_status"] = st
if st != 200 or not home:
    json.dump(res, open(os.path.join(out, "analisis.json"), "w"), indent=2)
    sys.exit(f"La home respondió {st}. Si es 401/password, la tienda tiene contraseña; si es 0/409/1001, el dominio no funciona.")
open(os.path.join(out, "home.html"), "w").write(home)
m = re.search(r"Shopify\.theme\s*=\s*(\{.*?\});", home)
res["tema"] = json.loads(m.group(1)) if m else None
res["password"] = "/password" in home and "template-password" in home
res["secciones_home"] = secciones(home)
res["titulos_home"] = titulos(home)

estilos = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", home, re.S)) + " " + \
          " ".join(re.findall(r'style="([^"]*)"', home))
hexes = collections.Counter(h.upper() for h in re.findall(r"#[0-9a-fA-F]{6}\b", estilos))
res["colores_mas_usados"] = hexes.most_common(15)
res["variables_color"] = sorted(set(re.findall(r"(--[\w-]*(?:color|bg|ink|paper|accent|primary|green|text)[\w-]*)\s*:\s*(#[0-9a-fA-F]{3,8})", estilos)))[:40]
fuentes = collections.Counter(f.strip().strip("'\"") for f in re.findall(r"font-family\s*:\s*([^;}{]+)", estilos))
res["tipografias"] = fuentes.most_common(10)
res["google_fonts"] = sorted(set(re.findall(r"fonts\.(?:googleapis|shopifycdn)\.com/[^\"' )]+", home)))[:10]

st, pj = get("/products.json?limit=250")
productos = []
if st == 200:
    for p in json.loads(pj).get("products", []):
        img = p["images"][0] if p.get("images") else {}
        productos.append({
            "titulo": p["title"], "handle": p["handle"], "tipo": p.get("product_type"),
            "precios": [v["price"] for v in p.get("variants", [])], "tags": p.get("tags"),
            "imagenes": len(p.get("images", [])), "imagen_tamano": [img.get("width"), img.get("height")],
            "descripcion_inicio": text(p.get("body_html") or "")[:220],
        })
res["productos"] = productos
st, cj = get("/collections.json")
res["colecciones"] = [c["handle"] for c in json.loads(cj).get("collections", [])] if st == 200 else []

if productos:
    st, prod = get("/products/" + productos[0]["handle"])
    res["secciones_producto"] = secciones(prod)
    res["titulos_producto"] = titulos(prod)
st, cart = get("/cart")
res["secciones_carrito"] = secciones(cart)
sin_codigo = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", home, flags=re.S)
footer = re.search(r'id="shopify-section-[^"]*footer[^"]*".*?(?=id="shopify-section-|</body>)', sin_codigo, re.S) \
    or re.search(r"<footer.*?</footer>", sin_codigo, re.S)
res["footer_texto"] = text(footer.group(0).split(">", 1)[-1])[:900] if footer else ""
res["menu_links"] = sorted(set(re.findall(r'<a[^>]+href="(/(?:pages|collections|policies|products)[^"#?]*)"', home)))[:40]
json.dump(res, open(os.path.join(out, "analisis.json"), "w"), ensure_ascii=False, indent=2)

md = [f"# Análisis de {base}", ""]
tema = res["tema"] or {}
md += [f"- **Tema base:** {tema.get('schema_name')} {tema.get('schema_version')} (nombre: {tema.get('name')})",
       f"- **Contraseña:** {'sí' if res['password'] else 'no'}",
       f"- **Secciones de la home:** {', '.join(res['secciones_home'])}",
       f"- **Secciones de producto:** {', '.join(res.get('secciones_producto', []))}",
       f"- **Secciones del carrito:** {', '.join(res['secciones_carrito'])}",
       "", "## Textos de la home"] + [f"- {x}" for x in res["titulos_home"]]
md += ["", "## Colores (más usados en los estilos)"] + [f"- `{c}` × {n}" for c, n in res["colores_mas_usados"]]
md += ["", "## Variables de color"] + [f"- `{k}: {v}`" for k, v in res["variables_color"]]
md += ["", "## Tipografías"] + [f"- {f} × {n}" for f, n in res["tipografias"]]
md += ["", "## Productos", "", "| Título | Tipo | Precio | Tags | Imagen |", "|---|---|---|---|---|"]
md += [f"| {p['titulo']} | {p['tipo']} | {', '.join(p['precios'])} | {', '.join(p['tags'])} | {p['imagen_tamano'][0]}×{p['imagen_tamano'][1]} |" for p in productos]
md += ["", "## Footer (datos de la referencia: NO copiar)", "", res["footer_texto"], "",
       "## Links internos", ""] + [f"- {x}" for x in res["menu_links"]]
open(os.path.join(out, "ANALISIS.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md[:8]))
print(f"... {len(productos)} productos. Ver {out}/ANALISIS.md")
