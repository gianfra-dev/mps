#!/usr/bin/env python3
"""Genera le mappe regionali (<regione>/index.html) e la pagina d'accesso (index.html).
Uso: python3 build.py <cartella_dati> [cartella_output]
Cartella dati: prov.geojson, g/com1..20.geojson (confini). Sedi: tools/data/csv/*.csv (Banca d'Italia) e tools/data/geocode.json (geocode.py)"""
import re,json,sys,os,unicodedata,collections,datetime,math
DATA=sys.argv[1];HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.abspath(sys.argv[2] if len(sys.argv)>2 else os.path.join(HERE,'..'))
TODAY=datetime.date.today().strftime('%d/%m/%Y')
def norm(s):
    s=unicodedata.normalize('NFD',s.lower());return re.sub(r'[^a-z]','',''.join(ch for ch in s if not unicodedata.combining(ch)))
def dp(pts,eps):
    if len(pts)<5:return pts
    keep=[False]*len(pts);keep[0]=keep[-1]=True;st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop();ax,ay=pts[a];bx,by=pts[b];dx,dy=bx-ax,by-ay;L=math.hypot(dx,dy) or 1e-12;mx=-1;mi=a
        for i in range(a+1,b):
            dd=abs(dy*(pts[i][0]-ax)-dx*(pts[i][1]-ay))/L
            if dd>mx:mx=dd;mi=i
        if mx>eps:keep[mi]=True;st.append((a,mi));st.append((mi,b))
    return [p for p,k in zip(pts,keep) if k]
def dpring(r,eps):
    m=len(r)//2
    return (dp(r[:m+1],eps)[:-1]+dp(r[m:],eps)) if len(r)>=8 else r
EPS=float(os.environ.get('EPS',0.0002));ND=int(os.environ.get('ND',4))
def simp(coords,eps=None,nd=None):
    eps=EPS if eps is None else eps;nd=ND if nd is None else nd
    out=[]
    for ring in coords:
        r=[[round(x,nd),round(y,nd)] for x,y in dpring(ring,eps)];rr=[];last=None
        for p in r:
            if p!=last:rr.append(p)
            last=p
        if len(rr)>=4:out.append(rr)
    return out
def geom(g):
    polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    ps=[p for p in (simp(q) for q in polys) if p]
    if not ps:ps=[p for p in (simp(q,0) for q in polys) if p]
    return {'type':'MultiPolygon','coordinates':ps}
def bbox(g):
    xs=[p[0] for q in g['coordinates'] for p in q[0]];ys=[p[1] for q in g['coordinates'] for p in q[0]];return min(xs),min(ys),max(xs),max(ys)
def pip(x,y,ring):
    ins=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:ins=not ins
        j=i
    return ins
def inside(x,y,g,bb):
    if not(bb[0]<=x<=bb[2] and bb[1]<=y<=bb[3]):return False
    return any(pip(x,y,p[0]) and not any(pip(x,y,hh) for hh in p[1:]) for p in g['coordinates'])
tt=lambda s:(s or '').strip().title().replace("'S ","'s ")
# ---------- sedi dai CSV Banca d'Italia + coordinate (geocode.json) ----------
sys.path.insert(0,HERE)
from common import read_csv,cname
GEO=json.load(open(f'{HERE}/data/geocode.json'))
raw=[]
for b,fn in (('ISP','intesa'),('BPER','bper'),('MPS','mps'),('BPER','bds')):   # il Banco di Sardegna (fn='bds') è conteggiato come BPER, marcato con s=1
    for r in read_csv(f'{HERE}/data/csv/{fn}.csv'):
        k='|'.join([r['CODICE MECCANOGRAFICO INTERMEDIARIO'],r['CODICE SUCCURSALE'],r['CAP'],r['INDIRIZZO']]);g=GEO.get(k)
        city=r["CITTA'"].strip().title();fr=r['FRAZIONE'].strip().title()
        raw.append(dict(k=k,b=b,nome=city+(' – '+fr if fr else ''),ind=tt(r['INDIRIZZO']),cap=r['CAP'],tel='',lat=g[0] if g else None,lon=g[1] if g else None,prec=(g[2] if g else None),comd=r["CITTA'"],provd=None,cod=r['CODICE SUCCURSALE'],tip='Filiale',spec=False,marchio='',s=1 if fn=='bds' else 0))
