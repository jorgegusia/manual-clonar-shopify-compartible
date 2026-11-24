"""Sube archivos sueltos de un tema local a un tema del destino con themeFilesUpsert.
Uso: python3 -I subir_archivos_tema.py TIENDA THEME_ID CARPETA archivo1 [archivo2 ...]"""
import json, os, subprocess, sys, tempfile
store, tid, folder, files = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
inp = [{"filename": f, "body": {"type": "TEXT", "value": open(os.path.join(folder, f)).read()}} for f in files]
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
    json.dump({"id": f"gid://shopify/OnlineStoreTheme/{tid}", "files": inp}, tf)
q = "mutation($id:ID!,$files:[OnlineStoreThemeFilesUpsertFileInput!]!){themeFilesUpsert(themeId:$id,files:$files){upsertedThemeFiles{filename} userErrors{filename code message}}}"
r = subprocess.run(["shopify","store","execute","-s",store,"--allow-mutations","-j","--variable-file",tf.name,"-q",q],
                   capture_output=True, text=True, stdin=subprocess.DEVNULL)
os.unlink(tf.name); print(r.stdout[r.stdout.find("{"):] or r.stderr[-800:])
