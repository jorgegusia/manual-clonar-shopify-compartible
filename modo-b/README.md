# Manual modo B: crear una tienda de EBOOKS copiando el ESTILO de una tienda sin acceso

Para cuando **no** hay acceso al admin de la tienda que se quiere copiar (eso es el modo A, el README principal).
El modo B **siempre** arma una tienda de **productos digitales (ebooks)** cuyo tema sale del **rubro de la LLC**
del usuario, con el estilo de una tienda de referencia (o el estilo por defecto) e imágenes generadas con **Nano Banana** (API de Gemini de Google; Higgsfield como alternativa).

Archivos de esta carpeta:
| Archivo | Para qué |
|---|---|
| `ficha-llc-ebooks.md` | Datos que hay que pedirle al usuario (LLC, rubro, tienda, estilo) |
| `ejemplo-marca.json` | Molde de `marca.json`: todos los datos y textos de la tienda en un solo archivo (ejemplo ficticio) |
| `estilo-referencia.md` | Estilo por defecto "Paper Studio" (análisis de la referencia) |
| `prompts-imagenes.md` | Prompts de las imágenes (portadas, hero, logo) y cómo revisarlas |
| `plantillas/tema/sections/eb-*.liquid` | Secciones del tema que recrean el estilo (header, home, producto, footer) |
| `plantillas/politicas/*.html` | Las 5 políticas en inglés con marcadores `{{LLC}}`, `{{ADDRESS}}`... |

Scripts (en `scripts/` de la skill o del repo del manual, correr con `python3 -I`): `analizar_referencia.py`, `generar_imagenes.py`, `armar_productos.py`,
`armar_tema.py`, `generar_politicas.py`, más los del modo A que se reutilizan (`edit_theme_json.py`,
`upload_videos.py ... IMAGE`, `capturar-link-auth.sh`).

---

## 0. Reglas (además de las del modo A §0)

1. **Siempre ebooks o productos digitales.** Nunca productos físicos en modo B.
2. **El tema de los ebooks sale del rubro de la LLC.** Así la tienda es coherente con lo que la LLC declara
   (Shopify Payments, Stripe y los bancos lo revisan). Si el rubro es muy amplio, proponer 3 nichos y que elija.
3. **Copiar el diseño, no el contenido.** De la referencia se toma estructura, proporciones, paleta, tipografías
   y tipo de imagen. Textos, imágenes, nombre, logo y LLC son **propios**. Nunca dejar datos de la LLC de la
   referencia (el análisis los muestra en "Footer: NO copiar").
4. **Todo lo que ve el cliente, en inglés.** Al usuario se le habla en español.
5. **Prometer solo lo concreto.** Nada de "may cover", "proposed", cantidad de páginas o resultados inventados.
   Disclaimer educativo en todos los productos.
6. **Todo por CLI** (`shopify store execute` / `bulk execute` / `theme ...`), igual que el modo A. Lo único externo son las
   imágenes: API de Gemini con la key del usuario guardada en `~/.config/gemini/api_key` (nunca pedirla por chat ni
   guardarla en un repo).
7. **Nunca tocar el tema publicado:** se trabaja sobre un duplicado. Publicar, quitar la contraseña y borrar cosas,
   solo con OK explícito.
8. **Carpeta del cliente:** `clientes/<tienda>/` con `FICHA.md`, `datos/marca.json`, `referencia/`, `tema/`,
   `politicas/`, `imagenes/` (URLs y elecciones).

---

## 1. Ficha y datos (antes de tocar nada)

1. Crear `clientes/<tienda>/`, copiar `ficha-llc-ebooks.md` como `FICHA.md` y pedir en **un solo mensaje** lo que falte:
   LLC (nombre legal, estado, dirección, email, teléfono, horario, **rubro**), `.myshopify.com`, nombre comercial,
   código de descuento, referencia (opcional).
