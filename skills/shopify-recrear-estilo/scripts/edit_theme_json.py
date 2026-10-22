"""Edita un JSON del tema (settings_data.json, *-group.json, templates/*.json) preservando el comentario
/* ... */ que Shopify pone arriba. json.load directo falla por ese comentario.
Uso: python3 -I edit_theme_json.py <archivo.json> '<ruta.con.puntos>' '<valor JSON>'
Ejemplos:
  python3 -I edit_theme_json.py config/settings_data.json current.favicon '"shopify://shop_images/favicon.png"'
  python3 -I edit_theme_json.py sections/header-group.json sections.<id_header>.settings.logo '"shopify://shop_images/logo.png"'
  python3 -I edit_theme_json.py sections/footer-group.json sections.<id_footer>.blocks.<id_bloque>.settings.heading '"Help"'
Después: shopify theme push --theme ID --only <archivo> --allow-live (si el tema está publicado).
Ojo: textos como el copyright pueden estar en un BLOQUE y no en la sección; buscar el texto con grep primero.
"""
import json
import re
import sys

path, keypath, value = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
raw = open(path).read()
# Puede haber más de un comentario /* */ arriba (el de Shopify y uno propio): se conservan todos.
m = re.match(r"\s*((?:/\*.*?\*/\s*)+)", raw, re.S)
head = m.group(1).rstrip() + "\n" if m else ""
data = json.loads(raw[m.end():] if m else raw)
node = data
keys = keypath.split(".")
for k in keys[:-1]:
    node = node.setdefault(k, {})
print("antes:", json.dumps(node.get(keys[-1]), ensure_ascii=False)[:200])
node[keys[-1]] = value
open(path, "w").write(head + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("después:", json.dumps(value, ensure_ascii=False)[:200])
