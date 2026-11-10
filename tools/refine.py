#!/usr/bin/env python3
"""Passo di affinamento delle coordinate: per i comuni dove una banca ha UNA sola sede non ancora localizzata
e nel locator/OpenStreetMap c'è UN solo punto non usato dentro quel comune, assegna quel punto.
Uso: python3 refine.py <cartella_dati> <cartella_api>   (dati = confini g/com*.geojson; api = isp_raw.json, mps_raw.json, osm_bper.json)"""
import sys,os,json,re,collections
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from common import *
DATA,API=sys.argv[1],sys.argv[2]
CACHE=f'{HERE}/data/geocode.json';cache=json.load(open(CACHE))
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
def pip(x,y,ring):
    ins=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:ins=not ins
        j=i
    return ins
com=[]
for i in range(1,21):
    for f in json.load(open(f'{DATA}/g/com{i}.geojson'))['features']:
        g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        xs=[p[0] for q in polys for p in q[0]];ys=[p[1] for q in polys for p in q[0]]
        com.append((norm(f['properties']['name']),(min(xs),min(ys),max(xs),max(ys)),polys))
def where(lat,lon):
    for n,bb,polys in com:
        if bb[0]<=lon<=bb[2] and bb[1]<=lat<=bb[3] and any(pip(lon,lat,p[0]) and not any(pip(lon,lat,h) for h in p[1:]) for p in polys):return n
cand={'intesa':[(x['latitudine'],x['longitudine'],x['indirizzo']) for x in json.load(open(f'{API}/isp_raw.json')) if x['abi']=='03069'],
      'mps':[(x['latitudine'],x['longitudine'],x['indirizzo']) for x in json.load(open(f'{API}/mps_raw.json'))],
      'bper':[(e.get('lat') or e['center']['lat'],e.get('lon') or e['center']['lon'],((e['tags'].get('addr:street') or '')+' '+(e['tags'].get('addr:housenumber') or '')).strip()) for e in json.load(open(f'{API}/osm_bper.json'))['elements']]}
tot=collections.Counter()
for n in ('intesa','bper','mps'):
    rows=[r for r in read_csv(f'{HERE}/data/csv/{n}.csv') if not cache.get(rkey(r))]
    used={(round(v[0],5),round(v[1],5)) for k,v in cache.items() if v and v[2] in('bank','bank1','osm') and k.startswith({'intesa':'3069','bper':'5387','mps':'1030'}[n]+'|')}
    pts=collections.defaultdict(list)
    for la,lo,ad in cand[n]:
        if (round(la,5),round(lo,5)) in used:continue
        w=where(la,lo)
        if w:pts[w].append((la,lo,ad))
    grp=collections.defaultdict(list)
    for r in rows:grp[cname(r["CITTA'"])].append(r)
    for c,rs in grp.items():
        P=pts.get(c,[])
        if len(rs)==1 and len(P)==1:
            cache[rkey(rs[0])]=[P[0][0],P[0][1],'osm' if n=='bper' else 'bank1'];tot[n]+=1
        elif len(rs)>1 and P:   # più sedi: assegna solo se la via coincide
            for r in rs:
                m=[p for p in P if p[2] and akey(p[2])[:8]==akey(r['INDIRIZZO'])[:8]]
                if len(m)==1:cache[rkey(r)]=[m[0][0],m[0][1],'osm' if n=='bper' else 'bank1'];tot[n]+=1;P.remove(m[0])
json.dump(cache,open(CACHE,'w'));print('affinati',dict(tot),'totale in cache',sum(1 for v in cache.values() if v))
