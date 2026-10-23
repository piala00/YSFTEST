/* Bureau façon Sage 100 V12 : l'écran d'accueil reste au fond et chaque commande s'ouvre dans une fenêtre
   interne que l'on peut déplacer, étirer par ses bords, réduire, agrandir et fermer. Plusieurs fenêtres
   (documents des ventes, documents des achats…) peuvent être ouvertes et placées côte à côte.
   Les boîtes de dialogue (fenêtre de sélection d'un état) gardent la taille de leur contenu, sans
   redimensionnement, comme dans Sage. */
(function () {
  const mdi = window.ERP_MDI, zone = document.getElementById('fenetres-mdi'), barreReduites = document.getElementById('fenetres-reduites');
  const espace = document.querySelector('main.mdi');
  if (!mdi || !zone || !espace) return;
  const cle = 'erp-mdi-' + mdi.module;
  const TITRE = 30, MIN_L = 280, MIN_H = 160;
  let fenetres = [], zMax = 10, compteur = 0;

  const lire = () => { try { return JSON.parse(sessionStorage.getItem(cle) || '[]'); } catch (e) { return []; } };
  const enregistrer = () => {
    try {
      sessionStorage.setItem(cle, JSON.stringify(fenetres.map(f => ({
        url: f.url, titre: f.titre, x: f.x, y: f.y, l: f.l, h: f.h, etat: f.etat, z: f.z, dialogue: f.dialogue, ajustee: f.ajustee }))));
    } catch (e) {}
  };
  const surface = () => ({ l: espace.clientWidth, h: espace.clientHeight - (barreReduites.offsetHeight || 0) });

  // ------------------------------------------------------------------ création
  function creer(etat) {
    const f = Object.assign({ etat: 'normale', dialogue: false, ajustee: false, chargements: 0 }, etat);
    f.id = ++compteur;
    f.el = document.createElement('section');
    f.el.className = 'fenetre-mdi';
    f.el.innerHTML = `
      <div class="mdi-titre"><i class="bi bi-window"></i><span class="mdi-libelle"></span>
        <span class="mdi-boutons">
          <button type="button" data-cmd="reduire" title="Réduire"><i class="bi bi-dash-lg"></i></button>
          <button type="button" data-cmd="agrandir" title="Agrandir"><i class="bi bi-square"></i></button>
          <button type="button" data-cmd="fermer" class="mdi-fermer" title="Fermer"><i class="bi bi-x-lg"></i></button>
        </span></div>
      <div class="mdi-corps"><iframe title="Fenêtre"></iframe></div>
      ${['n', 's', 'e', 'o', 'ne', 'no', 'se', 'so'].map(b => `<div class="mdi-bord mdi-${b}" data-bord="${b}"></div>`).join('')}`;
    f.iframe = f.el.querySelector('iframe');
    f.libelle = f.el.querySelector('.mdi-libelle');
    f.libelle.textContent = f.titre || 'Chargement…';
    zone.appendChild(f.el);
    brancher(f);
    f.iframe.src = f.url;
    fenetres.push(f);
    placer(f);
    return f;
  }

  function placer(f) {
    const s = surface(), el = f.el;
    el.classList.toggle('dialogue', f.dialogue);
    el.classList.toggle('agrandie', f.etat === 'agrandie');
    el.hidden = f.etat === 'reduite';
    if (f.etat === 'agrandie') {
      Object.assign(el.style, { left: '0px', top: '0px', width: s.l + 'px', height: s.h + 'px' });
    } else {
      f.l = Math.max(MIN_L, Math.min(f.l, s.l)); f.h = Math.max(MIN_H, Math.min(f.h, s.h));
      f.x = Math.max(0, Math.min(f.x, s.l - 80)); f.y = Math.max(0, Math.min(f.y, s.h - TITRE));
      Object.assign(el.style, { left: f.x + 'px', top: f.y + 'px', width: f.l + 'px', height: f.h + 'px' });
    }
    el.style.zIndex = f.z;
    const bouton = el.querySelector('[data-cmd=agrandir]');
    bouton.title = f.etat === 'agrandie' ? 'Restaurer' : 'Agrandir';
    bouton.innerHTML = f.etat === 'agrandie' ? '<i class="bi bi-window-stack"></i>' : '<i class="bi bi-square"></i>';
    afficherReduites();
  }

  // Taille et position par défaut : en cascade, comme les fenêtres filles de Sage
  function positionDefaut() {
    const s = surface(), n = fenetres.filter(f => f.etat !== 'reduite').length % 8;
    const l = Math.min(Math.max(640, Math.round(s.l * 0.72)), s.l), h = Math.min(Math.max(380, Math.round(s.h * 0.78)), s.h);
    return { x: 16 + n * 26, y: 10 + n * 26, l, h };
  }

  // ------------------------------------------------------------------ activation (premier plan)
  function activer(f) {
    if (!f) return;
    if (f.z !== zMax) f.z = ++zMax;
    fenetres.forEach(g => g.el.classList.toggle('active', g === f));
    f.el.style.zIndex = f.z;
    enregistrer();
  }
  const active = () => fenetres.filter(f => f.etat !== 'reduite').sort((a, b) => b.z - a.z)[0] || null;

  // ------------------------------------------------------------------ commandes de la barre de titre
  function reduire(f) { f.etat = 'reduite'; placer(f); activer(active()); enregistrer(); }
  function basculerAgrandir(f) {
    if (f.dialogue) return;
    f.etat = f.etat === 'agrandie' ? 'normale' : 'agrandie'; placer(f); activer(f); enregistrer();
  }
  function restaurer(f) { f.etat = f.etat === 'reduite' ? (f.avantReduction || 'normale') : f.etat; placer(f); activer(f); enregistrer(); }
  function fermer(f) {
    fenetres = fenetres.filter(g => g !== f); f.el.remove(); afficherReduites(); activer(active()); enregistrer();
  }

  function afficherReduites() {
    barreReduites.innerHTML = '';
    fenetres.filter(f => f.etat === 'reduite').forEach(f => {
      const b = document.createElement('div');
      b.className = 'mdi-reduite';
      b.innerHTML = '<span></span><button type="button" title="Restaurer"><i class="bi bi-window"></i></button>' +
        '<button type="button" title="Agrandir"><i class="bi bi-square"></i></button><button type="button" class="mdi-fermer" title="Fermer"><i class="bi bi-x-lg"></i></button>';
      b.querySelector('span').textContent = f.titre;
      const [r, a, x] = b.querySelectorAll('button');
      b.querySelector('span').addEventListener('click', () => restaurer(f));
      r.addEventListener('click', () => restaurer(f));
      a.addEventListener('click', () => { f.etat = 'agrandie'; placer(f); activer(f); enregistrer(); });
      x.addEventListener('click', () => fermer(f));
      barreReduites.appendChild(b);
    });
    barreReduites.hidden = !barreReduites.children.length;
  }

  // ------------------------------------------------------------------ déplacer, étirer
  function glisser(e, f, deplacer) {
    if (e.button !== 0) return;
    e.preventDefault();
    activer(f);
    const depart = { x: e.clientX, y: e.clientY, fx: f.x, fy: f.y, l: f.l, h: f.h }, bord = deplacer ? '' : e.target.dataset.bord;
    document.body.classList.add('mdi-glisse');
    const bouger = ev => {
      const dx = ev.clientX - depart.x, dy = ev.clientY - depart.y, s = surface();
      if (deplacer) { f.x = depart.fx + dx; f.y = depart.fy + dy; }
      else {
        if (bord.includes('e')) f.l = Math.max(MIN_L, depart.l + dx);
        if (bord.includes('s')) f.h = Math.max(MIN_H, depart.h + dy);
        if (bord.includes('o')) { const l = Math.max(MIN_L, depart.l - dx); f.x = depart.fx + depart.l - l; f.l = l; }
        if (bord.includes('n')) { const h = Math.max(MIN_H, depart.h - dy); f.y = depart.fy + depart.h - h; f.h = h; }
        f.x = Math.max(0, f.x); f.y = Math.max(0, f.y); f.l = Math.min(f.l, s.l - f.x); f.h = Math.min(f.h, s.h - f.y);
      }
      f.ajustee = true;
      placer(f);
    };
    const lacher = () => {
      document.removeEventListener('pointermove', bouger); document.removeEventListener('pointerup', lacher);
      document.body.classList.remove('mdi-glisse'); enregistrer();
    };
    document.addEventListener('pointermove', bouger); document.addEventListener('pointerup', lacher);
  }

  function brancher(f) {
    const titre = f.el.querySelector('.mdi-titre');
    titre.addEventListener('pointerdown', e => {
      if (e.target.closest('.mdi-boutons')) return;
      if (f.etat === 'agrandie') { activer(f); return; }
      glisser(e, f, true);
    });
    titre.addEventListener('dblclick', e => { if (!e.target.closest('.mdi-boutons')) basculerAgrandir(f); });
    f.el.querySelectorAll('.mdi-bord').forEach(b => b.addEventListener('pointerdown', e => {
      if (f.etat !== 'agrandie' && !f.dialogue) glisser(e, f, false);
    }));
    f.el.addEventListener('pointerdown', () => activer(f));
    f.el.querySelector('[data-cmd=reduire]').addEventListener('click', () => { f.avantReduction = f.etat; reduire(f); });
    f.el.querySelector('[data-cmd=agrandir]').addEventListener('click', () => basculerAgrandir(f));
    f.el.querySelector('[data-cmd=fermer]').addEventListener('click', () => fermer(f));
    f.iframe.addEventListener('load', () => charge(f));
  }

  // ------------------------------------------------------------------ contenu chargé dans la fenêtre
  function charge(f) {
    let doc;
    try { doc = f.iframe.contentDocument; } catch (e) { return; }
    if (!doc || !doc.body) return;
    f.chargements += 1;
    const loc = f.iframe.contentWindow.location;
    f.url = loc.pathname + loc.search;
    f.titre = (doc.title || '').split(' · ')[0].trim() || f.titre;
    f.libelle.textContent = f.titre;
    f.libelle.title = f.titre;
    const boite = doc.getElementById('fenetre-selection');
    if (boite) {
      // Boîte de dialogue : taille de son contenu, centrée, ni étirée ni agrandie (comme « Mouvements de stock »)
      f.dialogue = true;
      if (f.etat === 'agrandie') f.etat = 'normale';
      const s = surface();
      f.l = Math.min(Math.ceil(boite.offsetWidth) + 18, s.l);
      f.h = Math.min(Math.ceil(boite.offsetHeight) + TITRE + 6, s.h);
      f.x = Math.round((s.l - f.l) / 2); f.y = Math.max(0, Math.round((s.h - f.h) / 3));
    } else if (f.dialogue) {
      // La sélection est validée : le résultat de l'état s'affiche dans une fenêtre normale
      f.dialogue = false;
      if (!f.ajustee) Object.assign(f, positionDefaut());
    }
    placer(f); activer(f); enregistrer();
  }

  // ------------------------------------------------------------------ ouverture
  function ouvrir(url) {
    const chemin = new URL(url, location.href);
    const cible = chemin.pathname + chemin.search;
    const existante = fenetres.find(f => f.url === cible);
    if (existante) { if (existante.etat === 'reduite') restaurer(existante); else activer(existante); return existante; }
    const f = creer(Object.assign({ url: cible, titre: '' }, positionDefaut(), { z: ++zMax }));
    if (window.innerWidth < 768) { f.etat = 'agrandie'; placer(f); }
    activer(f);
    return f;
  }

  // Liens des menus, de la barre verticale et des tuiles de l'accueil : ouverture dans une fenêtre
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href]');
    if (!a || e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    if (!a.closest('#barre-menus, .arbre, #bureau, .barre-outils')) return;
    if (a.target || a.hasAttribute('download') || a.getAttribute('href').startsWith('#') || a.getAttribute('href').startsWith('javascript')) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || mdi.accueils.includes(url.pathname) || url.pathname === '/'
        || /^\/(admin|static|deconnexion|connexion)\b/.test(url.pathname)) return;
    e.preventDefault();
    ouvrir(url.href);
  }, true);

  // Fenêtre › Réorganiser : mosaïque des fenêtres ouvertes (côte à côte)
  function mosaique() {
    const visibles = fenetres.filter(f => f.etat !== 'reduite' && !f.dialogue);
    if (!visibles.length) return;
    const s = surface(), colonnes = Math.ceil(Math.sqrt(visibles.length)), lignes = Math.ceil(visibles.length / colonnes);
    const l = Math.floor(s.l / colonnes), h = Math.floor(s.h / lignes);
    visibles.forEach((f, i) => {
      Object.assign(f, { etat: 'normale', x: (i % colonnes) * l, y: Math.floor(i / colonnes) * h, l, h, ajustee: true });
      placer(f);
    });
    enregistrer();
  }

  // Interface pour les pages affichées dans les fenêtres (menus.js) et pour la barre d'outils
  const parCadre = cadre => fenetres.find(f => f.iframe === cadre);
  window.erpFenetres = {
    ouvrir, mosaique,
    active: () => active(),
    fermer: f => fermer(f),
    activerCadre: cadre => activer(parCadre(cadre)),
    retour: cadre => {
      const f = parCadre(cadre);
      if (!f) return;
      if (f.chargements > 1 && !f.dialogue) f.iframe.contentWindow.history.back(); else fermer(f);
    },
    echap: cadre => { const f = parCadre(cadre); if (f && f.dialogue) fermer(f); },
  };
  // Un clic dans une fenêtre (iframe) ne remonte pas jusqu'ici : on suit le focus pour la mettre au premier plan
  window.addEventListener('blur', () => setTimeout(() => {
    const f = parCadre(document.activeElement);
    if (f) activer(f);
  }));
  window.addEventListener('resize', () => fenetres.forEach(placer));
  document.getElementById('form-logout')?.addEventListener('submit', () => {
    try { Object.keys(sessionStorage).filter(k => k.startsWith('erp-mdi-')).forEach(k => sessionStorage.removeItem(k)); } catch (e) {}
  });

  // ------------------------------------------------------------------ restauration après actualisation
  lire().sort((a, b) => a.z - b.z).forEach(etat => { zMax = Math.max(zMax, etat.z || 0); creer(etat); });
  activer(active());
  try {
    const attente = sessionStorage.getItem('erp-mdi-ouvrir-' + mdi.module);
    if (attente) { sessionStorage.removeItem('erp-mdi-ouvrir-' + mdi.module); ouvrir(attente); }
  } catch (e) {}
  afficherReduites();
})();
