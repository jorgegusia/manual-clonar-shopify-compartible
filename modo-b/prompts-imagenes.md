# Prompts de imágenes (Higgsfield)

Reemplazar `{...}` con los datos de `marca.json`. Textos de las imágenes en **inglés**.
Modelo recomendado para imágenes con texto: el de GPT Image de Higgsfield (`gpt_image_2_5` o el más nuevo que liste).

## Reglas
- **Tandas de máximo 6 imágenes.** Con 9 o más da error 429 (límite). Esperar que termine la tanda (herramienta de
  estado/espera) y recién ahí pedir la siguiente.
- **Revisar el texto de cada imagen** (abrir la URL y hacer zoom): título exacto, sin letras inventadas.
  Si sale mal escrito, regenerar SOLO esa.
- Las URLs que devuelve Higgsfield (cloudfront) se pasan **directo** a Shopify (`files[].originalSource` del producto
  o `fileCreate`). No hace falta descargarlas.
- Cada generación gasta créditos de Higgsfield: avisar al usuario cuántas se van a pedir (normal: 6 portadas + 1 hero + 2 logos = 9).

## 1. Portadas (6, cuadradas 1:1)
```
Premium product mockup of a single hardcover book standing upright, slightly angled to the left,
centered on a seamless plain background in {paper} with a soft natural shadow. Square 1:1, minimal editorial style.
Book cover: the top third is a light {paper} band with the title "{TITULO}" in an elegant dark serif font
(color {ink}) and below it the small uppercase line "DIGITAL EDITION". The lower two thirds show a flat,
graphic illustration of {OBJETOS_DEL_TEMA} in monochrome tones of {accent} and muted brown, paper-cut style.
Thick book spine in {accent}. No other text, no logos, no people.
```
- `{OBJETOS_DEL_TEMA}`: 3–5 objetos concretos del tema de ESE ebook (ej. "a phone on a tripod, a ring light, film frames").
- **Producto top (el de 199):** cambiar el comienzo por
  `Premium mockup of a set of three hardcover books standing side by side, the front one showing...`
  y usar el título de la colección.

## 2. Hero (1, horizontal 3:2, SIN texto)
```
Top-down flat lay of {OBJETOS_DEL_NICHO} arranged artfully on a {paper} surface, monochrome palette of {accent},
deep brown and {paper}, paper-cut craft aesthetic, soft diffused natural light, high detail, editorial
photography, landscape 3:2. No text, no letters, no logos, no people's faces.
```
Se muestra recortada en arco: dejar los objetos importantes en el centro.

## 3. Logo (2 opciones, horizontal ~3:1; si el modelo no tiene 3:1 usar 21:9)
```
Minimal brand logo on a plain white background: a simple thin-line icon of {ICONO} in {ink} on the left,
and the wordmark "{NOMBRE_TIENDA}" in an elegant serif font in {ink}, with the small uppercase subtitle
"{SUBTITULO}" in a light sans-serif underneath. Flat vector style, generous spacing, no other elements.
```
- `{ICONO}`: algo simple del nicho (una hoja, un libro abierto, un lápiz, un megáfono...).
- `{SUBTITULO}`: 1–2 palabras ("DIGITAL GUIDES", "PAPER STUDIO", "MARKETING LIBRARY").
- Elegir la opción con el texto **bien escrito**. Después **quitar el fondo** (herramienta de remover fondo de
  Higgsfield, si está disponible) para tener PNG transparente: el footer lo muestra en claro invirtiendo colores.
  Si no se puede quitar el fondo: en el footer desactivar "Show logo in light color" o generar una versión clara.

## 4. Subir a Shopify
- Portadas: van dentro de cada producto (`armar_productos.py --portadas portadas.json`).
- Hero y logo: `fileCreate` con la URL (`contentType: IMAGE`, `filename: <slug>-hero.png` / `<slug>-logo.png`).
  Esperar `fileStatus: READY`; en el tema se usan como `shopify://shop_images/<filename>`.
- Si el logo trae mucho margen, recortar con la URL del CDN: `...?width=1000&height=230&crop=center`, subir esa versión.
