"""Sube archivos del tema con themeFilesUpsert. Uso: python3 -I upsert.py <tienda> <theme_id_num> <carpeta_tema> <archivo> [...]"""
import json, subprocess, sys, tempfile, os
store, tid, base, *rels = sys.argv[1:]
files = [{"filename": r, "body": {"type": "TEXT", "value": open(os.path.join(base, r)).read()}} for r in rels]
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
    json.dump({"id": f"gid://shopify/OnlineStoreTheme/{tid}", "f": files}, tf)
r = subprocess.run(["shopify", "store", "execute", "-s", store, "--allow-mutations", "-j", "--variable-file", tf.name, "-q",
                    "mutation($id:ID!,$f:[OnlineStoreThemeFilesUpsertFileInput!]!){themeFilesUpsert(themeId:$id,files:$f){upsertedThemeFiles{filename} userErrors{filename code message}}}"],
                   capture_output=True, text=True, stdin=subprocess.DEVNULL)
os.unlink(tf.name)
print(r.stdout[r.stdout.find("{"):] if "{" in r.stdout else r.stdout + r.stderr)
