#!/usr/bin/env python3
"""Crea un unico file HTML (pagina iniziale + 20 regioni) a partire dalle pagine già generate da build.py.
Ogni pagina regionale è compressa (gzip) e decompressa nel browser solo quando serve (DecompressionStream).
Uso: python3 build_singolo.py [file_output]                      (default: ../filiali-tre-banche.html, usa le pagine già generate)
     CONFINI=<cartella_confini> python3 build_singolo.py          (rigenera le pagine con confini semplificati, ~110 m, e produce il file più piccolo)
     [SRC=cartella_pagine]                                         (cartella di pagine già generate da usare al posto della radice)"""
import os,re,sys,glob,json,base64,zlib,subprocess,tempfile
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.abspath(os.path.join(HERE,'..'))
OUT=sys.argv[1] if len(sys.argv)>1 else f'{ROOT}/filiali-tre-banche.html'
SRC=os.environ.get('SRC',ROOT)   # cartella con le pagine già generate (default: la radice del sito)
if os.environ.get('CONFINI'):   # variante leggera: pagine rigenerate in una cartella temporanea con confini semplificati
    TMP=tempfile.mkdtemp();SRC=TMP
    subprocess.run([sys.executable,f'{HERE}/build.py',os.environ['CONFINI'],TMP],check=True,env={**os.environ,'EPS':os.environ.get('EPS','0.001')},stdout=subprocess.DEVNULL)
def logo_uri():
    """logo ridotto (JPEG 560 px) per il file unico: pesa circa un terzo del PNG"""
    with tempfile.TemporaryDirectory() as d:
        o=f'{d}/l.jpg'
        try:
            subprocess.run(['sips','-s','format','jpeg','-s','formatOptions','82','-Z','560',f'{ROOT}/assets/logo.png','--out',o],check=True,capture_output=True)
            return 'data:image/jpeg;base64,'+base64.b64encode(open(o,'rb').read()).decode()
        except Exception:   # senza sips (non macOS): PNG originale
            return 'data:image/png;base64,'+base64.b64encode(open(f'{ROOT}/assets/logo.png','rb').read()).decode()
logo=logo_uri()
gz=lambda s:base64.b64encode((lambda c:c.compress(s.encode('utf-8'))+c.flush())(zlib.compressobj(9,zlib.DEFLATED,31))).decode()
land=open(f'{SRC}/index.html',encoding='utf-8').read().replace('<link rel="icon" href="assets/logo.png">','').replace('assets/logo.png',logo)
blocks=[];slugs=[];raw=0
for p in sorted(glob.glob(f'{SRC}/*/index.html')):
    slug=os.path.basename(os.path.dirname(p))
    h=open(p,encoding='utf-8').read().replace('../assets/logo.png','@@LOGO@@')
    if '<a class="back" href="../"' not in h:continue   # salta cartelle che non sono pagine regionali standard
    h=h.replace('<link rel="icon" href="@@LOGO@@">','')
    h=h.replace('<a class="back" href="../"','<a class="back" href="#" onclick="parent.postMessage(\'home\',\'*\');return false"')
    assert 'onclick="parent.postMessage' in h,slug
    raw+=len(h);blocks.append(f'<script type="text/plain" id="r-{slug}">{gz(h)}</script>');slugs.append(slug)
js='''<script>
(function(){
var S=%s,fr=null,tok=0;
function gunz(b){var bin=atob(b),u=new Uint8Array(bin.length);for(var i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
  return new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('gzip'))).text()}
function open(s,push){var el=document.getElementById('r-'+s);if(!el)return;
  if(typeof DecompressionStream==='undefined'){alert('Questo browser è troppo vecchio per aprire la mappa: aggiornalo.');return}
  var t=++tok;
  gunz(el.textContent.trim()).then(function(h){if(t!==tok)return;if(fr)fr.remove();
    fr=document.createElement('iframe');fr.srcdoc=h.split('@@LOGO@@').join(document.querySelector('header img').src);
    fr.style.cssText='position:fixed;inset:0;width:100%%;height:100%%;border:0;background:#fff;z-index:9999';
    document.body.appendChild(fr);document.documentElement.style.overflow='hidden';if(push)location.hash=s})}
function home(){tok++;if(fr){fr.remove();fr=null}document.documentElement.style.overflow=''}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;
  var m=(a.getAttribute('href')||'').match(/^([a-z-]+)\\/$/);if(m&&S.indexOf(m[1])>=0){e.preventDefault();open(m[1],true)}},true);
window.addEventListener('message',function(e){if(e.data==='home'){home();history.replaceState(null,'',location.pathname+location.search)}});
window.addEventListener('hashchange',function(){var s=location.hash.slice(1);s&&S.indexOf(s)>=0?open(s,false):home()});
var s=location.hash.slice(1);if(s&&S.indexOf(s)>=0)open(s,false);
})();
</script>'''%json.dumps(slugs)
assert '</body>' in land
land=land.replace('</body>',''.join(blocks)+js+'</body>')
open(OUT,'w',encoding='utf-8').write(land)
print(len(slugs),'regioni ->',OUT,round(os.path.getsize(OUT)/1e6,2),'MB (pagine non compresse:',round(raw/1e6,1),'MB)')
