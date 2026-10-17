"""Modo B (ebooks): valida los productos de marca.json y arma el JSONL para bulk productSet.
Uso: python3 -I armar_productos.py <marca.json> <salida.jsonl> [--portadas portadas.json]
- portadas.json (opcional): {handle: "https://...url-de-la-portada"} (URLs de Higgsfield o de cdn.shopify).
  Si no se pasa, usa el campo "portada" de cada producto en marca.json (si lo tiene).
Reglas que controla (frena si alguna falla):
- 6 productos, precios entre 19 y 199, todos distintos.
- Exactamente uno con "top": true y es el MÁS CARO (lleva tags bestseller y top).
- Descripción con "What's inside", "Format", disclaimer educativo y "Digital product only".
- Sin frases prohibidas (promesas vagas o inventadas).
Cada producto: ACTIVE, vendor = tienda, sin envío (requiresShipping false), sin control de stock,
metacampo custom.resumen (la línea corta de la tarjeta de la home).
Después:
shopify store bulk execute -s TIENDA --allow-mutations --variable-file salida.jsonl --watch --output-file productset-result.jsonl \
  -q 'mutation($input: ProductSetInput!){ productSet(input:$input){ product{ id handle } userErrors{ field message code } } }'
"""
import json
import re
import sys

PROHIBIDAS = ["may cover", "proposed", "planned title", "guaranteed results", "pages of", "doctor-approved",
              "get rich quick", "lose weight fast"]

args = sys.argv[1:]
marca_path, out = args[0], args[1]
portadas = {}
if "--portadas" in args:
    portadas = json.load(open(args[args.index("--portadas") + 1]))
m = json.load(open(marca_path))
tienda = m["tienda"]["nombre"]
prefix = re.sub(r"[^A-Z]", "", m["tienda"].get("slug", tienda).upper())[:3] or "EB"
prods = m["productos"]

errores = []
if len(prods) != 6:
    errores.append(f"hay {len(prods)} productos, tienen que ser 6")
precios = [float(p["precio"]) for p in prods]
if any(x < 19 or x > 199 for x in precios):
    errores.append(f"precios fuera de 19–199: {precios}")
if len(set(precios)) != len(precios):
    errores.append(f"precios repetidos: {precios}")
tops = [p for p in prods if p.get("top")]
if len(tops) != 1:
    errores.append(f"tiene que haber exactamente 1 producto top (hay {len(tops)})")
elif float(tops[0]["precio"]) != max(precios):
    errores.append("el producto top tiene que ser el más caro")
for p in prods:
    d = p["descripcion_html"]
    low = re.sub(r"<[^>]+>", " ", d).lower()
    for req in ("what's inside", "format", "not a substitute for professional", "digital product only"):
        if req not in low:
            errores.append(f"{p['handle']}: falta '{req}' en la descripción")
    for bad in PROHIBIDAS:
        if bad in low or bad in p["titulo"].lower():
            errores.append(f"{p['handle']}: frase prohibida '{bad}'")
    if not (portadas.get(p["handle"]) or p.get("portada")):
        errores.append(f"{p['handle']}: falta la portada")
if errores:
    sys.exit("NO se generó el archivo:\n- " + "\n- ".join(errores))

with open(out, "w") as fh:
    for i, p in enumerate(sorted(prods, key=lambda x: float(x["precio"])), 1):
        top = bool(p.get("top"))
        tags = ["ebook", "digital-product"] + (["bestseller", "top"] if top else []) + p.get("tags", [])
        inp = {
            "title": p["titulo"],
            "handle": p["handle"],
            "descriptionHtml": p["descripcion_html"],
            "vendor": tienda,
            "productType": "Digital Ebook Collection" if top else "Digital Ebook",
            "tags": tags,
            "status": "ACTIVE",
            "productOptions": [{"name": "Title", "values": [{"name": "Default Title"}]}],
            "variants": [{
                "optionValues": [{"optionName": "Title", "name": "Default Title"}],
                "price": p["precio"],
                "sku": f"{prefix}-{i:02d}",
                "taxable": True,
                "inventoryPolicy": "CONTINUE",
                "inventoryItem": {"requiresShipping": False, "tracked": False},
            }],
            "files": [{"originalSource": portadas.get(p["handle"]) or p["portada"], "contentType": "IMAGE",
                       "alt": p["titulo"]}],
            "metafields": [{"namespace": "custom", "key": "resumen", "type": "single_line_text_field",
                            "value": p["resumen"]}],
        }
        fh.write(json.dumps({"input": inp}, ensure_ascii=False) + "\n")
        print(f"{prefix}-{i:02d}  {p['precio']:>7}  {'TOP ' if top else '    '}{p['titulo']}")
print(f"OK: {out}")