2. Confirmar dudas de escritura (ej. "Digita" vs "Digital"). Si no hay teléfono: `xxx xx xxx` y avisar.
   **Nunca inventar un teléfono real.**
3. Con el rubro, proponer **3 nichos de ebooks** (1 línea cada uno) y 3 nombres comerciales si no tiene. Esperar que elija.
4. Copiar `ejemplo-marca.json` a `clientes/<tienda>/datos/marca.json` y completarlo a medida que avanza.

---

## 2. Analizar la referencia (sin acceso)

Si el usuario no pasa referencia, usar el **estilo por defecto** (`estilo-referencia.md`) y saltar a §3.

```bash
python3 -I scripts/analizar_referencia.py https://TIENDA-REFERENCIA clientes/<tienda>/referencia
```
- Saca de lo **público**: tema base (`Shopify.theme`), secciones de cada página en orden, títulos, colores y
  tipografías más usados, productos de `/products.json` (precios, tipo, tamaño de imagen) y el texto del footer.
- Si responde 401 o redirige a `/password`, la tienda tiene contraseña: pedir capturas. Si da 0/409/"Error 1001",
  el dominio no apunta a ninguna tienda: pedir la `.myshopify.com`.
- **Capturas** con el navegador (home arriba, biblioteca, banda y footer, ficha de producto; en compu y celular)
  para comparar al final. Colores exactos: `getComputedStyle` en el navegador si el análisis no alcanza.
- Resumirle al usuario en 5–8 líneas qué se toma (estructura, paleta, tipografías, tipo de imágenes) y
  **qué no** (textos, LLC, imágenes).
- Si la referencia tiene secciones que nuestras plantillas no tienen, agregarlas a `eb-home.liquid` con el mismo
  patrón (CSS con prefijo propio, variables `--eb-*`, settings editables) y pasar `theme check`.

---

## 3. Tienda de destino: acceso y mercados

### 3.1 Acceso (igual que modo A §4)
```bash
shopify auth logout && shopify theme list --store DESTINO.myshopify.com
```
```bash
shopify store auth --store DESTINO.myshopify.com --scopes read_products,write_products,read_files,write_files,read_content,write_content,read_online_store_pages,write_online_store_pages,read_online_store_navigation,write_online_store_navigation,read_publications,write_publications,read_themes,write_themes,read_legal_policies,write_legal_policies,read_discounts,write_discounts,read_markets,write_markets,read_locales,write_locales,read_translations,write_translations,read_inventory,write_inventory
```
- Todos los permisos de una vez (incluidos **mercados y políticas**). Login en una pestaña de Terminal visible,
  de a una autorización.
- **Pegar SIEMPRE la URL completa en el chat** (y el código): el usuario usa varios perfiles de navegador y la abre en el que
  corresponde. `store auth` no imprime el link: correrlo desde el principio con
  `sh scripts/capturar-link-auth.sh DESTINO.myshopify.com <scopes>` y pasar lo que quede en `/tmp/opened-urls.log`.
  Se aprueba en la MISMA Mac (vuelve a 127.0.0.1) y en pocos minutos.
- Confirmar el dominio con `shop { name myshopifyDomain currencyCode }` antes de crear nada.

### 3.2 Mercados UK (GBP) y USA (USD), mismo número en las dos monedas
1. Leer: `shop { currencyCode enabledPresentmentCurrencies billingAddress { countryCodeV2 } }` y `markets(first:20){ nodes { id name status } }`.
2. Crear "United Kingdom" y "United States" (si ya existen, `marketUpdate`):
   ```graphql
   mutation($input: MarketCreateInput!){ marketCreate(input:$input){ market{ id name } userErrors{ field message code } } }
   ```
   ```json
   {"input":{"name":"United Kingdom","status":"ACTIVE","conditions":{"regionsCondition":{"regions":[{"countryCode":"GB"}]}},
     "currencySettings":{"baseCurrency":"GBP","baseCurrencyManualRate":"1.0","localCurrencies":false,"roundingEnabled":false}}}
   ```
   (USA igual con `US` y `USD`). Si la versión de la API pide otros campos, mirar el error y el esquema de `MarketCreateInput`.