print('sedi dai CSV',collections.Counter(r['b'] for r in raw),'senza coordinate',sum(r['lat'] is None for r in raw))
# ---------- confini ----------
prov=json.load(open(f'{DATA}/prov.geojson'))['features']
REG=[]
for code in range(1,21):
    com=json.load(open(f'{DATA}/g/com{code}.geojson'))['features'];rname=com[0]['properties']['reg_name']
    cf=[];bbs=[]
    for f in com:
        g=geom(f['geometry']);cf.append({'type':'Feature','properties':{'n':f['properties']['name'],'p':f['properties']['prov_acr'],'k':norm(f['properties']['name'])},'geometry':g});bbs.append(bbox(g))
    rb=(min(b[0] for b in bbs),min(b[1] for b in bbs),max(b[2] for b in bbs),max(b[3] for b in bbs))
    REG.append(dict(code=code,rname=rname,cf=cf,bbs=bbs,rb=rb,PROVN={f['properties']['prov_acr']:f['properties']['prov_name'] for f in com},br=[]))
unm=collections.Counter();approx=collections.Counter()
byname=collections.defaultdict(list)
for R in REG:
    for f,bb in zip(R['cf'],R['bbs']):byname[f['properties']['k']].append((R,f,bb))
for r in raw:
    done=False
    if r['lat'] is not None:
        for R in REG:
            rb=R['rb']
            if not(rb[0]<=r['lon']<=rb[2] and rb[1]<=r['lat']<=rb[3]):continue
            for f,bb in zip(R['cf'],R['bbs']):
                if inside(r['lon'],r['lat'],f['geometry'],bb):
                    r['com']=f['properties']['n'];r['prov']=f['properties']['p'];done=True
                    exp=byname.get(cname(r['comd']),[])
                    if len(exp)==1 and exp[0][1] is not f:   # la posizione cade in un comune diverso da quello del CSV
                        if r.get('prec') in ('bank','bank1','manuale'):   # pin del locator ufficiale o inserito a mano: si tiene il pin, il comune è quello del CSV
                            Rx,fx,_=exp[0];r['com']=fx['properties']['n'];r['prov']=fx['properties']['p'];Rx['br'].append(r)
                        else:done=False                                    # geocodifica automatica dubbia: si fida del CSV (centro del comune)
                    else:R['br'].append(r)
                    break
            if done:break
    if not done:
        # coordinate assenti o fuori comune: uso il nome del comune (se univoco) e il centro del comune
        c=byname.get(cname(r['comd']),[])
        if len(c)==1:
            R,f,bb=c[0];r['com']=f['properties']['n'];r['prov']=f['properties']['p']
            if r['lat'] is None or r.get('prec') not in ('bank','bank1','manuale'):
                r['lon']=round((bb[0]+bb[2])/2,5);r['lat']=round((bb[1]+bb[3])/2,5);r['prec']='city'
            R['br'].append(r);done=True
    if not done:unm[(r['b'],r['comd'])]+=1
    elif r.get('prec') in ('city',None):approx[r['b']]+=1;r['a']=1
json.dump(sorted(r['k'] for R in REG for r in R['br'] if r.get('a')),open(f'{HERE}/data/approssimate.json','w'))
print('sedi senza comune riconosciuto (scartate):',sum(unm.values()),list(unm.items())[:12]);print('posizione approssimativa:',dict(approx))
KEY={"Valle d'Aosta/Vallée d'Aoste":("Valle d'Aosta",'valle-d-aosta'),'Trentino-Alto Adige/Südtirol':('Trentino-Alto Adige','trentino-alto-adige')}
regs=json.load(open(f'{DATA}/g/../regions.geojson'))['features'] if os.path.exists(f'{DATA}/regions.geojson') else json.load(open(f'{HERE}/data/regions.geojson'))['features']
regf={f['properties']['reg_name']:f for f in regs}
def encring(r):   # anello -> [x0,y0,dx,dy,...] in interi (1e-4 gradi): molto più compatto; la pagina lo decodifica
    o=[];px=py=0
    for x,y in r:
        X=round(x*1e4);Y=round(y*1e4);o+= [X-px,Y-py];px,py=X,Y
    return o
