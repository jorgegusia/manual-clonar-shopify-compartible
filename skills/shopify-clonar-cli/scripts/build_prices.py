"""Genera correcciones de precio (productVariantsBulkUpdate) solo para variantes que difieren del origen.
Empareja por handle + opciones de la variante. Útil si la moneda del destino estuvo mal y Shopify redondeó.
Uso: python3 -I build_prices.py <productos-origen.jsonl> <productos-destino.jsonl> <precios.jsonl>
Volver a correrlo después de subir: tiene que dar 0 variantes a corregir.
"""
import json
import sys
from decimal import Decimal


def load(fn):
    prods, variants = {}, {}
    for line in open(fn):
        o = json.loads(line)
        gid = o.get("id", "")
        if gid.startswith("gid://shopify/Product/"):
            prods[gid] = o["handle"]
        elif gid.startswith("gid://shopify/ProductVariant/"):
            key = tuple(sorted((s["name"], s["value"]) for s in o["selectedOptions"]))
            variants.setdefault(o["__parentId"], {})[key] = o
    return {prods[p]: (p, v) for p, v in variants.items()}


num = lambda x: Decimal(x) if x not in (None, "") else None
origin, dest = load(sys.argv[1]), load(sys.argv[2])
lines, n = [], 0
for h, (_, ov) in origin.items():
    if h not in dest:
        continue
    pid, dv = dest[h]
    ups = [{"id": dv[k]["id"], "price": o["price"], "compareAtPrice": o.get("compareAtPrice")}
           for k, o in ov.items()
           if k in dv and (num(o["price"]) != num(dv[k]["price"]) or num(o.get("compareAtPrice")) != num(dv[k].get("compareAtPrice")))]
    if ups:
        n += len(ups)
        lines.append({"productId": pid, "variants": ups})
with open(sys.argv[3], "w") as f:
    for line in lines:
        f.write(json.dumps(line) + "\n")
print("productos a corregir:", len(lines), "variantes:", n)
