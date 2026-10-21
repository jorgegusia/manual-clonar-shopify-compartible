"""Sube videos (o cualquier archivo local) a Files del DESTINO: stagedUploadsCreate -> POST del archivo -> fileCreate.
Uso: python3 -I upload_videos.py <tienda-destino.myshopify.com> <carpeta> <hecho.json> [IMAGE]
- Por defecto sube los .mp4 como VIDEO. Con IMAGE al final sube los .png/.jpg/.webp como imagen
  (sirve para logos/favicon generados localmente).
- Reanudable y con reintentos (la red suele cortar con ETIMEDOUT).
- Después verificar en destino: cantidad, que no haya duplicados y fileStatus READY antes de re-subir templates/index.json.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

store, folder, done_path = sys.argv[1], sys.argv[2], sys.argv[3]
kind = sys.argv[4] if len(sys.argv) > 4 else "VIDEO"
exts = (".mp4", ".mov") if kind == "VIDEO" else (".png", ".jpg", ".jpeg", ".webp", ".gif")
mimes = {".mp4": "video/mp4", ".mov": "video/quicktime", ".png": "image/png", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
done = json.load(open(done_path)) if os.path.exists(done_path) else {}


def gql(query, variables):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(variables, tf)
    try:
        for attempt in range(4):
            res = subprocess.run(["shopify", "store", "execute", "-s", store, "--allow-mutations", "-j",
                                  "--variable-file", tf.name, "-q", query],
                                 capture_output=True, text=True, stdin=subprocess.DEVNULL)
            if "{" in res.stdout:
                d = json.loads(res.stdout[res.stdout.index("{"):])
                return d.get("data", d)
            print("reintento", attempt + 1, (res.stdout + res.stderr)[-300:])
            time.sleep(5)
    finally:
        os.unlink(tf.name)
    raise RuntimeError("store execute falló 4 veces")


STAGE = ("mutation($input:[StagedUploadInput!]!){ stagedUploadsCreate(input:$input){ "
         "stagedTargets{ url resourceUrl parameters{ name value } } userErrors{ field message } } }")
CREATE = ("mutation($files:[FileCreateInput!]!){ fileCreate(files:$files){ files{ id fileStatus } "
          "userErrors{ field message code } } }")

todo = sorted(f for f in os.listdir(folder) if f.lower().endswith(exts) and f not in done)
print("pendientes:", len(todo))
for start in range(0, len(todo), 10):
    batch = todo[start:start + 10]
    st = gql(STAGE, {"input": [{"filename": f, "mimeType": mimes[os.path.splitext(f)[1].lower()], "resource": kind,
                                "httpMethod": "POST", "fileSize": str(os.path.getsize(os.path.join(folder, f)))}
                               for f in batch]})["stagedUploadsCreate"]
    if st["userErrors"]:
        print("stage errors", st["userErrors"])
        continue
    files = []
    for f, t in zip(batch, st["stagedTargets"]):
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}"]
        for p in t["parameters"]:
            cmd += ["-F", f"{p['name']}={p['value']}"]
        cmd += ["-F", f"file=@{os.path.join(folder, f)}", t["url"]]
        code = subprocess.run(cmd, capture_output=True, text=True).stdout
        if code not in ("200", "201", "204"):
            print("upload falló", f, code)
            continue
        files.append((f, {"originalSource": t["resourceUrl"], "contentType": kind, "filename": f}))
    if not files:
        continue
    cr = gql(CREATE, {"files": [x for _, x in files]})["fileCreate"]
    if cr["userErrors"]:
        print("create errors", cr["userErrors"])
    for (f, _), created in zip(files, cr["files"] or []):
        done[f] = created["id"]
    json.dump(done, open(done_path, "w"))
    print(f"tanda {start // 10 + 1}: {len(cr['files'] or [])} archivos (total {len(done)})")
print("TOTAL:", len(done))
