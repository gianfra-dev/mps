#!/usr/bin/env python3
"""Raccoglie le filiali dalle API pubbliche dei locator di Intesa Sanpaolo e MPS, interrogando una griglia di punti sull'Italia.
Uso: python3 crawl.py isp|mps <cartella_output>"""
import json,sys,time,math,uuid,urllib.request,os
bank,OUT=sys.argv[1],sys.argv[2];os.makedirs(OUT,exist_ok=True)
regs=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data/regions.geojson')))['features']
rings=[];verts=[]
for f in regs:
    g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    for p in polys:
        rings.append(p[0]);verts+=p[0][::3]
def pip(x,y,r):
    ins=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:ins=not ins
        j=i
    return ins
def land(lat,lon,tol):
    if any(pip(lon,lat,r) for r in rings):return True
    return any((lon-vx)**2*0.53+(lat-vy)**2<tol**2 for vx,vy in verts)
STEP,RAD={'isp':(0.42,40000),'mps':(0.33,30000)}[bank]
pts=[]
lat=35.4
while lat<47.2:
    lon=6.5;dl=STEP/math.cos(math.radians(lat))
    while lon<18.8:
        if land(lat,lon,STEP*0.75):pts.append((round(lat,4),round(lon,4)))
        lon+=dl
    lat+=STEP
print(bank,len(pts),'punti',flush=True)
res={}
def call(lat,lon):
    if bank=='isp':
        body=json.dumps({"payload":{"latitudine":lat,"longitudine":lon,"raggio":RAD,"numeroRisultati":1000}}).encode()
        r=urllib.request.Request("https://api.intesasanpaolo.com/ib/content/api/app/public/filiale/ricercaFilialiGeoloc",data=body,headers={"X-REQUEST-ID":str(uuid.uuid4()),"applicationName":"VET","channel":"02","x-isp-cypher-drw":"false","CALLER":"ricerca-filiali","Page":"ricerca-filiali.ricerca-filiali","x-isp-cypher":"false","X-BEAR-SESSION-TOKEN":"empty","X-ISP-Session-Id":"empty","Content-Type":"application/json","Accept":"application/json","Origin":"https://www.intesasanpaolo.com","User-Agent":"Mozilla/5.0"})
        d=json.load(urllib.request.urlopen(r,timeout=60));return d.get('payload',{}).get('listaFilialiGeoloc',[]) or [],'chiave'
    u=f"https://appx.mps.it/VWRestServices/client/public/filiale/elenco?elemPag=1000&ckF=true&ckB=false&pk=1&lat={lat}&lon={lon}&output=json"
    d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=60));return d.get('listaFiliali',[]) or [],None
mx=0
for i,(la,lo) in enumerate(pts):
    for t in range(3):
        try:L,k=call(la,lo);break
        except Exception as e:
            L=[];time.sleep(2)
    mx=max(mx,len(L))
    for x in L:
        key=x['chiave'] if bank=='isp' else x['entitaBanca'][0]['idElemento'] if x.get('entitaBanca') else (x['latitudine'],x['longitudine'],x['indirizzo'])
        res[key]=x
    if i%25==0:print(i,len(res),'maxrisultati',mx,flush=True)
    time.sleep(0.25)
json.dump(list(res.values()),open(f'{OUT}/{bank}_raw.json','w'),ensure_ascii=False)
print('FATTO',len(res),'maxrisultati',mx,flush=True)
