#!/bin/sh
# `shopify store auth` NO imprime el link de autorización: lo abre directo en el navegador.
# Si el usuario no lo ve o se le venció, este wrapper captura el link (y lo abre igual).
# Uso:
#   sh capturar-link-auth.sh TIENDA.myshopify.com read_products,write_products,...
#   cat /tmp/opened-urls.log      # el link para pasarle al usuario
# El usuario tiene que aprobarlo en la MISMA computadora (el callback vuelve a 127.0.0.1) y rápido:
# si tarda unos minutos da "Timed out waiting for OAuth callback".
set -e
STORE="$1"; SCOPES="$2"
DIR=$(mktemp -d)
cat > "$DIR/open" <<'EOF'
#!/bin/sh
echo "$@" >> /tmp/opened-urls.log
exec /usr/bin/open "$@"
EOF
chmod +x "$DIR/open"
rm -f /tmp/opened-urls.log
PATH="$DIR:$PATH" shopify store auth --store "$STORE" --scopes "$SCOPES"
