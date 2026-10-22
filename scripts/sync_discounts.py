"""Copia descuentos del ORIGEN al DESTINO (automáticos y por código, tipo Basic: porcentaje o monto fijo).
Uso: python3 -I sync_discounts.py <tienda-destino> <descuentos-origen.json>
<descuentos-origen.json> sale de queries/q_discounts.graphql. Las colecciones/productos se reasignan por handle.
Saltea los que ya existen en el destino con el mismo título. Otros tipos (Bxgy, envío gratis, de apps) se avisan.
"""
import json
import subprocess
import sys
import tempfile

store, src = sys.argv[1], sys.argv[2]


def gql(query, variables=None):
    args = ["shopify", "store", "execute", "-s", store, "-j", "--allow-mutations", "-q", query]
    if variables is not None:
        tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(variables, tf, ensure_ascii=False)
        tf.close()
        args += ["--variable-file", tf.name]
    out = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
    d = json.loads(out[out.index("{"):])
    return d.get("data", d)


def ids(kind, handles):
    q = "query($q:String){ %s(first:50, query:$q){ nodes{ id handle } } }" % kind
    nodes = gql(q, {"q": " OR ".join(f"handle:{h}" for h in handles)})[kind]["nodes"]
    found = {n["handle"]: n["id"] for n in nodes}
    missing = [h for h in handles if h not in found]
    if missing:
        print("  ojo, no existen en destino:", kind, missing)
    return [found[h] for h in handles if h in found]


def gets(cg):
    v = cg["value"]
    value = ({"percentage": v["percentage"]} if v["__typename"] == "DiscountPercentage"
             else {"discountAmount": {"amount": v["amount"]["amount"], "appliesOnEachItem": v["appliesOnEachItem"]}})
    it = cg["items"]
    if it["__typename"] == "AllDiscountItems":
        items = {"all": True}
    elif it["__typename"] == "DiscountCollections":
        items = {"collections": {"add": ids("collections", [n["handle"] for n in it["collections"]["nodes"]])}}
    else:
        items = {"products": {"productsToAdd": ids("products", [n["handle"] for n in it["products"]["nodes"]])}}
    return {"value": value, "items": items}


def minimum(m):
    if not m:
        return None
    if m["__typename"] == "DiscountMinimumQuantity":
        return {"quantity": {"greaterThanOrEqualToQuantity": m["greaterThanOrEqualToQuantity"]}}
    return {"subtotal": {"greaterThanOrEqualToSubtotal": m["greaterThanOrEqualToSubtotal"]["amount"]}}


existing = {n["discount"].get("title") for n in gql("{ discountNodes(first:100){ nodes{ discount{ ... on DiscountAutomaticBasic{ title } ... on DiscountCodeBasic{ title } } } } }")["discountNodes"]["nodes"]}
data = json.load(open(src))
for n in data.get("data", data)["discountNodes"]["nodes"]:
    d = n["discount"]
    t = d["__typename"]
    if d.get("title") in existing:
        print("ya existe:", d["title"])
        continue
    if t not in ("DiscountAutomaticBasic", "DiscountCodeBasic"):
        print("TIPO NO SOPORTADO, crearlo a mano:", t, d.get("title"))
        continue
    inp = {"title": d["title"], "startsAt": d["startsAt"], "endsAt": d["endsAt"],
           "combinesWith": d["combinesWith"], "customerGets": gets(d["customerGets"])}
    mr = minimum(d.get("minimumRequirement"))
    if mr:
        inp["minimumRequirement"] = mr
    if t == "DiscountAutomaticBasic":
        r = gql("mutation($d:DiscountAutomaticBasicInput!){ discountAutomaticBasicCreate(automaticBasicDiscount:$d){ automaticDiscountNode{ id } userErrors{ field message } } }",
                {"d": inp})["discountAutomaticBasicCreate"]
    else:
        inp.update({"code": d["codes"]["nodes"][0]["code"], "usageLimit": d["usageLimit"],
                    "appliesOncePerCustomer": d["appliesOncePerCustomer"], "customerSelection": {"all": True}})
        r = gql("mutation($d:DiscountCodeBasicInput!){ discountCodeBasicCreate(basicCodeDiscount:$d){ codeDiscountNode{ id } userErrors{ field message } } }",
                {"d": inp})["discountCodeBasicCreate"]
    print(d["title"], "->", r["userErrors"] or "OK")
