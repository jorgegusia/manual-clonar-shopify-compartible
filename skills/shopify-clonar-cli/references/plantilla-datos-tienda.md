# Ficha del clon (completar y pasársela a Claude)

> Copiá este archivo, reemplazá los ejemplos `entre corchetes` por tus datos y borrá lo que no aplique.
> **No escribas contraseñas acá**: los logins los aprobás vos en el navegador cuando Claude te pase el link.

## 1. Tiendas
- **Tienda de origen** (la que se copia): `[tienda-origen].myshopify.com`
  - Dónde verlo: en la URL del admin, `admin.shopify.com/store/ESTE-NOMBRE`
- **Tienda de destino** (donde se pega): `[tienda-destino].myshopify.com`
- **Dominio público del destino:** `[glowbeauty.com]`
- **¿Las dos tiendas son de la misma cuenta de Shopify?** `[sí / no]`
- **Moneda del origen:** `[GBP]`
- **Moneda del destino:** `[GBP]`
  - Tienen que ser iguales **antes** de importar. Si no, Shopify redondea los precios.

## 2. Marca nueva (para adaptar textos, políticas y footer)
- **Nombre de la marca:** `[Glow Beauty]`
- **Marca vieja a reemplazar** (cómo aparece hoy en la tienda): `[Marca Vieja]`
- **Empresa legal (razón social):** `[EJEMPLO COMMERCE LLC]`
- **Dirección legal:** `[123 Example St, Suite 100, Springfield, NM 87500, USA]`
- **Teléfono:** `[+1 000 000 0000]`
- **Email de soporte:** `[support@glowbeauty.com]`
- **Horario de atención:** `[Lunes a viernes, respuesta en 24–48 h hábiles]`
- **Ley aplicable o jurisdicción** (si las políticas la mencionan): `[State of New Mexico, USA]`

## 3. Archivos (ubicación en tu computadora)
- **Carpeta de trabajo:** `[~/Desktop/clon-glowbeauty]`
- **Logo para fondo claro** (SVG o PNG): `[logo-negro.svg]`
- **Logo para fondo oscuro** (opcional): `[logo-blanco.svg]`
- **Favicon** (cuadrado, SVG o PNG): `[favicon.svg]`
- **Políticas** (PDF o texto): `[Politicas.pdf]`
  - Reembolso, privacidad, términos, envíos, contacto y Legal Notice.
- **Opcionales, solo para comparar:**
  - Matrixify: `[archivo.xlsx]`
  - Zip del tema: `[tema.zip]`
  - CSV de productos: `[productos.csv]`
  - Claude va a verificar de qué tienda y de qué fecha son.

## 4. Decisiones (si no sabés, dejalo en blanco y Claude te pregunta)
- **¿Copiar los descuentos del origen?** `[sí / no]`
- **¿Publicar el tema al terminar?** `[sí, después de revisar la vista previa]`
- **¿Quitar la contraseña de la tienda?** `[lo hago yo]`
- **Páginas extra** a agregar (ej. página de reclamos) y en qué menú van: `[...]`

## 5. Lo que hace el usuario en el admin (no se puede por API)
- [ ] Cambiar el **nombre de la tienda**: Settings → General → Store details.
- [ ] Desactivar la **gestión automática** de la política de privacidad: Settings → Policies.
- [ ] Desactivar o borrar **descuentos** que no correspondan.
- [ ] Revisar pagos, envíos, impuestos, dominio y apps.
