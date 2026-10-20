"""Modo B (ebooks): genera las imágenes de la tienda con Nano Banana (API de Gemini de Google).
Uso:
  python3 -I generar_imagenes.py <marca.json> <carpeta-salida> [--solo portadas|hero|logos|<archivo>] [--modelo M]
                                 [--tamano 1K|2K|4K] [--rehacer] [--prueba]
  python3 -I generar_imagenes.py --listar        (modelos de imagen que habilita tu key)
- La key se lee de la variable GEMINI_API_KEY o del archivo ~/.config/gemini/api_key. Nunca se imprime.
- Arma los prompts con los datos de marca.json (ver prompts-imagenes.md) y genera:
    portada-<handle>.png  ×6 (1:1)   <slug>-hero.png (3:2)   <slug>-logo-1.png y <slug>-logo-2.png (21:9)
- --prueba: no llama a la API; escribe pedidos.json con los prompts y muestra cantidad y costo estimado.
- Reanudable: si el archivo ya existe lo saltea (salvo --rehacer). Reintenta los 429 (límite) esperando.
Campos que necesita en marca.json: tienda.nombre, tienda.slug, tienda.icono, tienda.subtitulo, paleta,
productos[].titulo/handle/objetos (+ top), home.objetos_hero.
Después: revisar las imágenes (texto bien escrito), renombrar el logo elegido a <slug>-logo.png y subir con
  python3 -I upload_videos.py TIENDA <carpeta> <carpeta>/subidas.json IMAGE
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta"
MODELO = "gemini-3-pro-image"  # Nano Banana Pro (estable). Ver opciones con --listar (Nano Banana 2: gemini-3.1-flash-image)
PRO = {"1K": 0.134, "2K": 0.134, "4K": 0.24}
PRECIOS = {"gemini-3-pro-image": PRO, "gemini-3-pro-image-preview": PRO, "gemini-2.5-flash-image": 0.039}

PORTADA = ("Premium product mockup of a single hardcover book standing upright, slightly angled to the left, centered on "
           "a seamless plain background in {paper} with a soft natural shadow. Square 1:1, minimal editorial style. "
           "Book cover: the top third is a light {paper} band with the title \"{titulo}\" in an elegant dark serif font "
           "(color {ink}) and below it the small uppercase line \"DIGITAL EDITION\". The lower two thirds show a flat, "
           "graphic illustration of {objetos} in monochrome tones of {accent} and muted brown, paper-cut style. "
           "Thick book spine in {accent}. No other text, no logos, no people. Spell the title exactly as written.")
PORTADA_TOP = ("Premium product mockup of a set of three hardcover books standing side by side, slightly angled, centered "
               "on a seamless plain background in {paper} with a soft natural shadow. Square 1:1, minimal editorial style. "
               "The front book cover: the top third is a light {paper} band with the title \"{titulo}\" in an elegant dark "
               "serif font (color {ink}) and below it the small uppercase line \"COMPLETE COLLECTION\". The lower part shows "
               "a flat, graphic illustration of {objetos} in monochrome tones of {accent} and muted brown, paper-cut style. "
               "Book spines in {accent}. No other text, no logos, no people. Spell the title exactly as written.")
HERO = ("Top-down flat lay of {objetos} arranged artfully on a {paper} surface, monochrome palette of {accent}, deep brown "
        "and {paper}, paper-cut craft aesthetic, soft diffused natural light, high detail, editorial photography, "
        "landscape 3:2, important objects near the center. No text, no letters, no logos, no faces.")
LOGO = ("Minimal brand logo centered on a pure white background (#FFFFFF): a simple thin-line icon of {icono} in {ink} "
        "on the left, and the wordmark \"{nombre}\" in an elegant serif font in {ink}, with the small uppercase subtitle "
        "\"{subtitulo}\" in a light sans-serif underneath. Flat vector style, generous spacing, no other elements, "
        "no shadows, no mockup. Spell the words exactly as written.")


def leer_key():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    p = os.path.expanduser("~/.config/gemini/api_key")
    if not k and os.path.exists(p):
        k = open(p).read().strip()
    if not k:
        sys.exit("No encontré la API key: guardala en ~/.config/gemini/api_key (ver manual modo B §5).")
    return k


def llamar(key, metodo, ruta, cuerpo=None):
    req = urllib.request.Request(API + ruta, method=metodo, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                                 data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


args = sys.argv[1:]
if args[:1] == ["--listar"]:
    data = llamar(leer_key(), "GET", "/models?pageSize=200")
    for mo in data.get("models", []):
        if "image" in mo["name"]:
            print(mo["name"].split("/")[-1], "-", mo.get("displayName", ""))
    sys.exit(0)


def opt(nombre, defecto=None):
    if nombre in args:
        i = args.index(nombre)
        valor = args[i + 1]
        del args[i:i + 2]
        return valor
    return defecto


solo, modelo, tamano = opt("--solo"), opt("--modelo", MODELO), opt("--tamano", "2K")
rehacer, prueba = "--rehacer" in args, "--prueba" in args
args = [a for a in args if a not in ("--rehacer", "--prueba")]
marca_path, salida = args[0], args[1]
m = json.load(open(marca_path))
t, pal = m["tienda"], m.get("paleta", {})
colores = {"paper": pal.get("paper", "#F4EDEC"), "ink": pal.get("ink", "#171717"), "accent": pal.get("accent", "#60241A")}

faltan = [f"tienda.{k}" for k in ("nombre", "slug", "icono", "subtitulo") if not t.get(k)]
faltan += [f"productos[{p.get('handle', '?')}].objetos" for p in m.get("productos", []) if not p.get("objetos")]
if not m.get("home", {}).get("objetos_hero"):
    faltan.append("home.objetos_hero")
if faltan:
    sys.exit("Faltan datos en marca.json: " + ", ".join(faltan))

pedidos = []
for p in m["productos"]:
    plantilla = PORTADA_TOP if p.get("top") else PORTADA
    pedidos.append({"archivo": f"portada-{p['handle']}", "grupo": "portadas", "aspecto": "1:1",
                    "prompt": plantilla.format(titulo=p["titulo"], objetos=p["objetos"], **colores)})
pedidos.append({"archivo": f"{t['slug']}-hero", "grupo": "hero", "aspecto": "3:2",
                "prompt": HERO.format(objetos=m["home"]["objetos_hero"], **colores)})
for n in (1, 2):
    pedidos.append({"archivo": f"{t['slug']}-logo-{n}", "grupo": "logos", "aspecto": "21:9",
                    "prompt": LOGO.format(icono=t["icono"], nombre=t["nombre"], subtitulo=t["subtitulo"], **colores)})
if solo:
    pedidos = [x for x in pedidos if solo in (x["grupo"], x["archivo"])]

os.makedirs(salida, exist_ok=True)
json.dump(pedidos, open(os.path.join(salida, "pedidos.json"), "w"), ensure_ascii=False, indent=2)
existentes = {os.path.splitext(f)[0] for f in os.listdir(salida)}
pendientes = [x for x in pedidos if rehacer or x["archivo"] not in existentes]
precio = PRECIOS.get(modelo, 0)
precio = precio.get(tamano, 0) if isinstance(precio, dict) else precio
print(f"Modelo {modelo} {tamano}: {len(pendientes)} imágenes a generar · costo estimado US$ {len(pendientes) * precio:.2f}")
if prueba:
    for x in pendientes:
        print(" -", x["archivo"], x["aspecto"])
    sys.exit(0)

key = leer_key()
config = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": None}}
resultado_path = os.path.join(salida, "resultado.json")
resultado = json.load(open(resultado_path)) if os.path.exists(resultado_path) else {}
for x in pendientes:
    config["imageConfig"]["aspectRatio"] = x["aspecto"]
    if "pro" in modelo or "-3" in modelo:
        config["imageConfig"]["imageSize"] = tamano
    cuerpo = {"contents": [{"parts": [{"text": x["prompt"]}]}], "generationConfig": config}
    for intento in range(6):
        try:
            data = llamar(key, "POST", f"/models/{modelo}:generateContent", cuerpo)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 503) and intento < 5:
                espera = 20 * (intento + 1)
                print(f"   {x['archivo']}: error {e.code}, espero {espera}s y reintento")
                time.sleep(espera)
                continue
            sys.exit(f"{x['archivo']}: error {e.code}: {msg}")
    partes = [p for c in data.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
    if not partes:
        print(f"   {x['archivo']}: la API no devolvió imagen ({json.dumps(data)[:200]}). Reintentar con --solo {x['archivo']}")
        continue
    inline = partes[0]["inlineData"]
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(inline.get("mimeType"), ".png")
    destino = os.path.join(salida, x["archivo"] + ext)
    open(destino, "wb").write(base64.b64decode(inline["data"]))
    resultado[x["archivo"] + ext] = {"modelo": modelo, "tamano": tamano, "aspecto": x["aspecto"]}
    json.dump(resultado, open(resultado_path, "w"), indent=2)
    print(f"OK {x['archivo']}{ext}")
    time.sleep(3)
print(f"Listo: {salida}. Revisar cada imagen (texto bien escrito) antes de subir.")