3. Pasar los demás mercados a `DRAFT` (después de crear UK y US: no se puede apagar el último).
4. Verificar con `contextualPricing(context:{country:GB})` y `US` que 19.99 sea £19.99 y $19.99.

**Si falla con `MULTIPLE_CURRENCIES_NOT_SUPPORTED`:** la tienda no tiene Shopify Payments como pasarela.
No reintentar con variantes. Pedirle al usuario: Configuración → Pagos → activar Shopify Payments (completa él
los datos de la LLC; Claude nunca carga datos financieros) y moneda de la tienda en USD. Seguir con el resto y
volver al final. **Plan B** (solo si no puede activar Shopify Payments), explicarle antes la diferencia de ingresos:
UK en su propio mercado en USD y 12 ebooks extra visibles solo en UK, 2 por cada precio ("baja" ≈ ×1.30 y "alza" ≈ ×1.36):

| Precio base | UK baja | UK alza |
|---|---|---|
| 19.99 | 25.99 | 26.99 |
| 29.99 | 38.99 | 40.99 |
| 49.99 | 64.99 | 67.99 |
| 69.99 | 90.99 | 94.99 |
| 99.99 | 129.99 | 135.99 |
| 199.00 | 259.00 | 269.00 |

Visibilidad: `catalogCreate` (contexto mercado USA) → `publicationCreate` (catalogId, `defaultState: EMPTY`,
`autoPublish: false`) → publicar ahí SOLO los 6 base. UK sin catálogo ve los 18. Verificar con `publishedInContext`.

---

## 4. Contenido: nicho, productos y textos

**Receta fija (no preguntar):**
| # | Nivel | Precio | Nota |
|---|---|---|---|
| 01 | Fundamentos (entrada) | **19.99** | el más simple |
| 02 | Tema puntual | **29.99** | |
| 03 | Tema puntual | **49.99** | |
| 04 | Tema puntual | **69.99** | |
| 05 | Guía avanzada / completa | **99.99** | integra varios temas |
| 06 | **Colección completa** | **199.00** | reúne los 5; tags `bestseller` y `top`; portada = set de 3 libros |

- El precio sigue la profundidad del contenido (como en la referencia), de 19.99 a 199. Si el usuario pide otra
  escalera, cambiarla en `marca.json`; `armar_productos.py` solo exige 6 precios distintos entre 19 y 199 y que el top sea el más caro.
- **Descripción** (inglés): párrafo de qué es y para quién → `<h3>What's inside</h3>` con 4–6 viñetas
  "**Tema:** explicación" → `<h3>Format</h3>` (PDF, entrega instantánea por email, cualquier dispositivo) →
  disclaimer educativo ("...not a substitute for professional advice. No specific results are guaranteed.") →
  "*Digital product only. No physical item is shipped.*"
- `resumen`: 1 línea corta para la tarjeta de la home.
- Textos de la home (`home` en marca.json): kicker, H1 de 6–9 palabras, intro de 1–2 frases, banda de cierre, 3–6 FAQ.
- Mostrarle al usuario la tabla de títulos y precios antes de generar imágenes.

---

## 5. Imágenes (Nano Banana, API de Gemini)

