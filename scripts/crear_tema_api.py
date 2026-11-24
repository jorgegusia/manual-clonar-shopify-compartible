"""Crea un tema SIN publicar en el destino desde una carpeta local, por API (sin `shopify theme push`).
Uso: python3 -I crear_tema_api.py TIENDA CARPETA_TEMA "NOMBRE"
zip -> stagedUploadsCreate -> POST -> themeCreate(source: resourceUrl) -> espera PROCESSED."""
import json, os, subprocess, sys, tempfile, time, zipfile
store, folder, name = sys.argv[1], sys.argv[2], sys.argv[3]
def gql(q, v):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf: json.dump(v, tf)
    r = subprocess.run(["shopify","store","execute","-s",store,"--allow-mutations","-j","--variable-file",tf.name,"-q",q],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    os.unlink(tf.name)
    d = json.loads(r.stdout[r.stdout.index("{"):]); return d.get("data", d)
zp = os.path.join(tempfile.mkdtemp(), "tema.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, fs in os.walk(folder):
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, folder)
            if rel.split(os.sep)[0] in ("assets","blocks","config","layout","locales","sections","snippets","templates"):
                z.write(p, rel)
st = gql("mutation($i:[StagedUploadInput!]!){stagedUploadsCreate(input:$i){stagedTargets{url resourceUrl parameters{name value}} userErrors{message}}}",
         {"i":[{"filename":"tema.zip","mimeType":"application/zip","resource":"FILE","httpMethod":"POST","fileSize":str(os.path.getsize(zp))}]})["stagedUploadsCreate"]
print(st["userErrors"]); t = st["stagedTargets"][0]
cmd = ["curl","-s","-o","/dev/null","-w","%{http_code}"]
for p in t["parameters"]: cmd += ["-F", f"{p['name']}={p['value']}"]
cmd += ["-F", f"file=@{zp}", t["url"]]
print("upload", subprocess.run(cmd, capture_output=True, text=True).stdout)
src = t["resourceUrl"]
r = gql("mutation($s:URL!,$n:String){themeCreate(source:$s,name:$n,role:UNPUBLISHED){theme{id name processing} userErrors{field message code}}}",
        {"s": src, "n": name})["themeCreate"]
print(r)
tid = r["theme"]["id"]
for _ in range(60):
    time.sleep(5)
    th = gql("query($id:ID!){theme(id:$id){processing processingFailed role}}", {"id": tid})["theme"]
    if not th["processing"]: print("listo", tid, th); break
