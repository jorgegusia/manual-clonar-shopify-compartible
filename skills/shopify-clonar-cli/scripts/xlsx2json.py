"""Lee un .xlsx (por ejemplo el Import_Result de Matrixify) sin dependencias y resume cada hoja.
Uso: python3 -I xlsx2json.py <archivo.xlsx> <salida.json>
Después agrupar por las columnas "Import Result" / "Import Comment" de cada hoja.
"""
import collections
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

z = zipfile.ZipFile(sys.argv[1])
shared = []
if "xl/sharedStrings.xml" in z.namelist():
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
        shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}


def col_idx(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


out = {}
for sh in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", NS):
    target = rels[sh.get(REL)].lstrip("/")
    path = target if target.startswith("xl/") else "xl/" + target
    rows = []
    for row in ET.fromstring(z.read(path)).iter("{%s}row" % NS["m"]):
        vals = {}
        for c in row.findall("m:c", NS):
            t, v = c.get("t"), c.find("m:v", NS)
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            else:
                val = v.text if v is not None else None
            vals[col_idx(c.get("r"))] = val
        if vals:
            rows.append([vals.get(i) for i in range(max(vals) + 1)])
    out[sh.get("name")] = rows
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)

# Resumen: tienda de la que salió el archivo y resultados por hoja
for name, rows in out.items():
    if not rows:
        continue
    hdr = {h: i for i, h in enumerate(rows[0]) if h}
    get = lambda r, k: r[hdr[k]] if k in hdr and len(r) > hdr[k] else None
    print(f"### {name}: {len(rows) - 1} filas")
    if "Shopify Domain" in hdr:
        print("   tienda:", {get(r, "Shopify Domain") for r in rows[1:]})
    if "Import Result" in hdr:
        print("   resultado:", dict(collections.Counter(get(r, "Import Result") for r in rows[1:])))
        for k, n in collections.Counter((get(r, "Import Comment") or "")[:180] for r in rows[1:]).most_common(5):
            print(f"     {n} x {k!r}")
