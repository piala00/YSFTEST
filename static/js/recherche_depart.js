/* Recherche des départs : aucune requête distante, aucune identité passager dans les URL. */
(function () {
  'use strict';
  function normaliser(s) { return (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().trim(); }
  function filtrer(options, recherche, gammes) {
    const mots = normaliser(recherche).split(/\s+/).filter(Boolean);
    return options.filter(o => gammes.includes(o.gamme) && mots.every(m =>
      normaliser(o.recherche).split(/[|\s-]+/).some(v => v.startsWith(m))));
  }
  function installer(select) {
    if (select.dataset.rechercheInstallee) return;
    select.dataset.rechercheInstallee = '1';
    const options = [...select.options].filter(o => o.value).map(o => ({value:o.value, label:o.textContent,
      gamme:o.dataset.gamme, recherche:o.dataset.recherche}));
    const requis = select.required, focus = document.activeElement === select;
    const zone = document.createElement('div'); zone.className = 'depart-recherche';
    const input = document.createElement('input'); input.type = 'text'; input.className = 'form-control';
    input.id = select.id + '-recherche'; input.autocomplete = 'off'; input.placeholder = 'Véhicule, numéro ou VIP…';
    input.required = requis; input.setAttribute('role', 'combobox'); input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    const filtres = document.createElement('div'); filtres.className = 'depart-filtres';
    const cases = ['VIP','CLASSIQUE'].map(g => {
      const label=document.createElement('label'), c=document.createElement('input');
      c.type='checkbox'; c.checked=true; c.value=g; c.className='form-check-input';
      label.append(c, document.createTextNode(' ' + (g==='VIP'?'VIP':'Classique'))); filtres.append(label); return c;
    });
    const liste=document.createElement('ul'); liste.className='depart-propositions'; liste.id=select.id+'-propositions';
    liste.setAttribute('role','listbox'); liste.hidden=true; input.setAttribute('aria-controls',liste.id);
    const compteur=document.createElement('div'); compteur.className='depart-compteur'; compteur.setAttribute('role','status');
    zone.append(input,filtres,liste,compteur); select.after(zone); select.hidden=true; select.required=false;
    const label=document.querySelector('label[for="'+select.id+'"]'); if(label)label.htmlFor=input.id;
    let resultat=[], actif=-1, selection=options.find(o=>o.value===select.value);
    input.value=selection?selection.label:'';
    function validite(){input.setCustomValidity(select.value || (!requis&&!input.value)?'':'Choisissez un départ dans les propositions.');}
    function fermer(){liste.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');}
    function choisir(o){select.value=o.value;selection=o;input.value=o.label;validite();fermer();select.dispatchEvent(new Event('change',{bubbles:true}));}
    function afficher(){
      const gammes=cases.filter(c=>c.checked).map(c=>c.value);
      resultat=filtrer(options,selection&&input.value===selection.label?'':input.value,gammes);actif=-1;
      liste.replaceChildren();
      resultat.slice(0,20).forEach((o,i)=>{const li=document.createElement('li');li.id=liste.id+'-'+i;li.textContent=o.label;
        li.setAttribute('role','option');li.setAttribute('aria-selected','false');
        li.addEventListener('mousedown',e=>{e.preventDefault();choisir(o);});liste.append(li);});
      compteur.textContent=resultat.length?'('+resultat.length+' départ(s)'+(resultat.length>20?' ; précisez la recherche':'')+')':'Aucun départ : modifiez la recherche ou les filtres.';
      liste.hidden=!resultat.length;input.setAttribute('aria-expanded',String(!liste.hidden));
    }
    input.addEventListener('input',()=>{selection=null;select.value='';select.dispatchEvent(new Event('change',{bubbles:true}));validite();afficher();});
    input.addEventListener('focus',afficher); input.addEventListener('blur',fermer);
    input.addEventListener('keydown',e=>{
      if(['ArrowDown','ArrowUp'].includes(e.key)){
        e.preventDefault();if(liste.hidden)afficher();if(!liste.children.length)return;
        actif=(actif+(e.key==='ArrowDown'?1:-1)+liste.children.length)%liste.children.length;
        [...liste.children].forEach((li,i)=>li.setAttribute('aria-selected',String(i===actif)));
        input.setAttribute('aria-activedescendant',liste.children[actif].id);liste.children[actif].scrollIntoView({block:'nearest'});
      }else if(e.key==='Enter'&&!liste.hidden){
        e.preventDefault();e.stopPropagation();if(actif>=0)choisir(resultat[actif]);else if(resultat.length===1)choisir(resultat[0]);
      }else if(e.key==='Escape'){fermer();e.stopPropagation();}
      else if(e.key==='Tab'&&!select.value&&resultat.length===1){choisir(resultat[0]);}
    });
    cases.forEach(c=>c.addEventListener('change',()=>{
      if(selection&&!cases.some(x=>x.checked&&x.value===selection.gamme)){selection=null;select.value='';input.value='';select.dispatchEvent(new Event('change',{bubbles:true}));}
      validite();afficher();
    }));
    select.addEventListener('change',()=>{const o=options.find(o=>o.value===select.value);if(o){selection=o;input.value=o.label;}validite();});
    validite();if(focus)input.focus();
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={normaliser,filtrer};
  if(typeof document==='undefined')return;
  const demarrer=()=>document.querySelectorAll('select[data-depart-select]').forEach(installer);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',demarrer);else demarrer();
})();
