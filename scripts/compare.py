"""Compara ORIGEN vs DESTINO (productos y colecciones exportados con queries/q_prod.graphql y q_col.graphql).
Uso: python3 -I compare.py <productos-origen> <productos-destino> <colecciones-origen> <colecciones-destino> [mapa-archivos.json]
Revisa: handles faltantes/sobrantes, título, plantilla, estado, variantes, precios, cantidad de imágenes,
metacampos (claves y valores; con el mapa compara también file_reference) y productos/orden de cada colección.
El objetivo del loop es que imprima "NINGUNA" en ambos.
"""
import json
import sys
from decimal import Decimal

fmap = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else {}


def load(fn, kind):
    objs, kids = {}, {}
    for line in open(fn):
        o = json.loads(line)
        if f"/{kind}/" in o.get("id", ""):
            objs[o["id"]] = o
            kids[o["id"]] = []
        else:
            kids[o["__parentId"]].append(o)
    return {o["handle"]: (o, kids[i]) for i, o in objs.items()}


def mf_value(x, remap):
    v = x["value"]
    if x["type"].startswith("list."):
        v = json.loads(v)
        if remap and x["type"] == "list.file_reference":
            v = [fmap.get(i, i) for i in v]
    elif remap and x["type"] == "file_reference":
        v = fmap.get(v, v)
    return v


def vkey(x):
    return tuple(sorted((s["name"], s["value"]) for s in x["selectedOptions"]))


def dec(x):
    return Decimal(x) if x else None


for kind, a, b in (("Product", sys.argv[1], sys.argv[2]), ("Collection", sys.argv[3], sys.argv[4])):
    O, D = load(a, kind), load(b, kind)
    print(f"== {kind}: origen {len(O)} destino {len(D)}")
    print("   faltan en destino:", sorted(set(O) - set(D)))
    print("   sobran en destino:", sorted(set(D) - set(O)))
    issues = {}
    for h in set(O) & set(D):
        (o, ok), (d, dk) = O[h], D[h]
        chk = {"title": (o["title"], d["title"]),
               "templateSuffix": (o.get("templateSuffix") or None, d.get("templateSuffix") or None)}
        if kind == "Product":
            ov = {vkey(x): x for x in ok if "ProductVariant" in x.get("id", "")}
            dv = {vkey(x): x for x in dk if "ProductVariant" in x.get("id", "")}
            chk["status"] = (o["status"], d["status"])
            chk["variantes"] = (sorted(ov), sorted(dv))
            chk["precios"] = ([(dec(ov[k]["price"]), dec(ov[k]["compareAtPrice"])) for k in sorted(ov) if k in dv],
                              [(dec(dv[k]["price"]), dec(dv[k]["compareAtPrice"])) for k in sorted(ov) if k in dv])
            chk["imagenes"] = (sum(1 for x in ok if "mediaContentType" in x), sum(1 for x in dk if "mediaContentType" in x))
            om = {(x["namespace"], x["key"]): mf_value(x, True) for x in ok if "key" in x}
            dm = {(x["namespace"], x["key"]): mf_value(x, False) for x in dk if "key" in x}
            chk["metacampos"] = (om, dm)
        else:
            chk["productos"] = ([x["handle"] for x in ok], [x["handle"] for x in dk])
            chk["reglas"] = (json.dumps(o.get("ruleSet"), sort_keys=True), json.dumps(d.get("ruleSet"), sort_keys=True))
        for k, (x, y) in chk.items():
            if x != y:
                issues.setdefault(k, []).append(h)
    print("   diferencias:", {k: (len(v), v[:4]) for k, v in issues.items()} or "NINGUNA")
