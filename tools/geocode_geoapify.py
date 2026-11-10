#!/usr/bin/env python3
"""Secondo passaggio di geocodifica con Geoapify per le sedi che Nominatim non ha trovato (valori null in data/geocode.json).
La chiave si legge dalla variabile d'ambiente GEOAPIFY_KEY (non va scritta nei file).
Uso: GEOAPIFY_KEY=xxxx python3 geocode_geoapify.py [--prova N]     (--prova N: solo le prime N sedi, senza salvare)
Attribuzione richiesta: © Geoapify, © OpenStreetMap contributors."""
import sys,os,json,re,time,urllib.request,urllib.parse,collections
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from common import *
KEY=os.environ.get('GEOAPIFY_KEY')
if not KEY:sys.exit('Imposta la variabile GEOAPIFY_KEY (chiave gratuita da myprojects.geoapify.com)')
prova=int(sys.argv[sys.argv.index('--prova')+1]) if '--prova' in sys.argv else 0
CACHE=f'{HERE}/data/geocode.json';cache=json.load(open(CACHE))
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
rows=[r for n in ('intesa','bper','mps') for r in read_csv(f'{HERE}/data/csv/{n}.csv')]
todo=[r for r in rows if rkey(r) in cache and cache[rkey(r)] is None]
if prova:todo=todo[:prova]
print('da riprovare:',len(todo),flush=True)
def clean(a):
    a=re.sub(r'\b(ANG|SNC|KM)\b.*$','',a.upper()).strip(' ,');return a.title()
def ok(res,r):
    c=cname(r["CITTA'"]);names=[norm(res.get(k,'')) for k in ('city','town','village','municipality','suburb','county')]
    near=any(n and (n==c or n in c or c in n) for n in names) or (res.get('postcode') or '')[:5]==r['CAP']
    conf=(res.get('rank') or {}).get('confidence',0)
    return near and conf>=0.6 and res.get('result_type') in ('building','amenity','street','postcode','suburb','locality','city')
st=collections.Counter()
t0=time.time()
def barra(i):
    n=len(todo);done=i+1;w=30;fill=int(w*done/n);el=time.time()-t0;eta=el/done*(n-done)
    sys.stdout.write(f"\r[{'#'*fill}{'.'*(w-fill)}] {done}/{n} ({100*done//n}%)  esatte {st['esatta']}  non trovate {st['non trovata']+st['scartata']}  restano ~{int(eta//60)}m{int(eta%60):02d}s   ");sys.stdout.flush()
for i,r in enumerate(todo):
    citta=r["CITTA'"].title();q=clean(r["INDIRIZZO"])+', '+r["CAP"]+' '+citta+', Italia'
    u='https://api.geoapify.com/v1/geocode/search?'+urllib.parse.urlencode({'text':q,'filter':'countrycode:it','format':'json','limit':1,'lang':'it','apiKey':KEY})
    try:d=json.load(urllib.request.urlopen(u,timeout=30)).get('results',[])
    except Exception as e:
        print('errore',e);st['errore']+=1
        if st['errore']>5:sys.exit('troppi errori: controllo la chiave/quota')
        time.sleep(2);continue
    g=d[0] if d else None
    if g and ok(g,r):
        precise=g.get('result_type') in ('building','amenity') or (g.get('rank') or {}).get('match_type') in ('full_match','match_by_building','match_by_street')
        val=[g['lat'],g['lon'],'geoapify' if precise else 'city'] if precise else None
        st['esatta' if val else 'scartata']+=1
        if not prova:cache[rkey(r)]=val
    else:st['non trovata']+=1
    if prova:print(q,'->',(g or {}).get('result_type'),(g or {}).get('rank'),g and (g['lat'],g['lon']))
    if not prova:
        barra(i)
        if i%25==0:json.dump(cache,open(CACHE,'w'))
    time.sleep(0.25)
if not prova:json.dump(cache,open(CACHE,'w'))
print('\nFATTO',dict(st),'- risultati salvati in data/geocode.json' if not prova else '(prova: nulla salvato)')
