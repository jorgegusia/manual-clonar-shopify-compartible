# Manual v4: clonar una tienda Shopify completa de ORIGEN a DESTINO (por CLI) y adaptarla a la marca nueva

Es la memoria de trabajo: qué se hace, en qué orden, qué falló antes y cómo se resolvió.
Sirve para **cualquier** par de tiendas y **cualquier** tema. Está probado en clones reales: una tienda de cartas coleccionables, una de cosmética coreana y una de calzado (ver *Casos*, al final).

**Cómo usarlo:** abrí un chat nuevo con Claude Code, pasale el link de este repo o pegá este README y decile:

> **"Seguí el manual de este README y usá los scripts de `scripts/`. Origen: `XXXX.myshopify.com`. Pedime el acceso al ORIGEN, descargá y analizá todo. Cuando esté listo, pedime el DESTINO, subí todo, compará y corregí en loop hasta que quede idéntica. Después adaptala a la marca nueva. Publicá el tema solo cuando yo diga."**

Los scripts están en `scripts/` y las consultas GraphQL en `queries/`. Hay que copiarlos a una carpeta de trabajo, por ejemplo `scripts/` dentro de la carpeta del cliente, **separada** de lo descargado. Se corren con `python3 -I`.

---

## Antes de empezar: datos que hay que tener listos

Completá `plantilla-datos-tienda.md` (está en este repo) y pasásela a Claude junto con el pedido. Los valores de abajo son **ejemplos inventados**: reemplazalos por los tuyos.

| Dato | Ejemplo | Para qué se usa |
|---|---|---|
| Tienda de **origen** (`.myshopify.com`) | `tienda-origen.myshopify.com` | Descargar todo |
| Tienda de **destino** (`.myshopify.com`) | `tienda-destino.myshopify.com` | Subir todo |
| Cuenta dueña de cada tienda | `dueno-origen@ejemplo.com` / `dueno-destino@ejemplo.com` | Logins del CLI (los hace el usuario en el navegador) |
| Moneda del destino (igual al origen) | `GBP` | Que no se redondeen precios |
| Dominio público del destino | `glowbeauty.com` | Links, emails, verificación en vivo |
| **Nombre de la marca nueva** | `Glow Beauty` | Reemplaza a la marca vieja en páginas, políticas, footer y fichas |
| **Empresa legal** (razón social) | `EJEMPLO COMMERCE LLC` | Políticas, Legal Notice, footer |
| Dirección legal | `123 Example St, Suite 100, Springfield, NM 87500, USA` | Políticas, Contact, footer |
| Teléfono | `+1 000 000 0000` | Políticas |
| **Email de soporte** | `support@glowbeauty.com` | Reemplaza todos los emails viejos |
| Logo (fondo claro y oscuro) | `logo-negro.svg`, `logo-blanco.svg` | Header (y página de contraseña) |
| Favicon | `favicon.svg` (cuadrado) | Pestaña del navegador |
| Políticas (PDF o texto) | `Politicas.pdf` | Reembolso, privacidad, términos, envíos, contacto, Legal Notice |
| Archivos locales (opcional) | Matrixify, zip del tema, CSV | Solo para comparar: verificar de qué tienda y fecha son |

> Si falta algún dato, Claude lo pregunta. **Nunca** se le pasan contraseñas: los logins los aprueba el usuario en el navegador.

---

## 0. Reglas para Claude (leer antes de empezar)

1. **Orden fijo:** primero el ORIGEN completo (acceso, descarga y análisis). Recién después el DESTINO (acceso, comparación, subida, verificación). Después la ADAPTACIÓN a la marca y al final la publicación, con OK del usuario.
2. **Todo por Shopify CLI.** No depender del conector MCP de Shopify, que se invalida seguido.
   - Tema: `shopify theme pull / push / list / publish / rename`.
   - Datos: `shopify store auth` + `shopify store execute` / `shopify store bulk execute` (GraphQL Admin API).
3. **Nunca crear a ciegas en el DESTINO.** Siempre exportar el destino y **compararlo** con el origen, y subir solo lo que falta o difiere. En los dos casos reales el destino ya tenía datos de importaciones anteriores.
4. **Saber de dónde viene cada diferencia antes de decidir.** Que algo difiera en el destino **no prueba** que lo hayan editado a mano: en un caso real, las "ediciones" eran restos de un Matrixify viejo de **otra** tienda. Preguntar o revisar el Import Result antes de "respetarlo" o pisarlo.
5. **Si el usuario da archivos locales** (zip de tema, Matrixify, CSV), **verificar de qué tienda y de qué fecha son** antes de usarlos:
   - Matrixify: hojas `Shop` / `Export Summary`, columna `Shopify Domain`.
   - Tema: comparar el zip con un `theme pull` fresco.

   En un caso real eran de otra tienda y de 3 semanas antes. Se descargó todo de nuevo desde el origen.
