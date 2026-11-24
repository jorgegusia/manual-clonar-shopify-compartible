"""Baja un tema completo por API (cuando `shopify theme pull` se cuelga).
Uso: python3 -I bajar_tema_api.py TIENDA THEME_ID CARPETA"""
import base64, json, os, subprocess, sys, urllib.request
store, tid, out = sys.argv[1], sys.argv[2], sys.argv[3]
Q = '''query($id:ID!,$after:String){ theme(id:$id){ files(first:50, after:$after){ pageInfo{hasNextPage endCursor}
 nodes{ filename body{ __typename ... on OnlineStoreThemeFileBodyText{content} ... on OnlineStoreThemeFileBodyBase64{contentBase64}
 ... on OnlineStoreThemeFileBodyUrl{url} } } } } }'''
after, n = None, 0
while True:
    v = {"id": f"gid://shopify/OnlineStoreTheme/{tid}", "after": after}
    r = subprocess.run(["shopify", "store", "execute", "-s", store, "-j", "-q", Q, "--variables", json.dumps(v)],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    txt = r.stdout[r.stdout.find("{"):]
    d = json.loads(txt)
    d = d.get("data", d)
    f = d["theme"]["files"]
    for node in f["nodes"]:
        p = os.path.join(out, node["filename"]); os.makedirs(os.path.dirname(p), exist_ok=True)
        b = node["body"]
        if b["__typename"].endswith("Text"):
            open(p, "w").write(b["content"])
        elif b["__typename"].endswith("Base64"):
            open(p, "wb").write(base64.b64decode(b["contentBase64"]))
        else:
            open(p, "wb").write(urllib.request.urlopen(b["url"]).read())
        n += 1
    print(n, flush=True)
    if not f["pageInfo"]["hasNextPage"]:
        break
    after = f["pageInfo"]["endCursor"]
print("TOTAL", n)
