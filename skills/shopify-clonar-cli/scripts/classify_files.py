"""Decide qué archivos de Files del ORIGEN hay que subir al DESTINO.
Uso: python3 -I classify_files.py <archivos-origen.jsonl> <productos-origen.jsonl> <lista-imagenes-tema.txt> <salida.json>
- Las fotos de producto NO se suben aparte: viajan con cada producto (productSet) y si no se duplicarían.
- Se suben: imágenes referenciadas por metacampos (file_reference), imágenes del tema (shop_images) y otras.
- Los videos se listan aparte: se suben con upload_videos.py (Shopify no acepta video por URL).
"""
import collections
import json
import sys

files_src, prods_src, theme_list, out = sys.argv[1:5]
fname = lambda u: u.split("?")[0].rsplit("/", 1)[-1]
files = [json.loads(line) for line in open(files_src)]
prod_media, refs = set(), set()
for line in open(prods_src):
    o = json.loads(line)
    if o.get("mediaContentType") == "IMAGE" and (o.get("preview") or {}).get("image"):
        prod_media.add(fname(o["preview"]["image"]["url"]))
    if o.get("type") in ("file_reference", "list.file_reference"):
        v = o["value"]
        refs.update(json.loads(v) if o["type"].startswith("list") else [v])
theme = {line.strip() for line in open(theme_list) if line.strip()}

cats, upload = collections.Counter(), []
for f in files:
    if f["__typename"] == "Video":
        cats["video"] += 1
        continue
    url = f["image"]["url"] if f.get("image") else f.get("url")
    n = fname(url)
    cat = "metacampo" if f["id"] in refs else "tema" if n in theme else "foto_producto" if n in prod_media else "otro"
    cats[cat] += 1
    if cat != "foto_producto":
        upload.append({"id": f["id"], "filename": n, "url": url, "alt": f.get("alt") or "", "cat": cat})
json.dump(upload, open(out, "w"), ensure_ascii=False, indent=0)
print(dict(cats), "| imágenes a subir:", len(upload))
missing_refs = refs - {f["id"] for f in files}
print("referencias de metacampos que no existen en Files del origen:", len(missing_refs))