6. **Loop:** subir, re-exportar el destino, comparar (`compare.py`), corregir y repetir hasta que diga **NINGUNA**.
7. **Carpeta de trabajo:** la que indique el usuario, con subcarpetas `tema/`, `imagenes-tema/`, `videos-tema/`, `datos/` y `politicas/`. Los scripts van aparte. No pisar los archivos originales del usuario.
8. **Acciones públicas o irreversibles solo con OK explícito:** publicar el tema, borrar o desactivar descuentos, borrar cualquier cosa, quitar la contraseña. Si el clasificador de permisos de Claude Code bloquea algo (por ejemplo, tocar descuentos), **no buscarle la vuelta**: explicarle al usuario cómo hacerlo en el admin.
9. **Comandos del CLI desde Bash:** agregar siempre `< /dev/null`, porque si no a veces se cuelgan esperando input. En macOS no existe `timeout`. En zsh una variable con varios IDs **no** se separa sola en un `for`: listar los IDs explícitos o usar Python.
10. **Logins (CLI y `store auth`):** correrlos en una pestaña de Terminal **visible**. Pegarle al usuario en el chat la **URL completa y el código** (usa varios perfiles de navegador). `store auth` no imprime el link: usar `scripts/capturar-link-auth.sh` desde el principio. Avisar que se vencen en pocos minutos. Si son dos autorizaciones, pedirlas **de a una**.
11. **Responder en español, con lenguaje simple.** El usuario no es técnico: explicar qué significa cada decisión ("igual al origen" = qué se borra o cambia).

---

## 1. Herramientas

```bash
node -v
```
```bash
shopify version
```
```bash
shopify commands | grep "store execute"
```
Si falta algo: Node LTS y `npm install -g @shopify/cli@latest`. La versión del CLI tiene que traer `store auth / store execute / store bulk execute`.

El aviso `npm error ... root-owned files` del auto-update del CLI es inofensivo y se ignora.

---

## 2. ORIGEN: acceso

Pedir el dominio `.myshopify.com`, que está en la URL del admin: `admin.shopify.com/store/ESTE-NOMBRE`. Si el usuario pasa un dominio sin decir si es origen o destino, **confirmarlo**.

### 2.1 CLI (tema)
```bash
shopify theme list --store ORIGEN.myshopify.com
```
**"Looks like you don't have access to this dev store"** casi siempre significa que el CLI tiene **cacheada la sesión de otra cuenta**:
```bash
shopify auth logout && shopify theme list --store ORIGEN.myshopify.com
```
El usuario inicia sesión con la cuenta **dueña** de esa tienda. Cada tienda nueva suele ser de otra cuenta, así que en cada cambio de tienda hay que hacer logout + login.

### 2.2 API (datos), solo lectura
```bash
shopify store auth --store ORIGEN.myshopify.com --scopes read_products,read_files,read_content,read_online_store_pages,read_online_store_navigation,read_publications,read_inventory,read_themes,read_legal_policies,read_metaobjects,read_metaobject_definitions,read_discounts,read_markets
```
`store auth` **no imprime el link**: lo abre en el navegador. Si el usuario no lo ve, usar `scripts/capturar-link-auth.sh` (ver 4.2).

---

## 3. ORIGEN: descargar y analizar TODO

### 3.1 Tema publicado
```bash
shopify theme list --store ORIGEN.myshopify.com --json
```
```bash
shopify theme pull --store ORIGEN.myshopify.com --theme ID_LIVE --path tema
```

### 3.2 Imágenes y videos del tema
Los `shopify://shop_images/...` y `shopify://files/videos/...` **no viajan con el tema**:
```bash
grep -rhoE 'shopify://shop_images/[^"\\]+' tema/templates tema/sections tema/config | sort -u | sed 's#shopify://shop_images/##' > imagenes-tema/lista.txt
grep -rhoE 'shopify://files/videos/[^"\\]+' tema/templates tema/sections tema/config | sort -u
```
- **Imágenes:** se bajan con `curl -sL` desde `https://ORIGEN.myshopify.com/cdn/shop/files/<nombre>` (verificar el código 200).
  - Si alguna da **404**, puede que tampoco exista en el origen y que ya se vea vacía ahí. Confirmarlo con la lista de Files.
  - Buscarla en la tienda "madre" si la hay. En un caso real, 7 de 9 faltantes estaban en la tienda madre.
