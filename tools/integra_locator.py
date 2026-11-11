#!/usr/bin/env python3
"""Integra le sedi Intesa Sanpaolo e MPS ancora approssimative cercandole nei locator ufficiali delle banche
(interrogando l'area del comune indicato nel CSV della Banca d'Italia) e abbinando l'indirizzo.
Uso: python3 integra_locator.py <cartella_confini> [--prova]      (dopo build.py, che crea data/approssimate.json)
Scrive data/geocode.json (precisione 'bank') e data/non_risolte.json con l'elenco delle sedi non risolte."""
import sys,os,json,re,time,uuid,math,collections,urllib.request
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from common import *
CONF=sys.argv[1];PROVA='--prova' in sys.argv
CACHE=f'{HERE}/data/geocode.json';cache=json.load(open(CACHE));appr=set(json.load(open(f'{HERE}/data/approssimate.json')))
def rkey(r):return '|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']])
cent={}
for i in range(1,21):
    for f in json.load(open(f'{CONF}/g/com{i}.geojson'))['features']:
        g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        xs=[p[0] for q in polys for p in q[0]];ys=[p[1] for q in polys for p in q[0]]
        cent.setdefault(norm(f['properties']['name']),((min(ys)+max(ys))/2,(min(xs)+max(xs))/2,max(max(ys)-min(ys),max(xs)-min(xs))))
TIPI=re.compile(r'^(VIALE|VIA|PIAZZALE|PIAZZA|CORSO|LARGO|STRADA|LOCALITA|VICOLO|CONTRADA|BORGO|LUNGOMARE)')
def strada(a):
    s=akey(a);s=TIPI.sub('',s);return s
def simili(a,b):
    x,y=strada(a),strada(b);return len(x)>=4 and len(y)>=4 and (x[:5]==y[:5] or x in y or y in x)
def num(a):
    m=re.search(r'(\d+)',a or '');return m.group(1) if m else ''
def isp(lat,lon,raggio):
    body=json.dumps({"payload":{"latitudine":lat,"longitudine":lon,"raggio":raggio,"numeroRisultati":500}}).encode()
    q=urllib.request.Request("https://api.intesasanpaolo.com/ib/content/api/app/public/filiale/ricercaFilialiGeoloc",data=body,headers={"X-REQUEST-ID":str(uuid.uuid4()),"applicationName":"VET","channel":"02","x-isp-cypher-drw":"false","CALLER":"ricerca-filiali","Page":"ricerca-filiali.ricerca-filiali","x-isp-cypher":"false","X-BEAR-SESSION-TOKEN":"empty","X-ISP-Session-Id":"empty","Content-Type":"application/json","Accept":"application/json","Origin":"https://www.intesasanpaolo.com","User-Agent":"Mozilla/5.0"})
    L=json.load(urllib.request.urlopen(q,timeout=60)).get('payload',{}).get('listaFilialiGeoloc',[]) or []
    return [dict(lat=x['latitudine'],lon=x['longitudine'],ind=x['indirizzo'],cap=x.get('cap') or '',com=x['comune'],nome=(x.get('datiSoa') or {}).get('descrizioneFiliale','')) for x in L if x['abi']=='03069']
def mps(lat,lon,raggio):
    u=f"https://appx.mps.it/VWRestServices/client/public/filiale/elenco?elemPag=300&ckF=true&ckB=false&pk=1&lat={lat}&lon={lon}&output=json"
    L=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=60)).get('listaFiliali',[]) or []
    return [dict(lat=x['latitudine'],lon=x['longitudine'],ind=x['indirizzo'],cap=x.get('cap') or '',com=x['comune'],nome=(x.get('entitaBanca') or [{}])[0].get('descrizioneFiliale','')) for x in L]
res=collections.defaultdict(list);fetched={}
targets=[(b,fn,r) for b,fn,fetch in (('ISP','intesa',isp),('MPS','mps',mps)) for r in read_csv(f'{HERE}/data/csv/{fn}.csv') if rkey(r) in appr]
used=collections.defaultdict(set)
for b,fn in (('ISP','intesa'),('MPS','mps')):
    for r in read_csv(f'{HERE}/data/csv/{fn}.csv'):
        k=rkey(r);v=cache.get(k)
        if v and k not in appr:used[b].add((round(v[0],5),round(v[1],5)))
print('sedi da cercare nei locator:',len(targets),flush=True)
ok=0;fail=[];verifica=[]
for i,(b,fn,r) in enumerate(targets):
    ck=cname(r["CITTA'"]);c=cent.get(ck)
    if not c:fail.append((b,r,'comune non presente nei confini'));continue
    key=(b,ck)
    if key not in fetched:
        try:fetched[key]=(isp if b=='ISP' else mps)(c[0],c[1],max(4000,int(c[2]*111000*0.8)));time.sleep(0.4)
        except Exception as e:fetched[key]=None;fail.append((b,r,'errore locator: '+str(e)[:40]));continue
    cands=[x for x in (fetched[key] or []) if cname(x['com'])==ck or x['cap']==r['CAP']]
    mine=akey(r['INDIRIZZO']);best=None;why=''
    ex=[x for x in cands if akey(x['ind'])==mine]
    if ex:best=ex[0];why='indirizzo identico'
    else:
        s=[x for x in cands if x['cap']==r['CAP'] and num(x['ind'])==num(r['INDIRIZZO']) and simili(x['ind'],r['INDIRIZZO'])]
        if len(s)==1:best=s[0];why='stesso CAP, civico e via simile'
        else:
            lib=[x for x in cands if (round(x['lat'],5),round(x['lon'],5)) not in used[b]]
            if len(lib)==1 and len([1 for t in targets if t[0]==b and cname(t[2]["CITTA'"])==ck])==1:best=lib[0];why='unica sede libera nel comune'
    if best:
        ok+=1;print(f"OK  {b} {r['INDIRIZZO']} ({r['CITTA'+chr(39)]}) -> {best['ind']} [{why}]")
        if not PROVA:cache[rkey(r)]=[best['lat'],best['lon'],'bank' if why!='unica sede libera nel comune' else 'bank1']
        if why=='unica sede libera nel comune':verifica.append((b,r,best['ind']))
        used[b].add((round(best['lat'],5),round(best['lon'],5)))
    else:
        fail.append((b,r,f'nessuna corrispondenza tra {len(cands)} sedi del locator nel comune'))
if not PROVA:
    json.dump(cache,open(CACHE,'w'))
    json.dump({'non_risolte':[dict(banca=b,indirizzo=r['INDIRIZZO'],cap=r['CAP'],citta=r["CITTA'"],frazione=r['FRAZIONE'],motivo=m) for b,r,m in fail],'assegnate_per_esclusione':[dict(banca=b,indirizzo_csv=r['INDIRIZZO'],citta=r["CITTA'"],indirizzo_locator=a) for b,r,a in verifica]},open(f'{HERE}/data/non_risolte.json','w'),ensure_ascii=False,indent=1)
print(f'\nrisolte {ok} su {len(targets)}; non risolte {len(fail)}')