**Requisito (una sola vez, lo hace el usuario):** key de [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
con **facturación activa** (Nano Banana Pro no tiene uso gratis) y guardada en su Mac sin pasarla por el chat:
```bash
mkdir -p ~/.config/gemini && read -s "k?Pegá tu API key de Google y Enter: " && print -r -- "$k" > ~/.config/gemini/api_key && chmod 600 ~/.config/gemini/api_key && unset k && echo " Guardada"
```
Comprobar que anda (y qué modelos de imagen tiene): `python3 -I scripts/generar_imagenes.py --listar`.

1. Completar en `marca.json`: `tienda.icono` (ícono del logo), `tienda.subtitulo` (ej. "MARKETING LIBRARY"),
   `productos[].objetos` (3–5 objetos concretos del tema de cada ebook) y `home.objetos_hero`.
2. Ver cantidad y costo **antes** de gastar, y pedirle el OK al usuario:
   ```bash
   python3 -I scripts/generar_imagenes.py clientes/<tienda>/datos/marca.json clientes/<tienda>/imagenes --prueba
   ```
   Normal: 9 imágenes (6 portadas 1:1, hero 3:2, 2 logos 21:9) ≈ **US$ 1,20** con Nano Banana Pro en 2K
   (US$ 0,134 c/u; 4K US$ 0,24). Con repeticiones, ~US$ 2 por tienda.
3. Generar (sin `--prueba`). Es reanudable; los 429 se reintentan solos.
4. **Revisar cada imagen** (abrirlas con Read y hacer zoom): título exacto en cada portada, logo bien escrito,
   hero sin texto. Rehacer solo la que falle: `--solo portada-<handle> --rehacer` (o `--solo logos`).
5. Elegir el logo, recortarle el margen y guardarlo como `<slug>-logo.<ext>` (la API devuelve JPG); mover los descartes a `imagenes/descartes/`.
6. Subir a Files (staged upload, ya probado en el modo A):
   ```bash
   python3 -I scripts/upload_videos.py DESTINO clientes/<tienda>/imagenes clientes/<tienda>/imagenes/subidas.json IMAGE
   ```
   `subidas.json` queda `{archivo: id}`: se pasa tal cual a `armar_productos.py --portadas` (las portadas se
   reutilizan por ID, no se suben dos veces). Hero y logo se usan en el tema como
   `shopify://shop_images/<slug>-hero.jpg` y `.../<slug>-logo.jpg` (con la extensión real; ponerlos en `marca.json` → `imagenes`).
   Verificar `fileStatus: READY` antes de subir el tema.
- El logo sale sobre fondo **blanco** a propósito: el header lo mezcla con el fondo (`mix-blend-mode: multiply`) y el
  footer lo muestra claro (`invert` + `screen`), así no hace falta PNG transparente.

**Alternativa: Higgsfield** (si el usuario ya paga el plan). Conector: Configuración → Conectores → Agregar conector
personalizado → `https://mcp.higgsfield.ai/mcp`. Mismos prompts (`prompts-imagenes.md`), tandas de máximo 6
(con 9 o más da 429), y sus URLs se pasan directo a Shopify (`fileCreate` con `originalSource` o
`armar_productos.py --portadas {handle: url}`).

---

## 6. Productos y descuento

```bash
python3 -I scripts/armar_productos.py clientes/<tienda>/datos/marca.json clientes/<tienda>/datos/productset.jsonl --portadas clientes/<tienda>/datos/portadas.json
```
Frena si algo no cumple la receta (6 productos, precios, top, disclaimer, frases prohibidas, portadas). Después:
```bash
shopify store bulk execute -s DESTINO --allow-mutations --variable-file clientes/<tienda>/datos/productset.jsonl --watch --output-file clientes/<tienda>/datos/productset-result.jsonl -q 'mutation($input: ProductSetInput!){ productSet(input:$input){ product{ id handle } userErrors{ field message code } } }'
```
- Publicar los 6 en **Online Store** (`publishablePublish` con el ID de esa publicación: buscarlo en `publications`).
- Cada variante queda con `requiresShipping: false` (si no, el checkout pide dirección).
- **Descuento:** código de la ficha, 15 %, todos los clientes, desde ahora, sin fecha de fin:
  `discountCodeBasicCreate` con `customerGets.items.all: true`, `customerGets.value.percentage: 0.15`,
  `context.all: ALL` (o `customerSelection.all: true` según la versión), `startsAt` = ahora.

---

## 7. Tema

1. Ver el tema publicado: `shopify theme list --store DESTINO < /dev/null`.
   - Si es **Horizon** (las tiendas nuevas lo traen): duplicarlo
     `shopify theme duplicate --store DESTINO --theme <ID_MAIN> --name "<Tienda>" --force --json < /dev/null`.
   - Si es otro tema: bajar Horizon de `https://github.com/Shopify/horizon` y subirlo con
     `theme push --unpublished --theme "<Tienda>"` (manual A §5.1). Las plantillas `eb-*` funcionan en cualquier tema
     Online Store 2.0, pero están probadas con Horizon.
2. Bajar el duplicado: `shopify theme pull --store DESTINO --theme <ID_NUEVO> --path clientes/<tienda>/tema < /dev/null`.
3. Armar los archivos:
   ```bash
   python3 -I scripts/armar_tema.py clientes/<tienda>/datos/marca.json clientes/<tienda>/tema
   ```
   Copia `sections/eb-*.liquid` y escribe `templates/index.json`, `templates/product.json`,
   `sections/header-group.json` y `sections/footer-group.json` (header con barra "15% OFF ... code X" y
   "Instant digital delivery", paleta y logo; footer con la LLC).
4. Validar: `shopify theme check --path clientes/<tienda>/tema` → los archivos `eb-*` y los 4 JSON sin errores.
5. Subir **en este orden** (si no, "la sección no existe"):
   ```bash
   shopify theme push --store DESTINO --theme <ID_NUEVO> --path clientes/<tienda>/tema --only sections/eb-header.liquid --only sections/eb-home.liquid --only sections/eb-product.liquid --only sections/eb-footer.liquid --json < /dev/null
   ```
   ```bash
   shopify theme push --store DESTINO --theme <ID_NUEVO> --path clientes/<tienda>/tema --only sections/header-group.json --only sections/footer-group.json --only templates/index.json --only templates/product.json --json < /dev/null
   ```
6. Favicon: ícono del logo recortado en cuadrado → `config/settings_data.json` `current.favicon` con `edit_theme_json.py`.

---

## 8. Todo en inglés, menús y páginas

- Menú `main-menu`: Home (`/`) / Our Ebooks (`/collections/all`) / Contact (`/pages/contact`) con `menuUpdate`
  (conservar los IDs de los ítems que ya existan). Menú `footer`: vacío o "Search" (las políticas ya salen solas).
- Página Contact: título "Contact" y el formulario del tema (template `page.contact`).
- Si el idioma principal de la tienda no es inglés: `shopLocaleEnable(locale:"en")` y publicarlo; **el usuario**
  pone el inglés como predeterminado en Configuración → Idiomas (el banner de cookies, checkout y emails dependen de eso).
  Mientras tanto, copiar `locales/en.default.json` a `locales/es.json` en el tema duplicado hace que los textos del
  tema salgan en inglés.

---

## 9. Políticas (con los datos de la LLC)

```bash
python3 -I scripts/generar_politicas.py clientes/<tienda>/datos/marca.json clientes/<tienda>/politicas
```
Cargar cada una (5 veces, una por archivo `*.vars.json`):
```bash
shopify store execute -s DESTINO --allow-mutations --variable-file clientes/<tienda>/politicas/REFUND_POLICY.vars.json -q 'mutation($shopPolicy: ShopPolicyInput!){ shopPolicyUpdate(shopPolicy:$shopPolicy){ shopPolicy{ type url } userErrors{ field message } } }' < /dev/null
```
- La de privacidad falla si está en "gestión automática": el usuario la desactiva en Configuración → Políticas.
- Si `shopPolicyUpdate` no tiene permiso, mandarle al usuario `politicas-para-copiar.html` (botón "Copy" en cada una)
  para pegarlas en Configuración → Políticas.
- El footer lista solo las políticas cargadas (`shop.policies`).
- Recomendar que un abogado las revise antes de lanzar anuncios.

---

## 10. Verificación (obligatoria)

Por API:
- 6 productos ACTIVE, con imagen, `requiresShipping: false`, publicados en Online Store.
- Precios: `contextualPricing` GB y US → tabla Producto | UK | USA con el mismo número.
- Logo y hero `READY`; políticas cargadas; descuento activo; menús en inglés.

En el navegador (`https://DESTINO/?preview_theme_id=<ID_NUEVO>`; si hay contraseña, pedirla al usuario o verificar por API):
- Capturas home, ficha y carrito en compu y celular, **al lado de las de la referencia**. Corregir hasta que el diseño coincida.
- Revisar con JavaScript que cada link del header y footer dé 200, que no haya palabras en español ni datos de la
  LLC de la referencia, y que aparezcan la LLC y el teléfono propios.
- Cerrar las pestañas abiertas.

---

## 11. Entrega (en español, corta)

- Tabla de productos con precio en £ y $, cuál es el top, estado de los mercados y el código de descuento.
- Link de la vista previa del tema.
- Pendientes del usuario: Shopify Payments + moneda USD (si hizo falta), inglés como idioma predeterminado,
  nombre de la tienda, **PDF de cada ebook con Shopify Digital Downloads**, revisar políticas, y OK para
  publicar el tema y quitar la contraseña (`shopify theme publish --theme ID --force`, manual A §8).
- Actualizar `FICHA.md` y los dos repos del manual con lo aprendido (§12).

---

## 12. Errores conocidos y aprendizajes

Primera tienda real: oct 2026 (6 ebooks de lettering, UK + US, ~US$ 1,34 en imágenes).

| Problema | Causa | Solución |
|---|---|---|
| `MULTIPLE_CURRENCIES_NOT_SUPPORTED` | Sin Shopify Payments | Ver §3.2 (no reintentar variantes) |
| Error 429 al generar imágenes | Límite por minuto de la API | `generar_imagenes.py` espera y reintenta; en Higgsfield, tandas de 6 |
| Error 400/403 de la API de Gemini | Key sin facturación o modelo no habilitado | Activar facturación en AI Studio; `--listar` para ver modelos |
| Texto mal escrito en portada o logo | El modelo inventa letras | Revisar con zoom y regenerar solo esa |
| "Section does not exist" al subir `index.json` | Se subió el JSON antes que la sección | Subir primero `sections/eb-*.liquid` |
| "Página 404" en el editor del tema | Falta la página o política | Crearla (§8–9) |
| El checkout pide dirección | Variante con envío | `requiresShipping: false` (lo pone `armar_productos.py`) |
| Referencia con "Error 1001" | El dominio no apunta a Shopify | Pedir la `.myshopify.com` |
| Logo con recuadro en el footer | Logo con fondo de color (no blanco) | Regenerar sobre blanco puro o desactivar "Show logo in light color" |
| Nano Banana devuelve **JPG**, no PNG | Formato de salida del modelo | Usar la extensión real en `marca.json → imagenes` (`.../<slug>-logo.jpg`) |
| Palabra inventada dentro de una ilustración ("hond") | `objetos` pedía "a handwritten word" | En `objetos` no pedir palabras ni letras; rehacer solo esa imagen con `--solo ... --rehacer` |
| Logo con mucho margen blanco | El modelo centra el logo en 21:9 | Recortar centrado: `sips -c ALTO ANCHO logo-1.jpg --out <slug>-logo.jpg` |
| `theme pull` corta con `EADDRNOTAVAIL` / `ENOTFOUND` | Red inestable con cientos de archivos | No hace falta el tema completo: alcanza con `locales/en.default.json`; armar con `armar_tema.py` y subir con `push --only` |
| La tienda está en GBP (no USD) | El usuario la pasó a libras | Funciona igual: UK en GBP sin redondeo + US en USD con tasa manual 1.0 → mismo número en £ y $ |
| Vista previa redirige a `/password` | Tienda con contraseña | Pasarle al usuario el link de vista previa: logueado en el admin la ve; Claude no ingresa la contraseña |