- **Videos:** sus URLs (`originalSource.url`) salen del bulk de Files (3.3). Se bajan con curl y **se suben por CLI** con `upload_videos.py`. Ya **no** hace falta el paso manual.

### 3.3 Datos (bulk export)
```bash
shopify store bulk execute -s ORIGEN --query-file queries/q_prod.graphql  --watch --output-file datos/productos-origen.jsonl
shopify store bulk execute -s ORIGEN --query-file queries/q_col.graphql   --watch --output-file datos/colecciones-origen.jsonl
shopify store bulk execute -s ORIGEN --query-file queries/q_files.graphql --watch --output-file datos/archivos-origen.jsonl
shopify store execute      -s ORIGEN -j --query-file queries/q_pages_menus.graphql --output-file datos/pages-menus-origen.json
shopify store execute      -s ORIGEN -j --query-file queries/q_shop.graphql        --output-file datos/shop-origen.json
```
Políticas públicas para comparar: `/policies/refund-policy`, `privacy-policy`, `terms-of-service`, `shipping-policy`, `contact-information` y `legal-notice`. Muchas tiendas tienen las políticas como **páginas** y no como políticas formales.

### 3.4 Análisis (reportar al usuario en una tabla)
- Cantidades: productos (activos / ocultos), variantes, imágenes, colecciones (manuales / automáticas), páginas, menús e ítems.
- **Moneda.** Va a ser crítica en el destino.
- **Metacampos de tipo `file_reference` / `list.file_reference`:** esos archivos tienen que existir en el destino **antes** que los productos. Ver 5.3.
- **Definiciones de metacampos** y si las colecciones automáticas usan reglas por metacampo.
- **Videos** del tema e **imágenes que faltan** incluso en el origen.
- Descuentos, redirecciones y canales de venta.
- Comparación con los archivos locales del usuario, si los dio (tienda y fecha).

---

## 4. DESTINO: acceso y chequeos

### 4.1 CLI
```bash
shopify auth logout && shopify theme list --store DESTINO.myshopify.com
```

### 4.2 API (lectura y escritura)
```bash
shopify store auth --store DESTINO.myshopify.com --scopes read_products,write_products,read_files,write_files,read_content,write_content,read_online_store_pages,write_online_store_pages,read_online_store_navigation,write_online_store_navigation,read_publications,write_publications,read_inventory,write_inventory,read_themes,write_themes,read_legal_policies,write_legal_policies,read_metaobjects,write_metaobjects,read_metaobject_definitions,write_metaobject_definitions,read_discounts,write_discounts,read_locations,read_markets
```
- **Pedir todos los permisos de una vez**, incluidos los de descuentos, `read_locations` (para cargar el stock) y `read_markets` (para comparar los mercados). Agregar permisos después obliga a re-autorizar y puede **cortar la sesión del CLI de temas** (error 401 *"Service is not valid for authentication"*). En ese caso: `shopify auth logout` + login de nuevo.
- Si el usuario no ve la página o se le vence (*"Timed out waiting for OAuth callback"*):
  ```bash
  sh scripts/capturar-link-auth.sh DESTINO.myshopify.com <scopes>
  ```
  ```bash
  cat /tmp/opened-urls.log
  ```
  Pasarle ese link. Tiene que aprobarlo **en la misma Mac y rápido**.
- Los cortes de red (`ETIMEDOUT`) pasan. Reintentar generando un código nuevo.

### 4.3 Chequeos ANTES de subir
1. **Moneda del destino = moneda del origen.** Si no, el usuario la cambia **antes** de importar, en Configuración → Detalles de la tienda. En un caso real el destino estaba en **PYG**, y Shopify redondeó 1.493 precios (£14.95 → 15). Se corrige con `build_prices.py` (6.2).
2. **Qué hay ya cargado:** exportar el destino con las mismas consultas y correr `compare.py`.
3. **Si el usuario ya importó un Matrixify,** pedirle el `Import_Result_*.xlsx` y leerlo con `scripts/xlsx2json.py`. Mirar **de qué tienda** era el archivo.

