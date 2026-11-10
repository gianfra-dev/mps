# Filiali Intesa Sanpaolo, BPER e Monte dei Paschi di Siena per regione

Sito statico (GitHub Pages): `index.html` è la pagina d'accesso con la mappa d'Italia; ogni regione ha la sua mappa in `<regione>/index.html`.

## Fonti
- **Intesa Sanpaolo** e **MPS**: API pubbliche dei locator ufficiali (`tools/crawl.py`).
- **BPER**: il locator ufficiale è protetto da reCAPTCHA; i dati vengono da OpenStreetMap (Overpass) e l'elenco è incompleto.
- Confini comunali/provinciali ISTAT da openpolis/geojson-italy.

## Pubblicare
Settings → Pages → *Deploy from a branch* → `main` / `(root)`. I link sono relativi.

## Rigenerare
```
python3 tools/crawl.py isp dati && python3 tools/crawl.py mps dati
python3 tools/build.py dati
```
(servono anche `osm_bper.json`, `prov.geojson` e `g/com1..20.geojson` nella cartella dati)
