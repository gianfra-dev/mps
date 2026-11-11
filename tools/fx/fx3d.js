/* Transizioni 3D tra le pagine e piccoli effetti di profondita'. Nessun listener di scroll. */
(()=>{
const root=document.documentElement,RM=matchMedia('(prefers-reduced-motion: reduce)');
const store=(k,v)=>{try{v===undefined?sessionStorage.removeItem(k):sessionStorage.setItem(k,v)}catch(e){}};
const read=k=>{try{return sessionStorage.getItem(k)}catch(e){return null}};

/* entrata: la direzione e' quella scelta nella pagina di partenza */
const dir=read('fxdir');store('fxdir');
if(!RM.matches)root.classList.add(dir==='back'?'fx-in-back':'fx-in-fwd');
addEventListener('animationend',e=>{if(e.target===document.body)root.classList.remove('fx-in-fwd','fx-in-back')});


/* lancio dei dadi: due dadi 3D rotolano, poi si apre la regione */
const PIPS={1:[[2,2]],2:[[1,1],[3,3]],3:[[1,1],[2,2],[3,3]],4:[[1,1],[1,3],[3,1],[3,3]],5:[[1,1],[1,3],[2,2],[3,1],[3,3]],6:[[1,1],[2,1],[3,1],[1,3],[2,3],[3,3]]};
const ROT={1:[0,0],6:[0,180],3:[0,-90],4:[0,90],2:[-90,0],5:[90,0]};   /* [rotX, rotY] che porta la faccia davanti */
function cube(cls){
  const n=1+Math.floor(Math.random()*6),[fx,fy]=ROT[n];
  const faces=[1,2,3,4,5,6].map(k=>'<div class="f f'+k+'">'+PIPS[k].map(p=>'<i style="grid-area:'+p[0]+'/'+p[1]+'"></i>').join('')+'</div>').join('');
  return '<div class="fx-cube '+cls+'" data-fx="'+fx+'" data-fy="'+fy+'">'+faces+'</div>';
}
function diceLeave(href,name){
  store('fxdir','fwd');
  const o=document.createElement('div');o.className='fx-dice';o.setAttribute('aria-hidden','true');
  o.innerHTML='<div class="pair">'+cube('r')+cube('u')+'</div><div class="name"></div>';
  o.querySelector('.name').textContent=name;
  root.appendChild(o);
  /* animazione via Web Animations: valori espliciti, nessuna variabile CSS (piu' sicuro su Safari) */
  o.querySelectorAll('.fx-cube').forEach((c,i)=>{
    const fx=+c.dataset.fx,fy=+c.dataset.fy,end='rotateX('+fx+'deg) rotateY('+fy+'deg)';
    const t=(x,y,z,rx,ry)=>'translate3d('+x+','+y+','+z+') rotateX('+(fx+rx)+'deg) rotateY('+(fy+ry)+'deg)';
    c.style.transform=end;
    if(c.animate)c.animate([
      {transform:'translate3d(-30vw,-70vh,-300px) rotateX(0deg) rotateY(0deg)',offset:0},
      {transform:t('0px','0px','40px',540,720),offset:.55},
      {transform:t('0px','-9vh','20px',630,810),offset:.72},
      {transform:t('0px','0px','0px',720,1080),offset:1}],
      {duration:1000+i*50,delay:100+i*100,easing:'cubic-bezier(.3,.7,.4,1)',fill:'backwards'});
  });
  setTimeout(()=>{location.href=href},1650);
}

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
  if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.getAttribute('target'))return;
  const u=new URL(a.getAttribute('href'),location.href);
  if(u.origin!==location.origin||(u.pathname===location.pathname&&u.hash))return;
  e.preventDefault();
  const r=a.getBoundingClientRect();
  if(!RM.matches&&!a.classList.contains('back')&&document.querySelector('.mapbox')){diceLeave(u.href,(a.dataset.n||a.textContent).trim());return}
  leave(u.href,r.left+r.width/2,r.top+r.height/2,a.classList.contains('back')?'back':'fwd');
});
addEventListener('pageshow',e=>{if(e.persisted){root.classList.remove('fx-out-fwd','fx-out-back');document.querySelectorAll('.fx-dice').forEach(d=>d.remove())}});

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