---

## 5. DESTINO: subir (en este orden)

### 5.1 Tema, sin publicar
```bash
shopify theme push --store DESTINO.myshopify.com --unpublished --theme "NOMBRE (clon)" --path tema --json
```
- Es **normal** el error `Setting 'video_full' value does not point to an applicable shopify-hosted video resource`. Significa que `templates/index.json` **no se guardó** y que la home va a dar 404. Se corrige en 5.4.
- **Verificar:** `theme pull` del tema nuevo a una carpeta temporal y `diff -rq` contra el original. Solo puede diferir `AGENTS.md`, que no es del tema.
  - También es normal que falten en `config/settings_data.json` los **app embeds** (bloques `shopify://apps/...`) de apps que el destino todavía no tiene: Shopify los descarta. Cuando el usuario instale esas apps, volver a subir `config/settings_data.json`.
  - Y que se borren settings que la sección ya no declara en su schema (ej. `pattern_*`): no cambian nada visible.

### 5.2 Definiciones de metacampos, ANTES de colecciones y productos
Sin definición, las colecciones automáticas con reglas `PRODUCT_METAFIELD_DEFINITION` **no se crean**. Matrixify da *"Metafield Definition [...] not found"*.

Crear cada una con `metafieldDefinitionCreate`, con el mismo namespace, key, name y type, `ownerType: PRODUCT`, `access.storefront: PUBLIC_READ`. Si se usa en reglas de colecciones, agregar `capabilities.smartCollectionCondition.enabled: true`. Al crearlas, Shopify adopta los valores ya existentes: verificar que `metafieldsCount` coincida.

### 5.3 Archivos: imágenes de metacampos y del tema, y videos
```bash
python3 -I scripts/classify_files.py datos/archivos-origen.jsonl datos/productos-origen.jsonl imagenes-tema/lista.txt datos/archivos-a-subir.json
python3 -I scripts/upload_images.py DESTINO.myshopify.com datos/archivos-a-subir.json datos/mapa-archivos.json
python3 -I scripts/upload_videos.py DESTINO.myshopify.com videos-tema datos/mapa-videos.json
```
- Las **fotos de producto no se suben aparte**: viajan con cada producto y si no se duplicarían en Files.
- `mapa-archivos.json` (id origen → id destino) es **imprescindible**: los metacampos `file_reference` guardan IDs, y los IDs del origen no existen en el destino.
- **Videos:** Shopify **rechaza** `fileCreate` con una URL de video. Por eso `upload_videos.py` hace staged upload: pide el espacio de subida, manda el archivo con POST y después hace `fileCreate`.
- **Verificar:** cantidad, sin duplicados (un reintento por timeout puede duplicar) y `fileStatus: READY`.

### 5.4 Re-subir la home cuando los videos estén READY
```bash
shopify theme push --store DESTINO.myshopify.com --theme ID --only templates/index.json --path tema --json
```
Tiene que terminar sin `errors`.

### 5.5 Productos
**Opción A (CLI, recomendada):**
```bash
python3 -I scripts/build_productset.py datos/productos-origen.jsonl datos/destino-productos.jsonl --map datos/mapa-archivos.json --location gid://shopify/Location/ID_DESTINO
shopify store bulk execute -s DESTINO --allow-mutations --variable-file datos/destino-productos.jsonl --watch --output-file datos/productset-result.jsonl -q 'mutation($input: ProductSetInput!){ productSet(input:$input){ product{ id handle } userErrors{ field message code } } }'
```
- **Foto de cada variante** (ej. una por color): `q_prod.graphql` trae `image { url }` de cada variante y `build_productset.py` la asigna con `file` (la misma URL que en `files`). Sin eso, al elegir un color no cambia la foto.
- **Stock:** con `--location` (ID de la ubicación del destino, `locations(first:5){nodes{id name}}`) se carga el `inventoryQuantity` del origen en las variantes con seguimiento de stock.
- Verificar `referencias de archivo sin mapear: 0`. Con el resultado se arma `mapa-productos.json` (`{handle: id}`).
- **Publicar** en los canales (bulk `publishablePublish`): lo creado por API **no se publica solo**. Usar los mismos canales que el origen, si existen en el destino.

**Opción B (Matrixify, la hace el usuario):** exportar **del ORIGEN y en el momento**, importar en el destino y pasar el Import Result (ver la tabla de errores).

