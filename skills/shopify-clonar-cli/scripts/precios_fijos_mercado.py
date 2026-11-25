"""Precios FIJOS en otra moneda para un mercado = el MISMO NÚMERO que en la moneda de la tienda ($49.99 → £49.99).
Uso:
  python3 -I precios_fijos_mercado.py TIENDA --mercado gid://shopify/Market/N --moneda GBP [--lista gid://shopify/PriceList/N]
- Sin --lista: crea un catálogo del mercado (sin publicación: los productos siguen según el canal) y una lista de precios
  en esa moneda, y la imprime. Con --lista: reusa la existente (para cargar productos NUEVOS o cambios de precio: volver a correrlo).
- Carga price + compareAtPrice de TODAS las variantes (bulk de productVariants), de a 250 por llamada.
- Funciona con Shopify Managed Markets (probado 2026-11-25, Pull House US → Reino Unido). Lo que NO funciona con Managed
  Markets es el tipo de cambio manual (baseCurrencyManualRate: ADAPTIVE_PRICING_REQUIRES_LOCAL_CURRENCIES).
- Ojo: un código de monto fijo ($25) se convierte con la cotización (da ~£19): crear un código propio del mercado
  (context: {markets: {add: [mercado]}}) con el monto en USD ajustado a la cotización para que dé el número exacto.
"""
import argparse
import json
import os
import subprocess
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("tienda"); ap.add_argument("--mercado", required=True); ap.add_argument("--moneda", required=True)
ap.add_argument("--lista")
a = ap.parse_args()


def gql(q, v=None, mut=False):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(v or {}, tf)
    cmd = ["shopify", "store", "execute", "-s", a.tienda, "-j", "--variable-file", tf.name, "-q", q]
    if mut:
        cmd.append("--allow-mutations")
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    os.unlink(tf.name)
    d = json.loads(r.stdout[r.stdout.index("{"):]); return d.get("data", d)


lista = a.lista
if not lista:
    c = gql('mutation($m:ID!){catalogCreate(input:{title:"Precios fijos mercado", status:ACTIVE, context:{marketIds:[$m]}}){catalog{id} userErrors{message}}}',
            {"m": a.mercado}, True)["catalogCreate"]
    print("catálogo", c); cat = c["catalog"]["id"]
    pl = gql('mutation($c:ID!,$cur:CurrencyCode!){priceListCreate(input:{name:"Mismo número que la moneda de la tienda", currency:$cur, parent:{adjustment:{type:PERCENTAGE_DECREASE, value:0}}, catalogId:$c}){priceList{id} userErrors{message}}}',
             {"c": cat, "cur": a.moneda}, True)["priceListCreate"]
    print("lista", pl); lista = pl["priceList"]["id"]

tmp = tempfile.mkdtemp(); qf = os.path.join(tmp, "q.graphql"); out = os.path.join(tmp, "v.jsonl")
open(qf, "w").write("{ productVariants { edges { node { id price compareAtPrice } } } }")
subprocess.run(["shopify", "store", "bulk", "execute", "-s", a.tienda, "--query-file", qf, "--watch", "--output-file", out],
               capture_output=True, text=True, stdin=subprocess.DEVNULL)
prices = []
for line in open(out):
    v = json.loads(line)
    e = {"variantId": v["id"], "price": {"amount": v["price"], "currencyCode": a.moneda}}
    if v.get("compareAtPrice") and float(v["compareAtPrice"]) > float(v["price"]):
        e["compareAtPrice"] = {"amount": v["compareAtPrice"], "currencyCode": a.moneda}
    prices.append(e)
ok, errs = 0, []
for i in range(0, len(prices), 250):
    d = gql('mutation($id:ID!,$p:[PriceListPriceInput!]!){priceListFixedPricesAdd(priceListId:$id, prices:$p){prices{variant{id}} userErrors{message}}}',
            {"id": lista, "p": prices[i:i + 250]}, True)["priceListFixedPricesAdd"]
    ok += len(d["prices"] or []); errs += d["userErrors"]
print(f"lista {lista}: {ok} de {len(prices)} variantes con precio fijo en {a.moneda}. Errores: {errs[:3]}")
