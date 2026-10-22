const viewer=document.querySelector('#shield');
const state={madera:'#ffffff',acero:'#ffffff',bronce:'#ffffff',roughness:.7};
const announce=(text)=>{document.querySelector('#announcement').textContent=text;};
function applyMaterial(name,color){
  const material=viewer.model?.materials.find(m=>m.name===name);
  if(!material)return;
  material.pbrMetallicRoughness.setBaseColorFactor(color);
  state[name]=color;
  const group=document.querySelector(`.swatches[data-material="${name}"]`);
  group.querySelectorAll('button').forEach(button=>{const selected=button.dataset.color===color;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});
  group.querySelector('input').value=color;
}
function applyFinish(value){
  viewer.model?.materials.filter(m=>m.name==='acero'||m.name==='bronce').forEach(m=>m.pbrMetallicRoughness.setRoughnessFactor(value));
  state.roughness=value;
  document.querySelectorAll('#finish button').forEach(b=>{const selected=Number(b.dataset.roughness)===value;b.classList.toggle('selected',selected);b.setAttribute('aria-pressed',String(selected));});
}
function setView(view){
  viewer.autoRotate=false;
  viewer.resetTurntableRotation(0);
  viewer.cameraOrbit={front:'-18deg 78deg 110%',back:'180deg 82deg 110%',detail:'-27deg 67deg 75%'}[view];
  viewer.cameraTarget='0m 0m 0m';
  syncRotate();
  document.querySelectorAll('[data-view]').forEach(b=>{const selected=b.dataset.view===view;b.classList.toggle('active',selected);b.setAttribute('aria-pressed',String(selected));});
}
function syncRotate(){document.querySelector('#rotate').setAttribute('aria-pressed',String(viewer.autoRotate));}
viewer.addEventListener('load',()=>{
  document.querySelector('#controls').disabled=false;
  document.querySelector('#status-label').textContent='EXPLORACIÓN 3D EN TIEMPO REAL';
  document.querySelector('#loading').hidden=true;
  announce('Escudo cargado. Ya puedes girarlo y modificar sus materiales.');
});
viewer.addEventListener('progress',e=>{document.querySelector('#progress-fill').style.width=`${Math.round(e.detail.totalProgress*100)}%`;});
viewer.addEventListener('error',()=>{document.querySelector('#loading').hidden=true;document.querySelector('#error').hidden=false;document.querySelector('#status-label').textContent='ERROR DE CARGA';});
document.querySelectorAll('.swatches button').forEach(b=>b.addEventListener('click',()=>{applyMaterial(b.closest('.swatches').dataset.material,b.dataset.color);announce(b.getAttribute('aria-label')+' aplicado');}));
document.querySelectorAll('input[type=color]').forEach(i=>i.addEventListener('input',()=>applyMaterial(i.dataset.material,i.value)));
document.querySelectorAll('#finish button').forEach(b=>b.addEventListener('click',()=>{applyFinish(Number(b.dataset.roughness));announce('Acabado '+b.textContent+' aplicado');}));
document.querySelector('#exposure').addEventListener('input',e=>{viewer.exposure=Number(e.target.value)/100;document.querySelector('#exposure-value').value=e.target.value+'%';});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
document.querySelector('#rotate').addEventListener('click',()=>{viewer.autoRotate=!viewer.autoRotate;viewer.rotationPerSecond='15deg';viewer.autoRotateDelay=500;syncRotate();});
document.querySelector('#reset').addEventListener('click',()=>{
  if(!viewer.model)return;
  ['madera','acero','bronce'].forEach(name=>applyMaterial(name,'#ffffff'));applyFinish(.7);setView('front');
  viewer.exposure=1.15;document.querySelector('#exposure').value=115;document.querySelector('#exposure-value').value='115%';announce('Apariencia y cámara restablecidas.');
});
document.querySelector('#fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.querySelector('#stage').requestFullscreen();}catch{announce('Tu navegador no permite pantalla completa.');}});
document.addEventListener('fullscreenchange',()=>{const active=!!document.fullscreenElement;document.querySelector('#fullscreen').setAttribute('aria-label',active?'Salir de pantalla completa':'Activar pantalla completa');});
fetch('assets/datos-modelo.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(data=>{document.querySelector('#triangles').textContent=data.triangulos.toLocaleString('es-MX');document.querySelector('#file-size').textContent=(data.glb_bytes/1024/1024).toFixed(2)+' MB';}).catch(()=>{});