### 5.6 Colecciones
```bash
python3 -I scripts/sync_collections.py DESTINO datos/colecciones-origen.jsonl datos/colecciones-destino.jsonl datos/mapa-productos.json <publicationId-Online-Store>
```
Crea las manuales que faltan (y las publica) y deja los mismos productos **en el mismo orden**. Las automáticas se crean con `collectionCreate` + `ruleSet`, con `conditionObjectId` = ID de la definición del metacampo **en el destino**.

### 5.7 Páginas, menús, políticas, redirecciones
- **Páginas:** comparar `title`, `body`, `isPublished` y `templateSuffix`. Las faltantes con `pageCreate` y las vacías con `pageUpdate`.
  - `data-sharing-opt-out` la genera Shopify en cada tienda: no tocarla.
  - Las diferencias de codificación (`&quot;` vs `"`) no cuentan.
- **Menús:** `python3 -I scripts/sync_menus.py DESTINO datos/pages-menus-origen.json main-menu,footer,...`. Reasigna cada ítem al recurso del destino por handle. **No** sincronizar `customer-account-main-menu`, porque sus URLs llevan el ID de cada tienda.
  - Los ítems de tipo **política** (`SHOP_POLICY`) se reasignan por tipo. Si la política todavía no existe en el destino (ej. privacidad en gestión automática) el menú falla con *"shop_policy not found"*: cargar primero las políticas y después los menús.
- **Políticas:** `shopPolicyUpdate` con `type` REFUND_POLICY, PRIVACY_POLICY, TERMS_OF_SERVICE, SHIPPING_POLICY, CONTACT_INFORMATION o LEGAL_NOTICE.
  - La **de privacidad** falla si está en gestión automática (*"Automatic management for Privacy Policy must be turned off"*). La desactiva el usuario en Configuración → Políticas → Privacy policy.
  - "Purchase options cancellation policy — Required" solo aplica si se venden suscripciones o preventas.
- **Redirecciones:** `urlRedirectCreate` para las que falten.
- **Descuentos:** comparar con el origen. Los que vinieron de importaciones viejas se **desactivan**, y lo hace el usuario si el clasificador lo bloquea. Ojo con los **automáticos**: aplican a todas las compras sin código.

---

## 6. Verificar y corregir en loop

### 6.1 Comparación completa
Re-exportar el destino (3.3 con `-s DESTINO`) y correr:
```bash
python3 -I scripts/compare.py datos/productos-origen.jsonl datos/productos-destino.jsonl datos/colecciones-origen.jsonl datos/colecciones-destino.jsonl datos/mapa-archivos.json
```
Tiene que decir **NINGUNA** en productos y en colecciones. Compara título, estado, plantilla, variantes, precios, imágenes, metacampos (incluido `file_reference` mapeado) y los productos y su orden en cada colección.

### 6.2 Precios (si la moneda estuvo mal)
```bash
python3 -I scripts/build_prices.py datos/productos-origen.jsonl datos/productos-destino.jsonl datos/precios.jsonl
shopify store bulk execute -s DESTINO --allow-mutations --variable-file datos/precios.jsonl --watch --output-file datos/precios-result.jsonl -q 'mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!){ productVariantsBulkUpdate(productId:$productId, variants:$variants){ productVariants{ id price } userErrors{ field message } } }'
```
Volver a correr `build_prices.py`: tiene que dar 0.

### 6.3 Canales y tienda en vivo
- Revisar `publishedOnPublication` de productos y colecciones contra el origen. Los "free gift" suelen estar solo en Online Store, a propósito.
- Probar `/`, una colección, un producto y una página. Si hay contraseña, todo redirige a `/password`.
- **Comparar el texto visible** del origen en vivo contra la vista previa del destino. La vista previa necesita cookies, porque redirige y pierde el `preview_theme_id`:
  ```bash
  curl -s -c cj -b cj -L -o destino.html "https://DESTINO.myshopify.com/products/HANDLE?preview_theme_id=ID"
  ```
  Sacar las etiquetas y hacer `diff` con la misma página del origen. Lo típico que queda: el nombre de la tienda ("My Store") y el **selector de países** si los mercados del destino no son los mismos que los del origen.

---

## 7. ADAPTAR a la marca nueva (después de clonar)

El clon trae textos, emails y datos legales de la tienda vieja. Hay que buscarlos y adaptarlos con los datos que dé el usuario: marca, email (ej. `support@DOMINIO.com`), empresa, dirección y teléfono.

