"""Convierte el bulk export de productos del ORIGEN en JSONL de productSet para el DESTINO.
Uso: python3 -I build_productset.py <productos-origen.jsonl> <salida.jsonl> [--map mapa-archivos.json] [--location gid://shopify/Location/N] [handle ...]
- Sin handles: todos los productos. Con handles: solo esos (ej. los que fallaron en Matrixify).
- --map: {id_archivo_origen: id_archivo_destino}. Reapunta metacampos file_reference / list.file_reference.
  Sin el mapa, esos metacampos quedarían apuntando a archivos del origen y Shopify los rechaza.
- --location: ubicación del DESTINO donde cargar el stock (inventoryQuantity del origen). Sin ella no se carga stock.
- La foto de cada variante (ej. una por color) viaja si el export trae `image { url }` en las variantes.
"""
import json
import sys

args = sys.argv[1:]
src, dst = args[0], args[1]
fmap, only, location = {}, set(), None
rest = args[2:]
while rest:
    a = rest.pop(0)
    if a == "--map":
        fmap = json.load(open(rest.pop(0)))
    elif a == "--location":
        location = rest.pop(0)
    else:
        only.add(a)


def path(url):
    return (url or "").split("?")[0]

products, order = {}, []
for line in open(src):
    o = json.loads(line)
    gid = o.get("id", "")
    if gid.startswith("gid://shopify/Product/"):
        o["_v"], o["_m"], o["_f"] = [], [], []
        products[gid] = o
        order.append(gid)
    elif gid.startswith("gid://shopify/ProductVariant/"):
        products[o["__parentId"]]["_v"].append(o)
    elif "key" in o and "namespace" in o:
        products[o["__parentId"]]["_m"].append(o)
    else:
        products[o["__parentId"]]["_f"].append(o)

unmapped = 0
with open(dst, "w") as out:
    for gid in order:
        p = products[gid]
        if only and p["handle"] not in only:
            continue
        metafields = []
        for m in p["_m"]:
            mf = {k: m[k] for k in ("namespace", "key", "type", "value")}
            if mf["type"] in ("file_reference", "list.file_reference"):
                ids = json.loads(mf["value"]) if mf["type"].startswith("list") else [mf["value"]]
                new = [fmap.get(i) for i in ids]
                unmapped += sum(1 for x in new if not x)
                new = [x for x in new if x]
                if not new:
                    continue
                mf["value"] = json.dumps(new) if mf["type"].startswith("list") else new[0]
            metafields.append(mf)
        inp = {
            "handle": p["handle"], "title": p["title"], "descriptionHtml": p["descriptionHtml"],
            "vendor": p["vendor"], "productType": p["productType"], "tags": p["tags"], "status": p["status"],
            "productOptions": [{"name": o["name"], "values": [{"name": v} for v in o["values"]]} for o in p["options"]],
            "metafields": metafields,
            "files": [{"originalSource": m["preview"]["image"]["url"], "alt": m.get("alt") or "", "contentType": "IMAGE"}
                      for m in p["_f"] if m.get("mediaContentType") == "IMAGE" and (m.get("preview") or {}).get("image")],
            "variants": [],
        }
        if p.get("templateSuffix"):
            inp["templateSuffix"] = p["templateSuffix"]
        seo = {k: v for k, v in (p.get("seo") or {}).items() if v}
        if seo:
            inp["seo"] = seo
        for v in p["_v"]:
            it = v.get("inventoryItem") or {}
            var = {"optionValues": [{"optionName": s["name"], "name": s["value"]} for s in v["selectedOptions"]],
                   "price": v["price"], "taxable": v["taxable"], "inventoryPolicy": v["inventoryPolicy"],
                   "inventoryItem": {"tracked": it.get("tracked", False), "requiresShipping": it.get("requiresShipping", True)}}
            w = ((it.get("measurement") or {}).get("weight")) or None
            if w and w.get("value") is not None:
                var["inventoryItem"]["measurement"] = {"weight": {"unit": w["unit"], "value": w["value"]}}
            for k in ("compareAtPrice", "sku", "barcode"):
                if v.get(k):
                    var[k] = v[k]
            img = path((v.get("image") or {}).get("url"))
            same = [f for f in inp["files"] if path(f["originalSource"]) == img]
            if img and same:
                var["file"] = same[0]
            if location and it.get("tracked") and v.get("inventoryQuantity") is not None:
                var["inventoryQuantities"] = [{"locationId": location, "name": "available", "quantity": v["inventoryQuantity"]}]
            inp["variants"].append(var)
        out.write(json.dumps({"input": inp}, ensure_ascii=False) + "\n")
print("productos:", len(only) if only else len(order), "| referencias de archivo sin mapear:", unmapped)
