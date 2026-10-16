"""Copia menús del ORIGEN al DESTINO reasignando cada ítem COLLECTION/PRODUCT/PAGE al recurso del destino
por handle (sacado de la URL del ítem). Los que no existen quedan como link HTTP relativo (y se avisa).
Uso: python3 -I sync_menus.py <tienda> <menus-origen.json> <handles separados por coma>
Existentes (main-menu, footer, etc.) -> menuUpdate (reemplaza todos los ítems); nuevos -> menuCreate.
No sincronizar customer-account-main-menu: sus URLs llevan el ID de cada tienda.
"""
import json
import os
import subprocess
import sys
import tempfile

store, src, wanted = sys.argv[1], sys.argv[2], sys.argv[3].split(",")


def gql(query, variables=None, mutation=False):
    args = ["shopify", "store", "execute", "-s", store, "-j", "-q", query] + (["--allow-mutations"] if mutation else [])
    tf = None
    if variables is not None:
        tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(variables, tf, ensure_ascii=False)
        tf.close()
        args += ["--variable-file", tf.name]
    res = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if tf:
        os.unlink(tf.name)
    d = json.loads(res.stdout[res.stdout.index("{"):])
    return d.get("data", d)


def all_ids(field):
    out, after = {}, None
    while True:
        q = "query($a:String){ %s(first:250, after:$a){ pageInfo{ hasNextPage endCursor } nodes{ id handle } } }" % field
        d = gql(q, {"a": after})[field]
        out.update({n["handle"]: n["id"] for n in d["nodes"]})
        if not d["pageInfo"]["hasNextPage"]:
            return out
        after = d["pageInfo"]["endCursor"]


ids = {"COLLECTION": all_ids("collections"), "PRODUCT": all_ids("products"), "PAGE": all_ids("pages")}
prefix = {"COLLECTION": "/collections/", "PRODUCT": "/products/", "PAGE": "/pages/"}
problems = []


def convert(items):
    out = []
    for i in items:
        it = {"title": i["title"], "type": i["type"]}
        if i["type"] in ids:
            handle = (i.get("url") or "").split(prefix[i["type"]], 1)[-1].split("?")[0].strip("/")
            rid = ids[i["type"]].get(handle)
            if rid:
                it["resourceId"] = rid
            else:
                problems.append((i["title"], i["type"], handle))
                it = {"title": i["title"], "type": "HTTP", "url": prefix[i["type"]] + handle}
        elif i.get("url"):
            url = i["url"]
            if i["type"] == "HTTP" and ".myshopify.com" in url:
                url = "/" + url.split(".myshopify.com/", 1)[-1]
            it["url"] = url
        if i.get("tags"):
            it["tags"] = i["tags"]
        if i.get("items"):
            it["items"] = convert(i["items"])
        out.append(it)
    return out


data = json.load(open(src))
origin = {m["handle"]: m for m in data.get("data", data)["menus"]["nodes"]}
dest = {m["handle"]: m["id"] for m in gql("{ menus(first:50){ nodes{ id handle } } }")["menus"]["nodes"]}
for h in wanted:
    m = origin[h]
    items = convert(m["items"])
    if h in dest:
        r = gql("mutation($id:ID!,$t:String!,$h:String!,$items:[MenuItemUpdateInput!]!){ menuUpdate(id:$id,title:$t,handle:$h,items:$items){ menu{ handle } userErrors{ field message } } }",
                {"id": dest[h], "t": m["title"], "h": h, "items": items}, True)["menuUpdate"]
    else:
        r = gql("mutation($t:String!,$h:String!,$items:[MenuItemCreateInput!]!){ menuCreate(title:$t,handle:$h,items:$items){ menu{ handle } userErrors{ field message } } }",
                {"t": m["title"], "h": h, "items": items}, True)["menuCreate"]
    print(h, "OK" if not r["userErrors"] else r["userErrors"])
print("ítems sin recurso en destino (quedaron como link HTTP):", problems)
