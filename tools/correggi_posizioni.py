#!/usr/bin/env python3
"""Correzione manuale delle sedi con posizione approssimativa.
  python3 correggi_posizioni.py esporta   -> crea data/da_correggere.csv (una riga per sede, con link di ricerca su OpenStreetMap)
  (compila lat e lon nel CSV: da Excel/Numbers, separatore ';', decimali con punto o virgola)
  python3 correggi_posizioni.py importa   -> inserisce le coordinate compilate in data/geocode.json (precisione 'manuale')
Poi rigenera le pagine con build.py."""
import sys,os,json,csv,urllib.parse
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from common import *
CACHE=f'{HERE}/data/geocode.json';OUT=f'{HERE}/data/da_correggere.csv'
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
NOMI={'intesa':'Intesa Sanpaolo','bper':'BPER Banca','mps':'Monte dei Paschi'}
cache=json.load(open(CACHE))
if len(sys.argv)<2 or sys.argv[1] not in('esporta','importa'):sys.exit(__doc__)
if sys.argv[1]=='esporta':
    appr=set(json.load(open(f'{HERE}/data/approssimate.json'))) if os.path.exists(f'{HERE}/data/approssimate.json') else set()
    n=0
    with open(OUT,'w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['banca','codice_sede','indirizzo','cap','citta','lat','lon','cerca_su_openstreetmap','chiave'])
        for b in('intesa','bper','mps'):
            for r in read_csv(f'{HERE}/data/csv/{b}.csv'):
                k=rkey(r)
                if cache.get(k) and k not in appr:continue
                citta=r["CITTA'"];q=r['INDIRIZZO']+', '+r['CAP']+' '+citta+', Italia'
                w.writerow([NOMI[b],r['CODICE SUCCURSALE'],r['INDIRIZZO'],r['CAP'],r["CITTA'"],'','','https://www.openstreetmap.org/search?query='+urllib.parse.quote(q),k]);n+=1
    print(n,'sedi da correggere ->',OUT)
else:
    n=0;bad=0
    for row in csv.DictReader(open(OUT,encoding='utf-8-sig'),delimiter=';'):
        if not row['lat'].strip() or not row['lon'].strip():continue
        try:la=float(row['lat'].replace(',','.'));lo=float(row['lon'].replace(',','.'))
        except ValueError:bad+=1;print('valori non numerici:',row['banca'],row['indirizzo'],row['citta']);continue
        if not(35<la<48 and 6<lo<19):bad+=1;print('fuori dall\'Italia (lat/lon invertiti?):',row['banca'],row['indirizzo'],row['citta'],la,lo);continue
        cache[row['chiave']]=[la,lo,'manuale'];n+=1
    json.dump(cache,open(CACHE,'w'));print(n,'posizioni importate;',bad,'scartate')
