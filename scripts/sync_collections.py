"""Sincroniza colecciones MANUALES del destino con el origen: crea las faltantes (y las publica) y deja
los mismos productos en el mismo orden (agrega faltantes en orden, quita sobrantes).
Uso: python3 -I sync_collections.py <tienda> <colecciones-origen.jsonl> <colecciones-destino.jsonl> <mapa-productos.json> <publicationId>
mapa-productos.json: {handle: gid del producto en destino} (sale del resultado del bulk productSet).
Colecciones AUTOMÁTICAS con reglas por metacampo: crear antes las definiciones (metafieldDefinitionCreate con
smartCollectionCondition) y usar conditionObjectId = id de la definición en destino.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

store, src, dst, pmap_path, pub = sys.argv[1:6]
pmap = json.load(open(pmap_path))


def gql(query, variables):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(variables, tf, ensure_ascii=False)
    try:
        for attempt in range(4):
            res = subprocess.run(["shopify", "store", "execute", "-s", store, "--allow-mutations", "-j",
                                  "--variable-file", tf.name, "-q", query],
                                 capture_output=True, text=True, stdin=subprocess.DEVNULL)
            if "{" in res.stdout:
                d = json.loads(res.stdout[res.stdout.index("{"):])
                return d.get("data", d)
            time.sleep(5)
    finally:
        os.unlink(tf.name)
    raise RuntimeError((res.stdout + res.stderr)[-500:])


def load(fn):
    objs, kids = {}, {}
    for line in open(fn):
        o = json.loads(line)
        if "/Collection/" in o.get("id", ""):
            objs[o["id"]] = o
            kids[o["id"]] = []
        else:
            kids[o["__parentId"]].append(o["handle"])
    return {o["handle"]: (o, kids[i]) for i, o in objs.items()}


O, D = load(src), load(dst)
for handle, (o, oprods) in O.items():
    if o.get("ruleSet"):
        continue  # automática: se llena sola por reglas
    if handle not in D:
        inp = {"handle": handle, "title": o["title"], "descriptionHtml": o.get("descriptionHtml") or "",
               "sortOrder": o["sortOrder"]}
        if o.get("templateSuffix"):
            inp["templateSuffix"] = o["templateSuffix"]
        seo = {k: v for k, v in (o.get("seo") or {}).items() if v}
        if seo:
            inp["seo"] = seo
        if o.get("image"):
            inp["image"] = {"src": o["image"]["url"], "altText": o["image"].get("altText") or ""}
        r = gql("mutation($input:CollectionInput!){ collectionCreate(input:$input){ collection{ id } userErrors{ field message } } }",
                {"input": inp})["collectionCreate"]
        if r["userErrors"]:
            print("ERROR crear", handle, r["userErrors"])
            continue
        cid, dprods = r["collection"]["id"], []
        gql("mutation($id:ID!,$p:[PublicationInput!]!){ publishablePublish(id:$id,input:$p){ userErrors{ message } } }",
            {"id": cid, "p": [{"publicationId": pub}]})
        print("creada", handle)
    else:
        cid, dprods = D[handle][0]["id"], D[handle][1]
    extra = [pmap[h] for h in dprods if h not in oprods and h in pmap]
    if extra:
        gql("mutation($id:ID!,$p:[ID!]!){ collectionRemoveProducts(id:$id, productIds:$p){ userErrors{ message } } }",
            {"id": cid, "p": extra})
        print("quitados", handle, len(extra))
    missing = [h for h in oprods if h not in dprods]
    nomap = [h for h in missing if h not in pmap]
    if nomap:
        print("SIN PRODUCTO EN DESTINO", handle, nomap)
    ids = [pmap[h] for h in missing if h in pmap]
    for s in range(0, len(ids), 250):
        r = gql("mutation($id:ID!,$p:[ID!]!){ collectionAddProducts(id:$id, productIds:$p){ userErrors{ field message } } }",
                {"id": cid, "p": ids[s:s + 250]})["collectionAddProducts"]
        if r["userErrors"]:
            print("ERROR agregar", handle, r["userErrors"])
    if ids:
        print(f"{handle}: +{len(ids)} productos")
