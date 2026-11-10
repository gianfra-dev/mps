#!/usr/bin/env python3
"""Genera le mappe regionali (<regione>/index.html) e la pagina d'accesso (index.html).
Uso: python3 build.py <cartella_dati> [cartella_output]
Cartella dati: isp_raw.json, mps_raw.json (crawl.py), osm_bper.json (Overpass), prov.geojson, g/com1..20.geojson"""
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
def simp(coords,eps=0.0002,nd=4):
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
# ---------- normalizzazione sedi ----------
raw=[]
for x in json.load(open(f'{DATA}/isp_raw.json')):
    if x['abi'] not in ('03069','03239'):continue   # esclusa Fideuram
    c1=x.get('categoria1');pb=x['abi']=='03239'
    name=(x.get('datiSoa') or {}).get('descrizioneFiliale') or x['comune']
    raw.append(dict(b='ISP',nome=tt(name),ind=tt(x['indirizzo']),cap=x.get('cap') or '',tel=x.get('numeroTelefono'),lat=x['latitudine'],lon=x['longitudine'],comd=x['comune'],provd=x.get('codiceProvincia'),cod=x['chiave'],
        tip='Private Banking' if pb else ('Filiale imprese' if c1=='Filiale Imprese' else 'Altro sportello' if c1=='Altro' else 'Filiale'),spec=pb or c1 in ('Filiale Imprese','Altro'),marchio='Private Banking' if pb else ''))
for x in json.load(open(f'{DATA}/mps_raw.json')):
    e=x['entitaBanca'][0]
    raw.append(dict(b='MPS',nome=tt(e.get('descrizioneFiliale') or x['comune']),ind=tt(x['indirizzo']),cap=x.get('cap') or '',tel=x.get('telefono'),lat=x['latitudine'],lon=x['longitudine'],comd=x['comune'],provd=x.get('provincia'),cod=str(e.get('codiceFiliale')),tip='Filiale',spec=False,marchio=''))
seen=set()
for e in json.load(open(f'{DATA}/osm_bper.json'))['elements']:
    t=e['tags'];lat=e.get('lat') or e['center']['lat'];lon=e.get('lon') or e['center']['lon']
    k=(round(lat,3),round(lon,3))
    if k in seen:continue
    seen.add(k)
    ind=((t.get('addr:street') or '')+(' '+t['addr:housenumber'] if t.get('addr:housenumber') else '')).strip()
    raw.append(dict(b='BPER',nome=tt(t.get('name') or 'BPER Banca')+(' – '+t['addr:city'] if t.get('addr:city') else ''),ind=ind or '(indirizzo non indicato)',cap=t.get('addr:postcode') or '',tel=t.get('phone') or t.get('contact:phone'),lat=lat,lon=lon,comd=t.get('addr:city') or '',provd=None,cod=f"osm-{e['type'][0]}{e['id']}",tip='Filiale',spec=False,marchio=(t.get('brand') if t.get('brand') and 'BPER' not in t.get('brand','').upper() else '')))
print('sedi grezze',collections.Counter(r['b'] for r in raw))
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
unm=collections.Counter()
for r in raw:
    done=False
    for R in REG:
        rb=R['rb']
        if not(rb[0]<=r['lon']<=rb[2] and rb[1]<=r['lat']<=rb[3]):continue
        for f,bb in zip(R['cf'],R['bbs']):
            if inside(r['lon'],r['lat'],f['geometry'],bb):
                r['com']=f['properties']['n'];r['prov']=f['properties']['p'];R['br'].append(r);done=True;break
        if done:break
    if not done:unm[r['b']]+=1
print('sedi fuori da ogni comune (scartate):',dict(unm))
KEY={"Valle d'Aosta/Vallée d'Aoste":("Valle d'Aosta",'valle-d-aosta'),'Trentino-Alto Adige/Südtirol':('Trentino-Alto Adige','trentino-alto-adige')}
regs=json.load(open(f'{DATA}/g/../regions.geojson'))['features'] if os.path.exists(f'{DATA}/regions.geojson') else json.load(open(f'{HERE}/data/regions.geojson'))['features']
regf={f['properties']['reg_name']:f for f in regs}
summary=[]
for R in REG:
    rname,slug=KEY.get(R['rname'],(R['rname'],re.sub(r'[^a-z]+','-',unicodedata.normalize('NFKD',R['rname'].lower()).encode('ascii','ignore').decode()).strip('-')))
    pf=[{'type':'Feature','properties':{'p':f['properties']['prov_acr'],'n':f['properties']['prov_name']},'geometry':geom(f['geometry'])} for f in prov if f['properties']['reg_name']==R['rname']]
    br=[{k:v for k,v in b.items() if k not in('comd','provd')} for b in R['br']]
    cnt=collections.defaultdict(set)
    for b in br:cnt[b['com']].add(b['b'])
    k2=sum(len(v)>=2 for v in cnt.values());k3=sum(len(v)==3 for v in cnt.values())
    n={k:sum(b['b']==k for b in br) for k in ('ISP','BPER','MPS')}
    print(f"{rname:22} ISP {n['ISP']:4} BPER {n['BPER']:4} MPS {n['MPS']:4} comuni {len(R['cf']):4} 2+:{k2:3} 3:{k3:3}")
    data=json.dumps({'comuni':{'type':'FeatureCollection','features':R['cf']},'prov':{'type':'FeatureCollection','features':pf},'br':br},separators=(',',':'),ensure_ascii=False)
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
        ring=[proj(p) for p in poly[0]];xs=[p[0] for p in ring];ys=[p[1] for p in ring]
        if (max(xs)-min(xs))*(max(ys)-min(ys))<6:continue
        ds+='M'+'L'.join(f'{x},{y}' for x,y in dpring(ring,0.35))+'Z'
    paths.append((s,ds))
W=math.ceil((18.8-X0)*K*S);H=math.ceil((Y0-35.4)*S)
svg=''.join(f'<a href="{s["slug"]}/" class="reg" data-n="{s["name"]}" data-i="{s["n"]["ISP"]}" data-b="{s["n"]["BPER"]}" data-m="{s["n"]["MPS"]}" data-o="{s["k2"]}"><title>{s["name"]}</title><path d="{ds}"/></a>' for s,ds in paths)
rows=''.join(f'<tr><td><a href="{s["slug"]}/">{s["name"]}</a></td><td class="n i">{s["n"]["ISP"]}</td><td class="n b">{s["n"]["BPER"]}</td><td class="n m">{s["n"]["MPS"]}</td><td class="n y">{s["k2"]}</td></tr>' for s in sorted(summary,key=lambda s:s['name']))
tot=lambda k:sum(s['n'][k] for s in summary)
html=open(f'{HERE}/landing.html').read()
for k,v in [('__SVG__',svg),('__W__',str(W)),('__H__',str(H)),('__ROWS__',rows),('__DATE__',TODAY),('__TI__',str(tot('ISP'))),('__TB__',str(tot('BPER'))),('__TM__',str(tot('MPS'))),('__TO__',str(sum(s['k2'] for s in summary)))]:html=html.replace(k,v)
open(f'{ROOT}/index.html','w').write(html)
print('TOTALE',{k:tot(k) for k in('ISP','BPER','MPS')},'comuni 2+',sum(s['k2'] for s in summary))