1. **Buscar el texto visible viejo** en el HTML en vivo, sin etiquetas:
   ```bash
   curl -sL https://DOMINIO/pages/x | sed 's/<[^>]*>/ /g' | grep -oiE "MarcaVieja|email-viejo|ciudad-vieja"
   ```
   - Si **todas** las páginas muestran lo mismo, viene del **header o footer**.
   - Ignorar nombres internos: clases CSS `marcavieja-*`, archivos `marcavieja-*.png`, comentarios del código y el campo *vendor* de los productos.
2. **Dónde suele estar:**
   - **Tema:** barra de anuncio (`header-group.json`), footer (bloque de **contacto**: dirección y email; **copyright**, que suele estar en un **bloque** y no en la sección), `templates/product.json` (bloques de garantía y "Shipping & Return") y popup de bienvenida.
   - **Páginas:** contact, about-us, brand-story, disclaimer y cs-center (FAQ).
   - **Políticas:** las 6.
   - Para editar los JSON del tema usar `scripts/edit_theme_json.py`, que preserva el comentario `/* */` del inicio, y después `theme push --only <archivo> --allow-live`.
3. **Políticas desde un PDF del usuario:** extraer el texto con PDFKit de macOS (no hay `pdftoppm`):
   ```bash
   osascript -l JavaScript -e 'ObjC.import("PDFKit"); var d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath("/ruta.pdf")); var o=[]; for(var i=0;i<d.pageCount;i++){o.push(ObjC.unwrap(d.pageAtIndex(i).string))} o.join("\n")'
   ```
   - Armar el HTML a mano: la extracción desordena las viñetas. Reemplazar marca y email y dejar igual empresa, dirección y teléfono, salvo que el usuario diga otra cosa.
   - Guardar cada política en `politicas/*.html` y cargarla con `shopPolicyUpdate`.
4. **Coherencia:** si las políticas nuevas contradicen otras páginas (FAQ, acordeón de devoluciones de la ficha), alinear esas páginas con las políticas o resumirlas con link a la política.
5. **Logo y favicon (SVG del usuario):**
   - Convertirlos a PNG con `sips -s format png -z ALTO ANCHO archivo.svg --out archivo.png`. El tema declara el favicon como PNG de 32×32.
   - Subirlos con `upload_videos.py <tienda> <carpeta> <hecho.json> IMAGE` (staged upload).
   - Asignarlos: el logo del header suele ser un setting de la **sección** del header (`sections.<header>.settings.logo`); el favicon y el logo general van en `config/settings_data.json` (`current.favicon`, `current.logo`).
   - Logo **negro** si el header es blanco: mirar el `background` en el CSS del header.
6. **Nombre interno del tema:** `shopify theme rename --theme ID --name "Marca"`.
7. **Lo que NO se puede por API:** el **nombre de la tienda**, que se ve en la pestaña del navegador, los emails y el checkout. Lo cambia el usuario en `admin.shopify.com/store/<tienda>/settings/general` → Store details. Lo mismo el *Homepage title* (Online Store → Preferences).

---

## 8. Publicar (solo con OK del usuario)
```bash
shopify theme publish --store DESTINO.myshopify.com --theme ID --force
```
Confirmar con `theme list` (rol `live`) y con `Shopify.theme = {..."role":"main"}` en el HTML. El tema anterior queda guardado para volver atrás.

**Checklist del usuario:** home completa (videos, banners), 2 fichas de producto (metacampos e imágenes de detalle), menú y footer, páginas, políticas y una compra de prueba.

**Fuera de alcance (lo revisa el usuario):** nombre de la tienda, dominio, pagos, envíos y zonas, impuestos, Markets, apps y su configuración, notificaciones por email, idiomas, ubicaciones de inventario, clientes y pedidos (no se clonan).

---

## 9. Errores reales y su solución

