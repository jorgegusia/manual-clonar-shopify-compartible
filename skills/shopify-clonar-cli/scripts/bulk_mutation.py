"""Corre un `shopify store bulk execute` con mutaciones SIN riesgo de duplicar si la red corta (ETIMEDOUT).
Uso: python3 -I bulk_mutation.py <tienda> <variables.jsonl> <resultado.jsonl> '<mutation>'
Si el CLI falla, mira currentBulkOperation(type:MUTATION): si hay una operación creada después de arrancar,
la espera y baja su resultado (no reintenta). Solo reintenta si Shopify no llegó a recibirla.
"""
import datetime
import json
import subprocess
import sys
import time
import urllib.request

store, variables, output, mutation = sys.argv[1:5]


def current():
    for _ in range(10):
        r = subprocess.run(["shopify", "store", "execute", "-s", store, "-j", "-q",
                            "query{ currentBulkOperation(type:MUTATION){ id status createdAt objectCount errorCode url } }"],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if "{" in r.stdout:
            d = json.loads(r.stdout[r.stdout.index("{"):])
            return d.get("data", d)["currentBulkOperation"]
        time.sleep(15)
    raise RuntimeError("no se pudo consultar currentBulkOperation")


for attempt in range(1, 6):
    start = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
    r = subprocess.run(["shopify", "store", "bulk", "execute", "-s", store, "--allow-mutations", "--variable-file", variables,
                        "--watch", "--output-file", output, "-q", mutation],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode == 0:
        print("OK al primer intento" if attempt == 1 else f"OK en el intento {attempt}")
        sys.exit(0)
    op = current()
    created = op and datetime.datetime.fromisoformat(op["createdAt"].replace("Z", "+00:00"))
    if not op or created < start:
        print(f"intento {attempt}: Shopify no recibió la operación, reintento")
        time.sleep(20)
        continue
    print(f"intento {attempt}: el CLI cortó pero la operación corre en Shopify ({op['status']}), espero sin reintentar")
    while op["status"] in ("CREATED", "RUNNING"):
        time.sleep(20)
        op = current()
    print("terminó:", op["status"], op["objectCount"], op.get("errorCode") or "")
    if op.get("url"):
        urllib.request.urlretrieve(op["url"], output)
        print("resultado guardado en", output)
    sys.exit(0 if op["status"] == "COMPLETED" else 1)
sys.exit("no se pudo lanzar la operación después de 5 intentos")
