#!/usr/bin/env python3
"""Assegna coordinate alle filiali dei CSV (Banca d'Italia, senza coordinate).
1) abbina l'indirizzo ai dati dei locator ufficiali (se disponibili, cartella --api);
2) altrimenti geocodifica con Nominatim/OpenStreetMap (1 richiesta/secondo);
Risultato in data/geocode.json: chiave -> [lat, lon, precisione] con precisione bank|addr|city.
Uso: python3 geocode.py [cartella_api_con_isp_raw.json_e_mps_raw.json]"""
import sys,os,json,re,time,urllib.request,urllib.parse,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
HERE=os.path.dirname(os.path.abspath(__file__));CACHE=f'{HERE}/data/geocode.json'
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
rows=[]
for n in ('intesa','bper','mps'):rows+= [(n,r) for r in read_csv(f'{HERE}/data/csv/{n}.csv')]
def num(a):
    m=re.search(r'(\d+)',a or '');return m.group(1) if m else ''
if len(sys.argv)>1:
    api={'intesa':[(x['indirizzo'],x['cap'],x['latitudine'],x['longitudine']) for x in json.load(open(sys.argv[1]+'/isp_raw.json'))],
         'mps':[(x['indirizzo'],x['cap'],x['latitudine'],x['longitudine']) for x in json.load(open(sys.argv[1]+'/mps_raw.json'))]}
    for n,L in api.items():
        ex={};A=collections.defaultdict(list)
        for a,c,la,lo in L:ex.setdefault((akey(a),c),(la,lo));A[(c,num(a))].append((akey(a),la,lo))
        for nn,r in rows:
            if nn!=n or rkey(r) in cache:continue
            k=(akey(r['INDIRIZZO']),r['CAP'])
            if k in ex:cache[rkey(r)]=[*ex[k],'bank'];continue
            mine=akey(r['INDIRIZZO']);ok=[c for c in A.get((r['CAP'],num(r['INDIRIZZO'])),[]) if c[0][:6]==mine[:6] or mine[:6] in c[0] or c[0][:6] in mine]
            if len(ok)==1:cache[rkey(r)]=[ok[0][1],ok[0][2],'bank']
    json.dump(cache,open(CACHE,'w'))
    print('abbinati ai locator:',len(cache),flush=True)
UA='FISAC-mappe-filiali/1.0 (geocodifica una tantum di sportelli bancari)'
def nom(params):
    u='https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode({**params,'format':'jsonv2','limit':1,'countrycodes':'it','addressdetails':1})
    for t in range(3):
        try:
            d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40));time.sleep(1.05);return d
        except Exception:time.sleep(5)
    return []
def valid(d,r):
    """accetta il risultato solo se comune o CAP coincidono con quelli del CSV"""
    if not d:return False
    ad=d[0].get('address',{});c=norm(r["CITTA'"])
    names=[norm(ad.get(k,'')) for k in ('city','town','village','municipality','hamlet','suburb','city_district')]
    return any(n and (n==c or n in c or c in n) for n in names) or ad.get('postcode','')[:5]==r['CAP']
def clean(a):
    a=re.sub(r'\b(ANG|SNC|KM)\b.*$','',a.upper()).strip(' ,');a=re.sub(r'(\d+)\s*[/-]?\s*[A-Z]{0,2}(\b|$)',r'\1',a,count=1);return a.title()
order={'01030':0,'03069':1,'05387':2}
todo=sorted([(n,r) for n,r in rows if rkey(r) not in cache],key=lambda x:order.get(x[1]['CODICE MECCANOGRAFICO INTERMEDIARIO'].zfill(5),3))
print('da geocodificare:',len(todo),flush=True)
for i,(n,r) in enumerate(todo):
    city=r["CITTA'"];st=clean(r['INDIRIZZO'])
    d=nom({'street':st,'postalcode':r['CAP'],'city':city,'country':'Italy'})
    if not valid(d,r):d=nom({'q':f'{st}, {r["CAP"]} {city}, Italia'})
    cache[rkey(r)]=[float(d[0]['lat']),float(d[0]['lon']),'addr'] if valid(d,r) else None
    if i%25==0:json.dump(cache,open(CACHE,'w'));print(i,len(todo),flush=True)
json.dump(cache,open(CACHE,'w'));print('FATTO',collections.Counter((v[2] if v else 'nessuna') for v in cache.values()),flush=True)