| Síntoma | Causa | Solución |
|---|---|---|
| `Looks like you don't have access to this dev store` | Sesión del CLI cacheada con otra cuenta | `shopify auth logout` + login con la cuenta dueña |
| Conector MCP de Shopify "invalidated" una y otra vez | El conector pierde la autorización | No depender de él: `shopify store auth/execute` |
| `Setting 'video_full' ... shopify-hosted video` en el push | Videos inexistentes en el destino → `index.json` no se guarda (home 404) | Subir los videos (5.3) y re-push de `templates/index.json` |
| `fileCreate` con URL de video rechazado | Shopify exige subir los bytes del video | `upload_videos.py` (staged upload) |
| Matrixify: `Metafield reference value not found` | Faltan en destino los archivos de metacampos `file_reference` | Subirlos antes (`classify_files` + `upload_images`) y reapuntar IDs (`--map`) |
| Matrixify: `Metafield Definition [...] not found` (colecciones automáticas) | Faltan las definiciones de metacampos | `metafieldDefinitionCreate` con `smartCollectionCondition` (5.2) |
| Matrixify: `URL is not valid ... 502 Bad Gateway` | El CDN de una imagen externa falló → **el producto no se crea** | Crear ese producto con `build_productset.py ... <handle>` + productSet |
| Matrixify: `Location for column "Inventory Available: <dirección>" not found` (falla **todo**) | El archivo trae una ubicación de inventario de otra tienda | Sacar esas columnas o crear la ubicación. O cargar los productos por CLI |
| Matrixify: `Published: Shop / Point of Sale ... channel not found` | El canal no existe en el destino | Solo un aviso: publicar en los canales que existan |
| Matrixify: 100 ítems de menú `Resource Handle ... not found` | Se importaron menús antes que productos y colecciones | Sincronizar menús al final con `sync_menus.py` |
| Precios redondeados (14.95 → 15) | Moneda del destino sin decimales (PYG) | Cambiar la moneda **antes**. Si ya pasó, `build_prices.py` |
| Descuentos "nuevos" activos en el destino (WELCOME15, automático 10%) | Venían en un Matrixify viejo de otra tienda | Compararlos con el origen. Los desactiva el usuario |
| `Automatic management for Privacy Policy must be turned off` | La política de privacidad es automática | El usuario la desactiva y después `shopPolicyUpdate` |
| `store auth` no muestra link / `Timed out waiting for OAuth callback` | Abre el navegador directo / el usuario tardó | `capturar-link-auth.sh`, pasar el link y aprobar rápido |
| `401 Service is not valid for authentication` en `theme ...` | Se re-autorizó `store auth` y se cortó la sesión de temas | `shopify auth logout` + login |
| `ETIMEDOUT` en el CLI | Cortes de red | Reintentos automáticos en los scripts. Verificar duplicados después |
| `store execute` sin salida o colgado | Esperaba stdin | Agregar `< /dev/null` |
| Texto viejo sigue visible después de cambiar un setting | Estaba en un **bloque** y no en la sección | `grep` del texto exacto en los JSON del tema |
| `json.load` falla en `settings_data.json` / `*-group.json` | Comentario `/* */` al inicio | `edit_theme_json.py` |
| Borrar o desactivar descuentos bloqueado por Claude Code | Clasificador de permisos (recurso compartido) | No forzarlo: lo hace el usuario en el admin, o agrega un permiso con `/permissions` |
| Imágenes del tema en 404 | Tampoco existen en el origen | Buscarlas en la tienda madre o pedírselas al usuario |
| Pestaña del navegador dice "My Store" | Nombre de la tienda por defecto | Lo cambia el usuario en Settings → General (no hay API) |
| Una imagen del tema `.avif` aparece en Files del destino como `.png` | Shopify convierte AVIF al crear el archivo | Cambiar la referencia `shopify://shop_images/X.avif` → `X.png` en el JSON del tema del destino |
| Menú: `Couldn't create link "Privacy Policy", shop_policy not found` | La política no existe todavía en el destino | Cargar las políticas antes; `sync_menus.py` reasigna `SHOP_POLICY` por tipo |
| Al elegir un color no cambia la foto | Las variantes se crearon sin `file` | Exportar con `image { url }` en variantes y `build_productset.py` (asigna la foto) |
| `Access denied for markets field` | Falta `read_markets` en `store auth` | Agregarlo a los permisos desde el principio |

---

## 10. Historial de aprendizajes

- **v2:** dependía del conector MCP (se invalidaba) y los videos se subían a mano.
- **v3 (primer clon):** todo por CLI, chequeo de moneda, definiciones de metacampos antes de las colecciones, comparar antes de crear y re-sincronizar precios.
- **v4 (segundo clon):**
  - Videos subidos por CLI (staged upload).
  - Clasificación de Files: las fotos de producto no se suben aparte.
  - **Reapuntar metacampos `file_reference`** con un mapa de IDs.
  - Sincronización de colecciones (productos y orden) y de menús (resourceId por handle).
  - Verificar el origen y la fecha de los archivos locales del usuario.
  - Una diferencia no siempre es una edición intencional.
  - Fase de **adaptación a la marca**: políticas desde PDF, páginas, footer, ficha de producto, logo y favicon, nombre del tema.
  - Política de privacidad automática.
  - Link de `store auth` capturado con un wrapper.
  - Pedir todos los permisos (incluidos descuentos) de una vez.
