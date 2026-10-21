---
name: shopify-recrear-estilo
description: Crea una tienda Shopify de EBOOKS / productos digitales desde cero copiando el ESTILO de una tienda de referencia SIN acceso a su admin (o con el estilo por defecto "Paper Studio"), con el tema de los ebooks según el RUBRO de la LLC del usuario, políticas en inglés con los datos de la LLC, imágenes generadas con Nano Banana / API de Gemini de Google (portadas, hero, logo; Higgsfield como alternativa), mercados UK (GBP) y USA (USD), 6 ebooks de 19.99 a 199 y descuento del 15%. Usar cuando el usuario pida "crear/armar una tienda de ebooks", "recrear el estilo de esta tienda", "quiero una tienda igual a esta" (sin acceso), pase datos de una LLC o su rubro para armar una tienda, mencione Nano Banana o Higgsfield para las imágenes de una tienda, o use el prompt maestro de tiendas de ebooks UK + USA. Es el "modo B". Si SÍ hay acceso al admin de la tienda a copiar, usar shopify-clonar-cli (modo A).
---

# Recrear estilo + tienda de ebooks (modo B: sin acceso a la referencia)

Manual completo con comandos y tabla de errores: `references/manual.md` (leer la sección de cada fase).
Ficha para el usuario: `references/ficha-llc-ebooks.md`. Molde de datos: `references/ejemplo-marca.json`.
Estilo por defecto: `references/estilo-referencia.md`. Prompts de imágenes: `references/prompts-imagenes.md`.
Plantillas: `plantillas/tema/sections/eb-*.liquid` y `plantillas/politicas/*.html`. Scripts: `scripts/` (`python3 -I`).

## Contexto del usuario
- Español rioplatense, no técnico: explicar simple, en tablas, con links y códigos exactos. **Todo lo que ve el cliente, en inglés.**
- Si existe `~/Documents/Shopify-Clones/`: trabajar en `clientes/<tienda>/` (FICHA.md, `datos/marca.json`, `referencia/`, `tema/`, `politicas/`, `imagenes/`). Al terminar, actualizar FICHA y los dos repos del manual (`modo-b/`).

## Cuándo es esta skill
- Siempre que se cree una tienda **a partir de una referencia sin acceso** o **con estilo sugerido**: el resultado es SIEMPRE una tienda de **ebooks / productos digitales**.
- El **rubro de la LLC** define el tema de los ebooks, las imágenes y los textos. Los **datos de la LLC** van en footer, contacto y las 5 políticas.

## Flujo (orden fijo)
1. **Ficha** (manual §1): pedir en UN mensaje lo que falte: LLC (nombre legal, estado, dirección, email, teléfono, horario, **rubro**), `.myshopify.com`, nombre comercial, código de descuento (si no: NOMBRE15), referencia opcional. Proponer **3 nichos** según el rubro y esperar elección. Nunca inventar un teléfono (si falta: `xxx xx xxx`).
2. **Referencia** (§2): `analizar_referencia.py URL clientes/<t>/referencia` + capturas en compu y celular. Sin referencia → `estilo-referencia.md`. Resumir qué se toma y qué NO (textos, imágenes, LLC de la referencia).
3. **Destino** (§3): login CLI + `store auth` con TODOS los scopes (incluye markets, legal_policies, discounts, locales). Confirmar dominio. Mercados UK (GBP) y USA (USD) con tasa manual 1.0 sin redondeo; si da `MULTIPLE_CURRENCIES_NOT_SUPPORTED` → Shopify Payments (lo activa el usuario) o plan B.
4. **Contenido** (§4): 6 ebooks, precios **19.99 · 29.99 · 49.99 · 69.99 · 99.99 · 199.00** según profundidad; el de 199 es la colección completa (tags `bestseller`, `top`). Descripciones con What's inside / Format / disclaimer / "Digital product only". Mostrar tabla al usuario.
5. **Imágenes** (§5): completar `objetos`, `objetos_hero`, `icono`, `subtitulo` en marca.json → `generar_imagenes.py marca.json imagenes/ --prueba` (cantidad y costo, ~US$ 1,20) → OK del usuario → generar → **revisar cada imagen con zoom** (título exacto) → elegir logo → `upload_videos.py TIENDA imagenes/ imagenes/subidas.json IMAGE`. Si no hay key, frenar y explicar cómo crearla (abajo).
6. **Productos y descuento** (§6): `armar_productos.py marca.json productset.jsonl --portadas imagenes/subidas.json` → bulk `productSet` → publicar en Online Store → descuento 15 % sin fin.
7. **Tema** (§7): `theme duplicate` del main (Horizon) → `theme pull` → `armar_tema.py marca.json tema/` → `theme check` → push **primero `sections/eb-*.liquid`, después los 4 JSON**. Nunca editar el tema publicado.
8. **Inglés, menús, páginas** (§8) y **políticas** (§9): `generar_politicas.py marca.json politicas/` → `shopPolicyUpdate` ×5 (o `politicas-para-copiar.html` al usuario).
9. **Verificación** (§10): API (productos, precios GB/US iguales, imágenes READY, políticas, descuento) + capturas lado a lado con la referencia + links 200, sin español ni datos de la referencia.
10. **Entrega** (§11): tabla de productos £/$, link de vista previa, pendientes del usuario (Payments, idioma, nombre, **PDF con Digital Downloads**, OK para publicar).

## Imágenes: API de Google (por defecto) o Higgsfield
- **Google (Nano Banana Pro, `gemini-3-pro-image`, 2K):** ~US$ 0,134 por imagen, sin suscripción. El usuario crea la key en `https://aistudio.google.com/apikey`, activa la **facturación** (no hay uso gratis para Pro) y la guarda en `~/.config/gemini/api_key` con el comando del manual §5. **Nunca pedir la key por chat ni guardarla en un repo.** Probar con `generar_imagenes.py --listar`.
- **Higgsfield** (solo si ya paga el plan): Configuración → Conectores → Agregar conector personalizado → `https://mcp.higgsfield.ai/mcp`. Mismos prompts, tandas de máx. 6, URLs directo a Shopify.
- La tienda **no lleva videos** (la referencia no tiene). Si algún día hacen falta (anuncios), la misma key de Google da acceso a Veo.

## Reglas que evitan errores ya vividos
- Reutilizar del modo A: acceso y scopes (`capturar-link-auth.sh`), `edit_theme_json.py`, `upload_videos.py ... IMAGE`, publicar (§8 del manual A).
- Comandos CLI con `< /dev/null`. Autorizaciones de a una. Nada irreversible ni público sin OK (publicar tema, quitar contraseña, borrar).
- Prometer solo lo concreto: nada de "may cover"/"proposed"/páginas inventadas (`armar_productos.py` lo frena).
- Nunca dejar nombre, LLC, email o teléfono de la tienda de referencia.
- No se puede por API: nombre de la tienda, idioma predeterminado, activar Shopify Payments, subir PDF a Digital Downloads. Los hace el usuario.
