"""Sube imágenes al DESTINO con fileCreate (originalSource = URL del CDN del origen), en tandas de 50.
Uso: python3 -I upload_images.py <tienda-destino.myshopify.com> <archivos-a-subir.json> <mapa-archivos.json>
Guarda {id_origen: id_destino} en el mapa (necesario para build_productset.py --map). Es reanudable.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

store, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
items = json.load(open(src))
mapping = json.load(open(out)) if os.path.exists(out) else {}
todo = [i for i in items if i["id"] not in mapping]
print("pendientes:", len(todo), "| ya subidas:", len(mapping))

MUT = ("mutation($files:[FileCreateInput!]!){ fileCreate(files:$files){ files{ id } "
       "userErrors{ field message code } } }")


def run(variables):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(variables, tf)
    try:
        for attempt in range(4):
            res = subprocess.run(["shopify", "store", "execute", "-s", store, "--allow-mutations", "-j",
                                  "--variable-file", tf.name, "-q", MUT],
                                 capture_output=True, text=True, stdin=subprocess.DEVNULL)
            if "{" in res.stdout:
                d = json.loads(res.stdout[res.stdout.index("{"):])
                return d.get("data", d)["fileCreate"]
            print("reintento", attempt + 1, (res.stdout + res.stderr)[-300:])
            time.sleep(5)
    finally:
        os.unlink(tf.name)
    raise RuntimeError("store execute falló 4 veces")


for start in range(0, len(todo), 50):
    batch = todo[start:start + 50]
    data = run({"files": [{"originalSource": i["url"], "filename": i["filename"], "alt": i["alt"],
                           "contentType": "IMAGE", "duplicateResolutionMode": "RAISE_ERROR"} for i in batch]})
    if data["userErrors"]:
        print("userErrors tanda", start // 50 + 1, data["userErrors"][:5])
        continue  # no mapear una tanda con errores: los índices podrían no coincidir
    for i, f in zip(batch, data["files"] or []):
        mapping[i["id"]] = f["id"]
    json.dump(mapping, open(out, "w"))
    print(f"tanda {start // 50 + 1}: {len(data['files'] or [])} creadas (total {len(mapping)})")
print("TOTAL mapeadas:", len(mapping), "de", len(items))
