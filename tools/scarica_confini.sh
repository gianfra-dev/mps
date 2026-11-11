#!/bin/sh
# Scarica i confini comunali/provinciali (ISTAT via openpolis/geojson-italy) nella cartella indicata (default ./confini).
# Uso: sh scarica_confini.sh [cartella]   poi: python3 build.py <cartella>
D=${1:-confini}; mkdir -p "$D/g"; B=https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson
curl -sL -o "$D/prov.geojson" $B/limits_IT_provinces.geojson
for i in $(seq 1 20); do curl -sL -o "$D/g/com$i.geojson" $B/limits_R_${i}_municipalities.geojson; done
