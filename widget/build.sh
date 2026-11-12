#!/bin/sh
# Arma el ZIP que se sube a Kommo, con tu dominio dentro de script.js.
#   ./build.sh https://widget.tudominio.com
set -e
API="${1:?Uso: ./build.sh https://widget.tudominio.com}"
cd "$(dirname "$0")"
TMP=$(mktemp -d)
cp -R manifest.json script.js i18n images "$TMP/"
sed -i.bak "s#https://widget.tudominio.com#${API}#g" "$TMP/script.js" "$TMP/manifest.json" && rm -f "$TMP"/*.bak
( cd "$TMP" && COPYFILE_DISABLE=1 zip -qr widget.zip manifest.json script.js i18n images )
mv "$TMP/widget.zip" ./widget.zip && rm -rf "$TMP"
echo "listo: widget/widget.zip (API = $API)"