def enc(fs):return [{**f,'geometry':{'type':'MultiPolygon','coordinates':[[encring(r) for r in p] for p in f['geometry']['coordinates']]}} for f in fs]
summary=[]
for R in REG:
    rname,slug=KEY.get(R['rname'],(R['rname'],re.sub(r'[^a-z]+','-',unicodedata.normalize('NFKD',R['rname'].lower()).encode('ascii','ignore').decode()).strip('-')))
    pf=[{'type':'Feature','properties':{'p':f['properties']['prov_acr'],'n':f['properties']['prov_name']},'geometry':geom(f['geometry'])} for f in prov if f['properties']['reg_name']==R['rname']]
    br=[{k:v for k,v in b.items() if k not in('k','comd','provd','prec','tel','marchio','spec') and not(k=='s' and not v)} for b in R['br']]
    cnt=collections.defaultdict(set)
    for b in br:cnt[b['com']].add(b['b'])
    k2=sum(len(v)>=2 for v in cnt.values());k3=sum(len(v)==3 for v in cnt.values())
    n={k:sum(b['b']==k for b in br) for k in ('ISP','BPER','MPS')}
    print(f"{rname:22} ISP {n['ISP']:4} BPER {n['BPER']:4} MPS {n['MPS']:4} comuni {len(R['cf']):4} 2+:{k2:3} 3:{k3:3}")
    data=json.dumps({'comuni':{'type':'FeatureCollection','features':enc(R['cf'])},'prov':{'type':'FeatureCollection','features':enc(pf)},'br':br},separators=(',',':'),ensure_ascii=False)
    t=open(f'{HERE}/template.html').read()
    for k,v in [('__REG__',rname),('__DATE__',TODAY),('__PROVN__',json.dumps(R['PROVN'],ensure_ascii=False)),('__SLUG__',slug),('__DATA__',data)]:t=t.replace(k,v)
    os.makedirs(f'{ROOT}/{slug}',exist_ok=True);open(f'{ROOT}/{slug}/index.html','w').write(t)
    summary.append(dict(slug=slug,name=rname,n=n,k2=k2,k3=k3,feat=regf[R['rname']]))
# ---------- pagina d'accesso ----------
S=60;X0=6.5;Y0=47.2;K=math.cos(math.radians(42))
proj=lambda p:[round((p[0]-X0)*K*S,1),round((Y0-p[1])*S,1)]
paths=[]
for s in summary:
    g=s['feat']['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'];ds=''
    for poly in polys:
        if sum(p[1] for p in poly[0])/len(poly[0])<36.2:continue   # Lampedusa e Linosa fuori dalla mappa schematica
        ring=[proj(p) for p in poly[0]];xs=[p[0] for p in ring];ys=[p[1] for p in ring]
        if (max(xs)-min(xs))*(max(ys)-min(ys))<6:continue
        ds+='M'+'L'.join(f'{x},{y}' for x,y in dpring(ring,0.35))+'Z'
    paths.append((s,ds))
W=math.ceil((18.8-X0)*K*S);H=math.ceil((Y0-36.55)*S)
seas=''.join(f'<text class="sea" transform="translate({proj([lo,la])[0]},{proj([lo,la])[1]}) rotate({r})">{n}</text>' for n,lo,la,r in (('Mar Ligure',8.5,43.45,-18),('Mar Tirreno',12.3,39.7,62),('Mar Adriatico',14.7,42.8,48),('Mar Ionio',17.6,38.2,40))) if os.environ.get('LANDING')=='landing_risiko.html' else ''   # nomi dei mari solo per la variante Risiko
svg=seas+''.join(f'<a href="{s["slug"]}/" class="reg" data-n="{s["name"]}" data-i="{s["n"]["ISP"]}" data-b="{s["n"]["BPER"]}" data-m="{s["n"]["MPS"]}" data-o="{s["k2"]}"><title>{s["name"]}</title><path d="{ds}"/></a>' for s,ds in paths)
rows=''.join(f'<tr><td><a href="{s["slug"]}/">{s["name"]}</a></td><td class="n i">{s["n"]["ISP"]}</td><td class="n b">{s["n"]["BPER"]}</td><td class="n m">{s["n"]["MPS"]}</td><td class="n y">{s["k2"]}</td></tr>' for s in sorted(summary,key=lambda s:s['name']))
mil=lambda n:f'{n:,}'.replace(',','.')
tot=lambda k:sum(s['n'][k] for s in summary)
html=open(f"{HERE}/{os.environ.get('LANDING','landing.html')}").read()
for k,v in [('__SVG__',svg),('__W__',str(W)),('__H__',str(H)),('__ROWS__',rows),('__DATE__',TODAY),('__TI__',mil(tot('ISP'))),('__TB__',mil(tot('BPER'))),('__TM__',mil(tot('MPS'))),('__TO__',mil(sum(s['k2'] for s in summary)))]:html=html.replace(k,v)
open(f'{ROOT}/index.html','w').write(html)
print('TOTALE',{k:tot(k) for k in('ISP','BPER','MPS')},'comuni 2+',sum(s['k2'] for s in summary))