- **v4.1 (tercer clon, clon idéntico):**
  - Foto por variante y stock por ubicación (`build_productset.py --location`); `compare.py` ahora revisa también fotos de variantes, stock, vendor, tipo, etiquetas y descripción.
  - `sync_menus.py` reasigna ítems de políticas (`SHOP_POLICY`).
  - AVIF → PNG en Files; app embeds descartados hasta instalar las apps.
  - Comparar el texto visible con la vista previa (cookies) y revisar mercados.
  - Permisos `read_locations` y `read_markets`.
  - `< /dev/null` en los comandos del CLI.

---

## Casos (resumidos, sin datos de los negocios)

### Caso 1: tienda de cartas coleccionables
- Unos 490 productos con 1.500 variantes, 670 metacampos de texto y fecha, 175 colecciones (4 automáticas por metacampo), 10 páginas y 4 menús. Sin videos.
- **Problemas:**
  - El destino ya tenía casi todo cargado por Matrixify.
  - El destino estaba en **PYG**: Shopify redondeó unos 1.500 precios.
  - 1 producto falló por una imagen 502.
  - 3 colecciones automáticas no se crearon porque faltaban las definiciones de metacampos.
- Se resolvió todo por CLI, la comparación final dio 0 diferencias y se publicó.

### Caso 2: tienda de cosmética coreana (con cambio de marca)
- Unos 140 productos con 220 variantes, 1.600 fotos, 430 metacampos (114 `list.file_reference` → 432 imágenes de detalle y "cómo usar"), 70 colecciones manuales, 6 páginas, 7 menús, 60 videos y 37 imágenes en el tema.
- **Problemas:**
  - Los archivos locales que dio el usuario eran de **otra tienda** y estaban viejos.
  - Ese Matrixify viejo se importó en el destino: fallaron todos los productos (ubicación de inventario) y quedaron 3 descuentos y páginas de la marca vieja.
  - 9 imágenes del tema no existían ni en el origen (7 se recuperaron de la tienda madre).
  - Hubo que adaptar todo a la marca nueva: 6 políticas desde un PDF, páginas, footer, ficha de producto, logo y favicon (SVG → PNG), una página de reclamos con su menú en el footer y el nombre del tema.
- **Pendientes del usuario:** desactivar descuentos viejos y cambiar el nombre de la tienda.

---

### Caso 3: tienda de calzado (clon idéntico)
- Origen en GBP → destino recién creado en otra moneda (se cambió a GBP antes de cargar productos).
- 2 productos (uno con 6 colores × 9 talles, una foto por color y stock por variante), 1 colección, 2 páginas, 2 menús, 6 políticas, ~180 imágenes. Sin metacampos ni videos. Dos apps con app embeds en el tema.
- **Problemas:** faltaba la foto de cada variante en la consulta, una imagen AVIF quedó como PNG, el footer falló por el ítem de la política de privacidad y faltaba el permiso `read_markets`.
- La comparación dio NINGUNA en la primera pasada. Quedó para el usuario: nombre de la tienda, mercados, instalar las apps y publicar.

## Estructura del repo
```
README.md                     este manual
plantilla-datos-tienda.md     ficha para completar con los datos de cada clon
queries/                      consultas GraphQL (bulk y normales)
scripts/
  xlsx2json.py                leer el Import Result de Matrixify (sin dependencias)
  classify_files.py           qué archivos de Files subir (y cuáles no)
  upload_images.py            subir imágenes por URL (fileCreate) + mapa de IDs
  upload_videos.py            subir videos o imágenes locales (staged upload)
  build_productset.py         productos del origen → productSet (con --map para file_reference)
  sync_collections.py         colecciones: crear faltantes y dejar los mismos productos en el mismo orden
  sync_menus.py               menús con resourceId reasignado por handle
  build_prices.py             corregir precios que difieren
  compare.py                  comparación completa origen vs destino (objetivo: NINGUNA)
  edit_theme_json.py          editar JSON del tema preservando el comentario de Shopify
  capturar-link-auth.sh       obtener el link de `shopify store auth`
```
