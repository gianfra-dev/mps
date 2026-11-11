/* Transizioni 3D tra le pagine e piccoli effetti di profondita'. Nessun listener di scroll. */
(()=>{
const root=document.documentElement,RM=matchMedia('(prefers-reduced-motion: reduce)');
const store=(k,v)=>{try{v===undefined?sessionStorage.removeItem(k):sessionStorage.setItem(k,v)}catch(e){}};
const read=k=>{try{return sessionStorage.getItem(k)}catch(e){return null}};

/* entrata: la direzione e' quella scelta nella pagina di partenza */
const dir=read('fxdir');store('fxdir');
if(!RM.matches)root.classList.add(dir==='back'?'fx-in-back':'fx-in-fwd');
addEventListener('animationend',e=>{if(e.target===document.body)root.classList.remove('fx-in-fwd','fx-in-back')});

/* uscita: la pagina gira via prima di navigare */
function leave(href,x,y,d){
  store('fxdir',d);
  if(RM.matches){location.href=href;return}
  root.style.setProperty('--ox',x+'px');root.style.setProperty('--oy',y+'px');
  root.classList.add('fx-out-'+d);
  setTimeout(()=>{location.href=href},520);
}
document.addEventListener('click',e=>{
  const a=e.target.closest&&e.target.closest('a[href]');
  if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target)return;
  const u=new URL(a.getAttribute('href'),location.href);
  if(u.origin!==location.origin||(u.pathname===location.pathname&&u.hash))return;
  e.preventDefault();
  const r=a.getBoundingClientRect();
  leave(u.href,r.left+r.width/2,r.top+r.height/2,a.classList.contains('back')?'back':'fwd');
});
addEventListener('pageshow',e=>{if(e.persisted)root.classList.remove('fx-out-fwd','fx-out-back')});

/* pagina d'accesso */
const box=document.querySelector('.mapbox');
if(box&&!RM.matches){
  document.querySelectorAll('a.reg').forEach((a,i)=>{a.style.setProperty('--i',i);if(a._g)a._g.querySelectorAll('.pz').forEach(p=>p.style.setProperty('--i',i))});
  box.classList.add('fx-deal');
  box.addEventListener('animationend',e=>{if(e.target===box)box.classList.remove('fx-deal')});
  /* il tabellone segue il puntatore: inclinazione massima 7 gradi */
  if(matchMedia('(hover:hover)').matches){
    let raf=0,px=0,py=0;
    const main=document.querySelector('main');
    main.addEventListener('pointermove',e=>{px=e.clientX/innerWidth-.5;py=e.clientY/innerHeight-.5;if(!raf)raf=requestAnimationFrame(()=>{raf=0;box.style.setProperty('--ry',(px*7).toFixed(2)+'deg');box.style.setProperty('--rx',(5-py*7).toFixed(2)+'deg')})});
    main.addEventListener('pointerleave',()=>{box.style.setProperty('--ry','0deg');box.style.setProperty('--rx','0deg')});
    box.style.setProperty('--rx','5deg');
  }
  /* i dadi rotolano da soli all'apertura */
  setTimeout(()=>{const d=document.querySelector('.dice');if(d)d.click()},1500);
}
})();
