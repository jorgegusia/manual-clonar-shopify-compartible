"""Modo B (ebooks): completa las 5 políticas en inglés con los datos de la LLC de marca.json.
Uso: python3 -I generar_politicas.py <marca.json> <carpeta-salida> [carpeta-plantillas] [--fecha "October 17, 2026"]
Genera en la carpeta de salida:
- <handle>.html            una por política (privacy, refund, shipping, terms, contact-information)
- <TIPO>.vars.json         variables para shopPolicyUpdate (una por política)
- politicas-para-copiar.html  todas juntas con un botón "Copy" (para pegarlas a mano si hace falta)
Cargar cada una:
shopify store execute -s TIENDA --allow-mutations --variable-file <TIPO>.vars.json \
  -q 'mutation($shopPolicy: ShopPolicyInput!){ shopPolicyUpdate(shopPolicy:$shopPolicy){ shopPolicy{ type url } userErrors{ field message } } }'
"""
import datetime
import html
import json
import os
import re
import sys

POLITICAS = [
    ("privacy-policy", "PRIVACY_POLICY", "Privacy Policy"),
    ("refund-policy", "REFUND_POLICY", "Refund Policy"),
    ("shipping-policy", "SHIPPING_POLICY", "Shipping Policy"),
    ("terms-of-service", "TERMS_OF_SERVICE", "Terms of Service"),
    ("contact-information", "CONTACT_INFORMATION", "Contact Information"),
]

args = sys.argv[1:]
fecha = None
if "--fecha" in args:
    i = args.index("--fecha")
    fecha = args[i + 1]
    del args[i:i + 2]
marca_path, salida = args[0], args[1]
here = os.path.dirname(os.path.abspath(__file__))
plant = args[2] if len(args) > 2 else next((d for d in (os.path.join(here, "..", "modo-b", "plantillas", "politicas"), os.path.join(here, "..", "plantillas", "politicas")) if os.path.isdir(d)), "")
m = json.load(open(marca_path))
t, llc = m["tienda"], m["llc"]

faltan = [k for k in ("nombre", "estado", "direccion", "email") if not llc.get(k)]
if faltan:
    sys.exit("Faltan datos de la LLC en marca.json: " + ", ".join(faltan))
if not fecha:
    fecha = datetime.date.today().strftime("%B %d, %Y").replace(" 0", " ")
valores = {
    "STORE": t["nombre"],
    "WEBSITE": t.get("web") or t.get("myshopify", ""),
    "LLC": llc["nombre"],
    "STATE": llc["estado"],
    "ADDRESS": llc["direccion"],
    "EMAIL": llc["email"],
    "PHONE": llc.get("telefono") or "xxx xx xxx",
    "HOURS": llc.get("horario") or "Monday to Friday, 9:00 am to 5:00 pm (ET)",
    "DATE": fecha,
}

os.makedirs(salida, exist_ok=True)
bloques = []
for handle, tipo, titulo in POLITICAS:
    body = open(os.path.join(plant, handle + ".html")).read()
    for k, v in valores.items():
        body = body.replace("{{" + k + "}}", html.escape(v, quote=False))
    resto = re.findall(r"\{\{[A-Z_]+\}\}", body)
    if resto:
        sys.exit(f"{handle}: quedaron marcadores sin completar {sorted(set(resto))}")
    open(os.path.join(salida, handle + ".html"), "w").write(body)
    json.dump({"shopPolicy": {"type": tipo, "body": body}},
              open(os.path.join(salida, tipo + ".vars.json"), "w"), ensure_ascii=False)
    bloques.append(f'<section><div class="bar"><h1>{titulo}</h1><button onclick="copy(\'{handle}\', this)">Copy</button></div>'
                   f'<div id="{handle}" class="doc">{body}</div></section>')
    print(f"OK {handle}")

pagina = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Policies – %s</title><style>
body{font:16px/1.6 -apple-system,Segoe UI,Arial,sans-serif;max-width:860px;margin:30px auto;padding:0 16px;color:#171717;background:#faf8f7}
section{background:#fff;border:1px solid #e5e0de;border-radius:10px;padding:20px 24px;margin-bottom:24px}
.bar{display:flex;justify-content:space-between;align-items:center;gap:16px}.bar h1{font-size:22px;margin:0}
button{background:#171717;color:#fff;border:0;border-radius:6px;padding:9px 16px;cursor:pointer;font-weight:700}
.doc{margin-top:12px;border-top:1px solid #eee;padding-top:8px}</style></head><body>
<p>Settings → Policies: copy each policy and paste it in its box (the copy keeps the formatting).</p>
%s
<script>function copy(id,b){const el=document.getElementById(id);const h=new Blob([el.innerHTML],{type:'text/html'});
const t=new Blob([el.innerText],{type:'text/plain'});navigator.clipboard.write([new ClipboardItem({'text/html':h,'text/plain':t})])
.then(()=>{b.textContent='Copied ✓';setTimeout(()=>b.textContent='Copy',1500)}).catch(()=>{const r=document.createRange();
r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');b.textContent='Copied ✓'})}</script>
</body></html>""" % (html.escape(t["nombre"]), "\n".join(bloques))
open(os.path.join(salida, "politicas-para-copiar.html"), "w").write(pagina)
if not llc.get("telefono"):
    print("AVISO: no hay teléfono; las políticas dicen 'xxx xx xxx'. Pedírselo al usuario.")
print(f"Listo: {salida}/politicas-para-copiar.html")
