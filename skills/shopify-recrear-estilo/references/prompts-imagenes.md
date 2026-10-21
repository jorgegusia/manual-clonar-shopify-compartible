# Prompts de imágenes

Los prompts **reales** están en `scripts/generar_imagenes.py` (constantes `PORTADA`, `PORTADA_TOP`, `HERO`, `LOGO`)
y se completan solos con `marca.json`. Este archivo explica qué pide cada uno y cómo revisarlos. Si se cambia un
prompt, cambiarlo en el script (y acá si cambia la idea).

Herramienta por defecto: **Nano Banana Pro** (`gemini-3-pro-image`, API de Gemini), 2K. Alternativa: Higgsfield
(mismos textos, tandas de máximo 6). Textos dentro de las imágenes en **inglés**.

## Qué se genera (9 por tienda)
| Archivo | Formato | Qué es |
|---|---|---|
| `portada-<handle>.png` ×5 | 1:1 | Un libro de tapa dura parado, levemente girado, sobre fondo liso color *paper* con sombra suave. Franja superior clara con el **título exacto** en serif + "DIGITAL EDITION"; abajo, ilustración plana tipo papel recortado de `objetos` del ebook en tonos del *accent*. Lomo color *accent* |
| `portada-<handle-top>.png` | 1:1 | Igual, pero **set de 3 libros** y "COMPLETE COLLECTION" |
| `<slug>-hero.png` | 3:2 | Flat-lay (desde arriba) de `home.objetos_hero`, monocromo *accent*/marrón/*paper*, luz suave, **sin texto**. Se ve recortada en arco: lo importante al centro |
| `<slug>-logo-1.png` y `-2` | 21:9 | Ícono de línea fina (`tienda.icono`) + nombre en serif + `tienda.subtitulo` en mayúsculas chicas, color *ink*, **fondo blanco puro** |

## Cómo elegir los datos
- `objetos`: 3–5 cosas **concretas y dibujables** del tema de ese ebook ("a phone on a small tripod, a ring light,
  film frames"). Nada abstracto ("growth", "success").
- `icono`: un objeto simple del nicho (una hoja, un libro abierto, un megáfono, una taza).
- `subtitulo`: 1–3 palabras ("DIGITAL GUIDES", "PAPER STUDIO", "MARKETING LIBRARY").

## Revisión (obligatoria antes de subir)
- Abrir cada imagen y hacer zoom al texto: título **letra por letra**, sin palabras de más.
- Que la portada se vea como las de la referencia (libro solo, fondo que se funde con la página).
- Logo: elegir el mejor de los 2 y renombrarlo `<slug>-logo.png`. Debe ser legible a 150 px de ancho.
- Si una falla: `generar_imagenes.py ... --solo <archivo> --rehacer` (cada repetición cuesta otra imagen).

## Por qué el logo va sobre blanco
El tema lo mezcla con CSS: en el header `mix-blend-mode: multiply` hace desaparecer el blanco sobre el fondo papel,
y en el footer `invert` + `mix-blend-mode: screen` lo muestra en claro sobre el bordó. Así no hace falta PNG transparente.
