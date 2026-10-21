# Estilo de referencia por defecto: "Paper Studio" (editorial, papel y bordó)

Tienda analizada: `https://e2c3yd-zk.myshopify.com/` (sin acceso, solo lo público, oct 2026).
Es el estilo que se usa **siempre que el usuario no pase otra referencia**. Se copia el **diseño**
(estructura, proporciones, paleta, tipografías, tipo de imágenes); los **textos, imágenes, nombre y LLC son propios**.

## Qué es por dentro
- Tema base **Horizon 4.3.0** (gratis de Shopify). El tema se llama "... - AI draft": lo armó la IA de Shopify.
- Todo el diseño está en secciones propias: `ebook_header`, `ebook_hero` (home entera), `ebook_product`,
  `ebook_cart`, `ebook_shared_footer`. Colección y contacto usan las secciones normales de Horizon con estilos encima.
- Nuestra versión: `plantillas/tema/sections/eb-header|eb-home|eb-product|eb-footer.liquid`.

## Paleta y tipografías
| Token | Color | Uso |
|---|---|---|
| paper | `#F4EDEC` | fondo de toda la tienda (rosado muy claro, "papel") |
| ink | `#171717` | texto |
| accent | `#60241A` | bordó: botones, barra de anuncios, banda de cierre, footer |
| muted | `#686868` | texto secundario |

- Títulos: **Georgia** (serif), grandes y apretados (`letter-spacing` negativo).
- Etiquetas chicas ("kicker"): sans en mayúsculas, 12 px, espaciado .13em.
- Texto de tarjetas y botones: Arial/sans.
- Botones cuadrados en la home (sin redondeo) con flecha ↗; en la ficha de producto, botón ancho redondeado.
- Si el rubro pide otra paleta, cambiar solo los 4 tokens (misma lógica: fondo claro cálido + 1 acento oscuro).

## Estructura de la home (en orden)
1. **Header** blanco-papel: logo a la izquierda (ícono de línea + wordmark serif + subtítulo en versalitas),
   menú Home / Our Ebooks / Contact en negrita, selector de país/moneda en píldora con borde negro.
2. **Hero editorial** en 2 columnas: kicker en mayúsculas, H1 serif enorme (3–4 líneas), párrafo,
   botón bordó "Explore the ebooks ↗". A la derecha, imagen 3:2 recortada **en arco** (bordes superiores redondos).
3. **Biblioteca** "A new idea to begin with." + "Choose a digital guide and learn at your own pace.":
   grilla de 3 columnas, tarjetas con la portada (mockup de libro), "01 / DIGITAL GUIDES", título serif,
   1 línea de resumen, precio a la izquierda y "View ebook ↗" a la derecha. Orden: de menor a mayor precio.
4. **Banda bordó** con kicker "DIGITAL GUIDES", una frase grande en serif y "Contact us ↗".
5. **Footer bordó**: logo claro, nombre de la LLC en negrita, dirección registrada, email y teléfono;
   a la derecha "Join our email list" con campo en píldora y botón redondo →; abajo "Links" (Search + políticas)
   y "© año LLC".

## Ficha de producto
2 columnas: portada a la izquierda; a la derecha "← Our Ebooks", H1 serif, precio, botón ancho bordó
redondeado "Add to cart" y la descripción (párrafo + subtítulo + viñetas con el tema en negrita).

## Imágenes (ver `prompts-imagenes.md` y `generar_imagenes.py`)
- **Portadas 1:1 (1024×1024):** libro de tapa dura parado, levemente en ángulo, sobre fondo liso del color paper
  (se funde con la página). Tapa: franja superior clara con el título en serif y "DIGITAL EDITION" chiquito;
  mitad inferior con una ilustración plana del nicho en tonos del acento (monocromo bordó/marrón). Lomo en color acento.
- **Hero 3:2:** flat-lay (vista desde arriba) de objetos del nicho, monocromo en tonos del acento y paper, luz suave, sin texto.
- **Logo:** ícono de línea fina + wordmark serif + subtítulo en versalitas, sobre blanco (el tema lo mezcla con el fondo).

## Diferencias a propósito con la referencia
- La referencia usa textos tipo "proposed guide", "may cover": **no** se copian (prometer solo lo concreto).
- Se agrega barra de anuncios con el descuento y FAQ opcional (no rompen el estilo).
