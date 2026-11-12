#!/usr/bin/env python3
"""Crea un unico file HTML (pagina iniziale + 20 regioni) a partire dalle pagine già generate da build.py.
Uso: python3 build_singolo.py [file_output]   (default: ../filiali-tre-banche.html)"""
import os,re,sys,glob,json,base64
HERE=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.abspath(os.path.join(HERE,'..'))
OUT=sys.argv[1] if len(sys.argv)>1 else f'{ROOT}/filiali-tre-banche.html'
SRC=os.environ.get('SRC',ROOT)   # cartella con le pagine già generate (default: la radice del sito)
logo='data:image/png;base64,'+base64.b64encode(open(f'{ROOT}/assets/logo.png','rb').read()).decode()
esc=lambda s:s.replace('</script','<\\/script')
land=open(f'{SRC}/index.html',encoding='utf-8').read().replace('assets/logo.png',logo)
blocks=[];slugs=[]
for p in sorted(glob.glob(f'{SRC}/*/index.html')):
    slug=os.path.basename(os.path.dirname(p))
    if slug in('assets','tools'):continue
    h=open(p,encoding='utf-8').read().replace('../assets/logo.png','@@LOGO@@')
    if '<a class="back" href="../"' not in h:continue   # salta cartelle che non sono pagine regionali standard
    h=h.replace('<a class="back" href="../"','<a class="back" href="#" onclick="parent.postMessage(\'home\',\'*\');return false"')
    assert 'onclick="parent.postMessage' in h,slug
    blocks.append(f'<script type="text/html" id="r-{slug}">{esc(h)}</script>');slugs.append(slug)
js='''<script>
(function(){
var S=%s,fr=null;
function open(s,push){if(fr)fr.remove();var el=document.getElementById('r-'+s);if(!el)return;
  fr=document.createElement('iframe');fr.srcdoc=el.textContent.replace(/<\\\\\\/script/g,'</script').split('@@LOGO@@').join(document.querySelector('header img').src);
  fr.style.cssText='position:fixed;inset:0;width:100%%;height:100%%;border:0;background:#fff;z-index:9999';
  document.body.appendChild(fr);document.documentElement.style.overflow='hidden';if(push)location.hash=s}
function home(){if(fr){fr.remove();fr=null}document.documentElement.style.overflow=''}
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
print(len(slugs),'regioni ->',OUT,round(os.path.getsize(OUT)/1e6,1),'MB')
