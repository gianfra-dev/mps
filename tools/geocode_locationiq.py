#!/usr/bin/env python3
"""Passaggio di geocodifica con LocationIQ per le sedi ancora approssimative (valori null in data/geocode.json
e sedi elencate in data/approssimate.json, create da build.py).
Chiave dalla variabile d'ambiente LOCATIONIQ_KEY (non va scritta nei file).
Uso: LOCATIONIQ_KEY=xxxx python3 geocode_locationiq.py [--prova N]    (--prova N: solo le prime N sedi, senza salvare)
Attribuzione richiesta da LocationIQ: «Search by LocationIQ.com» con link a https://locationiq.com"""
import sys,os,json,re,time,urllib.request,urllib.parse,collections
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from common import *
KEY=os.environ.get('LOCATIONIQ_KEY')
if not KEY:sys.exit('Imposta la variabile LOCATIONIQ_KEY (chiave gratuita da my.locationiq.com)')
BASE=os.environ.get('LOCATIONIQ_URL','https://eu1.locationiq.com/v1/search')
prova=int(sys.argv[sys.argv.index('--prova')+1]) if '--prova' in sys.argv else 0
CACHE=f'{HERE}/data/geocode.json';cache=json.load(open(CACHE))
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
appr=set(json.load(open(f'{HERE}/data/approssimate.json'))) if os.path.exists(f'{HERE}/data/approssimate.json') else set()
rows=[r for n in ('intesa','bper','mps') for r in read_csv(f'{HERE}/data/csv/{n}.csv')]
todo=[r for r in rows if rkey(r) in appr or cache.get(rkey(r)) is None]
if prova:todo=todo[:prova]
print('sedi da riprovare:',len(todo),flush=True)
def clean(a):
    a=re.sub(r'\b(ANG|SNC|KM)\b.*$','',a.upper()).strip(' ,');return a.title()
def ok(g,r):
    ad=g.get('address') or {};c=cname(r["CITTA'"])
    names=[norm(ad.get(k,'')) for k in ('city','town','village','municipality','suburb','hamlet','county')]
    near=any(n and (n==c or n in c or c in n) for n in names) or (ad.get('postcode') or '')[:5]==r['CAP']
    mt=((g.get('matchquality') or {}).get('matchtype') or '').lower()
    return near and mt in ('building','street','point','house')
st=collections.Counter();t0=time.time()
def barra(i):
    n=len(todo);done=i+1;w=30;fill=int(w*done/n);el=time.time()-t0;eta=el/done*(n-done)
    sys.stdout.write(f"\r[{'#'*fill}{'.'*(w-fill)}] {done}/{n} ({100*done//n}%)  trovate {st['esatta']}  non trovate {st['non trovata']}  restano ~{int(eta//60)}m{int(eta%60):02d}s   ");sys.stdout.flush()
for i,r in enumerate(todo):
    citta=r["CITTA'"].title();q=clean(r['INDIRIZZO'])+', '+r['CAP']+' '+citta+', Italia'
    u=BASE+'?'+urllib.parse.urlencode({'key':KEY,'q':q,'format':'json','limit':1,'countrycodes':'it','addressdetails':1,'matchquality':1,'accept-language':'it'})
    d=[]
    for tent in range(3):
        try:d=json.load(urllib.request.urlopen(u,timeout=30));break
        except urllib.error.HTTPError as e:
            if e.code==404:d=[];break          # nessun risultato
            if e.code==429:time.sleep(3);continue   # troppe richieste: attendo
            if e.code in (401,403):sys.exit(f'\nchiave non valida o quota esaurita (HTTP {e.code})')
            st['errore']+=1;time.sleep(2)
        except Exception:st['errore']+=1;time.sleep(2)
    g=d[0] if isinstance(d,list) and d else None
    if g and ok(g,r):
        st['esatta']+=1
        if not prova:cache[rkey(r)]=[float(g['lat']),float(g['lon']),'locationiq']
    else:st['non trovata']+=1
    if prova:print(q,'->',g and ((g.get('matchquality') or {}).get('matchtype'),g['lat'],g['lon']),'ACCETTATA' if g and ok(g,r) else 'scartata')
    else:
        barra(i)
        if i%25==0:json.dump(cache,open(CACHE,'w'))
    time.sleep(0.55)   # il piano gratuito ammette 2 richieste/secondo
if not prova:json.dump(cache,open(CACHE,'w'))
print('\nFATTO',dict(st),'- risultati salvati in data/geocode.json' if not prova else '(prova: nulla salvato)')
