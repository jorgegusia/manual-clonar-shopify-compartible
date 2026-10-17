# Ficha: tienda de ebooks (modo B)

> Completá lo que tengas y pasásela a Claude. Lo que falte te lo pregunta en UN solo mensaje.
> **No escribas contraseñas ni datos de tarjeta acá.**

## 1. La LLC (va en el footer, las políticas y el contacto)
- **Nombre legal exacto:** `[EJEMPLO COMMERCE LLC]`
- **Estado donde está registrada:** `[New Mexico]`
- **Dirección completa** (la de la LLC o del agente registrado): `[123 Example St, Suite 100, Springfield, NM 87500, USA]`
- **Email de soporte:** `[support@tudominio.com]`
- **Teléfono:** `[+1 000 000 0000]` (si no hay, va "xxx xx xxx" y lo cambiás después)
- **Horario de atención:** `[Monday to Friday, 9:00 am to 5:00 pm (ET)]`
- **Rubro / actividad de la LLC** (como figura en sus papeles o en Stripe/Shopify Payments): `[Digital marketing consulting]`
  - **De acá sale el tema de los ebooks**, las imágenes y los textos. Así la tienda es coherente con la LLC.

## 2. La tienda
- **Dirección .myshopify.com:** `[mi-tienda.myshopify.com]` (en la URL del admin: `admin.shopify.com/store/ESTE-NOMBRE`)
- **Nombre comercial** (si no tenés, Claude propone 3): `[...]`
- **Dominio propio** (opcional): `[...]`
- **Código de descuento** (si no, se usa NOMBRE15): `[...]`

## 3. Estilo
- **Tienda de referencia** (opcional). Si no ponés nada se usa el estilo por defecto "Paper Studio"
  (`estilo-referencia.md`): `[https://...]`
- **Colores** (opcional; si no, la paleta de la referencia o una propuesta según el rubro): `[...]`

## 4. Lo que decide Claude (te avisa qué eligió)
- Tema de los 6 ebooks según el rubro (te propone 3 opciones de nicho y elegís una).
- Títulos, descripciones, precios (escalera de 19.99 a 199) y cuál es el producto top.
- Imágenes con Nano Banana (API de Google, ~US$ 2 por tienda): 6 portadas, 1 hero y 2 logos.

## 5. Lo que hacés vos (no se puede por API)
- [ ] Una sola vez: API key de Google con facturación activa, guardada en tu Mac (manual §5).
- [ ] Shopify Payments activo y moneda de la tienda en USD (para tener £ y $).
- [ ] Configuración → Idiomas: inglés como idioma predeterminado.
- [ ] Configuración → Detalles de la tienda: nombre correcto.
- [ ] Subir los PDF de cada ebook con la app **Shopify Digital Downloads** (sin PDF no se puede vender).
- [ ] Revisar la vista previa y dar el OK para publicar el tema y quitar la contraseña.
