# Filiali Intesa Sanpaolo, BPER e Monte dei Paschi di Siena per regione

Sito statico (GitHub Pages): `index.html` è la pagina d'accesso con la mappa d'Italia; ogni regione ha la sua mappa in `<regione>/index.html`.

## Fonti
- **Elenco sportelli**: Banca d'Italia (succursali in Italia attive), file in `tools/data/csv/` aggiornati al 10/11/2026.
- **Posizioni sulla mappa**: i CSV non hanno coordinate. Sono state ricavate abbinando gli indirizzi ai locator pubblici di Intesa Sanpaolo e MPS e a OpenStreetMap (`tools/data/geocode.json`). Le sedi senza posizione esatta sono mostrate al centro del comune con cerchio tratteggiato e non entrano nelle linee di prossimità.
- Confini comunali/provinciali ISTAT da openpolis/geojson-italy.

## Pubblicare
Settings → Pages → *Deploy from a branch* → `main` / `(root)`. I link sono relativi.

## Aggiornare / completare le posizioni
```
python3 tools/geocode.py     # riprende la geocodifica (Nominatim, ~1 richiesta/s) delle sedi senza coordinate
GEOAPIFY_KEY=... python3 tools/geocode_geoapify.py   # facoltativo: riprova con Geoapify le sedi non trovate (attribuzione: © Geoapify, © OpenStreetMap contributors)
python3 tools/build.py <cartella_confini>   # rigenera le pagine (serve prov.geojson e g/com1..20.geojson)
```
