---
name: shopify-clonar-cli
description: Clona una tienda Shopify COMPLETA de una tienda de origen a una de destino usando Shopify CLI (tema, imágenes y videos del tema, productos con metacampos, colecciones, páginas, menús, políticas), verifica en loop hasta que no haya diferencias y la adapta a una marca nueva (logo, favicon, políticas, textos legales). Usar cuando el usuario pida clonar, duplicar, copiar o migrar una tienda Shopify a otra cuenta o tienda TENIENDO acceso al admin de la tienda de origen, cuando pase dominios .myshopify.com de origen y destino, cuando mencione Matrixify o un Import_Result, o cuando quiera re-sincronizar productos, precios, colecciones o menús entre dos tiendas. Es el "modo A" (con acceso). Si NO hay acceso al origen y solo se quiere copiar el estilo de una tienda de referencia, eso es otra skill (shopify-recrear-estilo).
---

# Clonar tienda Shopify por CLI (modo A: con acceso al origen)

Manual completo con comandos, tabla de errores reales y casos: `references/manual.md` (leer la sección que corresponda a cada fase).
Herramientas: `scripts/*.py` (correr con `python3 -I`) y `queries/*.graphql`, en la carpeta de esta skill.
Ficha de datos para completar con el usuario: `references/plantilla-datos-tienda.md`.

## Contexto del usuario
- Habla español rioplatense y no es técnico: explicar simple, en tablas, con **links y códigos exactos** cuando tenga que aprobar algo.
- Si existe `~/Documents/Shopify-Clones/`, trabajar ahí: `clientes/<nombre>/` con `FICHA.md` (copiar la plantilla). Leer su `CLAUDE.md`. Al terminar, actualizar la FICHA y los repos del manual (privado y compartible).

## Flujo (orden fijo)
1. **Datos:** completar la ficha (origen, destino, moneda, marca nueva, empresa, email, logos, políticas). Si el usuario pasa archivos locales (Matrixify, zips de tema, CSV), **verificar de qué tienda y fecha son** antes de usarlos.
2. **Origen: acceso.** `shopify auth logout && shopify theme list --store ORIGEN` (login en una pestaña de Terminal visible) + `shopify store auth` con scopes de lectura (manual §2).
3. **Origen: descarga y análisis.**
   - `theme pull` del tema publicado.
   - Imágenes y videos del tema (`shopify://shop_images`, `shopify://files/videos`).
   - Bulk export de productos, colecciones y Files (`queries/`), páginas, menús y datos de la tienda.
   - Reportar en una tabla: cantidades, moneda, metacampos `file_reference`, videos, faltantes (manual §3).
4. **Destino: acceso y chequeos.**
   - Login + `store auth` con **todos** los scopes de una vez, incluidos los de descuentos.
   - Moneda igual a la del origen **antes** de importar.
   - Exportar el destino y `compare.py`.
   - Leer el Import Result de Matrixify si lo hay, con `xlsx2json.py` (manual §4).
5. **Destino: subida** (manual §5), en este orden:
   1. Tema `--unpublished`.
   2. Definiciones de metacampos.
   3. Archivos: `classify_files.py` → `upload_images.py` (genera `mapa-archivos.json`) → `upload_videos.py`.
   4. Re-push de `templates/index.json` cuando los videos estén READY.
   5. Productos: `build_productset.py --map` + bulk productSet + publicar.
   6. `sync_collections.py`.
   7. Páginas.
   8. `sync_menus.py`.
   9. Políticas.
6. **Loop de verificación:** re-exportar el destino y `compare.py ... mapa-archivos.json` hasta que diga **NINGUNA**. Precios con `build_prices.py`. Revisar canales y tienda en vivo (manual §6).
7. **Adaptación a la marca nueva** (manual §7):
   - Buscar texto visible viejo en el HTML en vivo.
   - Revisar header, footer (bloques), `product.json`, páginas y las 6 políticas (desde el PDF del usuario).
   - Logo y favicon: SVG → PNG con `sips` y subida con `upload_videos.py ... IMAGE`.
   - Nombre del tema. Editar JSON del tema con `edit_theme_json.py`.
8. **Publicar solo con OK explícito:** `shopify theme publish --theme ID --force` y verificar en vivo.

## Reglas que evitan los errores ya vividos
- **Nunca crear a ciegas:** comparar primero. Una diferencia en el destino puede venir de una importación vieja de otra tienda, no de una edición a mano: averiguar el origen antes de pisarla o respetarla.
- Comandos del CLI desde Bash con `< /dev/null`. En macOS no hay `timeout`. En zsh, no iterar sobre variables con varios IDs.
- `store auth` no imprime el link: si el usuario no lo ve o se vence, usar `scripts/capturar-link-auth.sh` y pasarle el link. Autorizaciones **de a una**, avisando que vencen en minutos.
- Errores 401 en `theme ...` después de re-autorizar: `shopify auth logout` + login.
- Videos: nunca `fileCreate` con URL. Siempre staged upload.
- Metacampos `file_reference`: siempre reapuntar con el mapa de IDs.
- Productos con una foto por color: exportar con `q_prod.graphql` (trae `image { url }` de cada variante) y armar con `build_productset.py --location <ubicación destino>` para copiar también el stock.
- App embeds de apps que el destino no tiene se descartan en el push: re-subir `config/settings_data.json` cuando el usuario instale las apps.
- Nada irreversible ni público sin OK: publicar, borrar o desactivar descuentos, quitar la contraseña. Si el clasificador de permisos lo bloquea, **no forzarlo**: guiar al usuario en el admin.
- No se puede por API: nombre de la tienda, gestión automática de la política de privacidad. Los hace el usuario.
- Tabla completa de errores y soluciones: `references/manual.md` §9.

## Modo C (híbrido), para cuando exista la skill de estilo
Si el usuario tiene acceso a una tienda (estructura y datos) pero quiere el **estilo** de otra sin acceso: esta skill aporta los pasos 2–6 (datos, productos, colecciones, archivos) y `shopify-recrear-estilo` aporta el diseño y las imágenes generadas. La skill `shopify-tienda-maestro` decide y coordina.
