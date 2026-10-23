/* Barre de menus façon Sage 100c : un clic ouvre un menu, le survol passe d'un menu à l'autre,
   les sous-menus s'ouvrent en cascade, Échap ou un clic extérieur referme. */
(function () {
  const dansFenetre = document.documentElement.classList.contains('dans-fenetre');
  const mdi = () => (!dansFenetre && window.erpFenetres) || null;
  const barre = document.getElementById('barre-menus');
  if (barre) {
    const menus = barre.querySelectorAll('.menu');
    const fermer = () => { barre.classList.remove('active'); menus.forEach(m => m.classList.remove('ouvert')); };
    const ouvrir = menu => { menus.forEach(m => m.classList.toggle('ouvert', m === menu)); barre.classList.add('active'); };
    menus.forEach(menu => {
      const titre = menu.querySelector('.menu-titre');
      titre.addEventListener('click', e => {
        e.stopPropagation();
        menu.classList.contains('ouvert') ? fermer() : ouvrir(menu);
      });
      titre.addEventListener('mouseenter', () => { if (barre.classList.contains('active')) ouvrir(menu); });
    });
    document.addEventListener('click', e => { if (!barre.contains(e.target)) fermer(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') fermer(); });
    barre.querySelectorAll('a.item').forEach(a => a.addEventListener('click', fermer));
  }

  // ------------------------------------------------------------------
  // Commandes d'interface : Fichier, Édition, Fenêtre et barre d'outils
  // ------------------------------------------------------------------
  let dernierChamp = null;   // le clic dans un menu fait perdre le focus : on mémorise le dernier champ
  document.addEventListener('focusin', e => {
    if (e.target.matches('input:not([type=checkbox]):not([type=radio]):not([type=hidden]), textarea')) dernierChamp = e.target;
  });
  const main = () => document.querySelector('main');
  function signaler(message) {
    const zone = document.createElement('div');
    zone.className = 'toast-erp';
    zone.textContent = message;
    document.body.appendChild(zone);
    setTimeout(() => zone.remove(), 2500);
  }
  function lienAvecIcone(icone) {
    const i = main() && main().querySelector(`a > i.${icone}, a.btn > i.${icone}`);
    return i ? i.closest('a') : null;
  }
  function remplacerSelection(champ, texte) {
    const debut = champ.selectionStart ?? champ.value.length, fin = champ.selectionEnd ?? champ.value.length;
    champ.value = champ.value.slice(0, debut) + texte + champ.value.slice(fin);
    champ.selectionStart = champ.selectionEnd = debut + texte.length;
    champ.dispatchEvent(new Event('input', { bubbles: true }));
  }
  const ACTIONS = {
    imprimer: () => window.print(),
    actualiser: () => window.location.reload(),
    fermer: () => {
      if (mdi() && mdi().active()) return mdi().fermer(mdi().active());
      window.close(); window.location.href = '/';
    },
    reorganiser: () => mdi() ? mdi().mosaique() : signaler('Aucune fenêtre à réorganiser.'),
    annuler: () => { if (dernierChamp) { dernierChamp.focus(); document.execCommand('undo'); } },
    couper: () => {
      if (!dernierChamp) return signaler('Sélectionnez du texte dans un champ.');
      const c = dernierChamp, texte = c.value.slice(c.selectionStart, c.selectionEnd);
      navigator.clipboard?.writeText(texte); remplacerSelection(c, ''); c.focus();
    },
    copier: () => {
      const texte = dernierChamp && dernierChamp.selectionStart !== dernierChamp.selectionEnd
        ? dernierChamp.value.slice(dernierChamp.selectionStart, dernierChamp.selectionEnd)
        : String(window.getSelection());
      if (!texte) return signaler('Rien à copier : sélectionnez du texte.');
      navigator.clipboard?.writeText(texte).then(() => signaler('Copié dans le presse-papiers.'));
    },
    coller: () => {
      if (!dernierChamp) return signaler('Cliquez d\'abord dans le champ à compléter.');
      if (!navigator.clipboard?.readText) return signaler('Utilisez Ctrl+V : le navigateur bloque la lecture du presse-papiers.');
      navigator.clipboard.readText().then(t => { remplacerSelection(dernierChamp, t); dernierChamp.focus(); })
        .catch(() => signaler('Utilisez Ctrl+V : accès au presse-papiers refusé.'));
    },
    effacer: () => {
      if (!dernierChamp) return;
      if (dernierChamp.selectionStart !== dernierChamp.selectionEnd) remplacerSelection(dernierChamp, '');
      else { dernierChamp.value = ''; dernierChamp.dispatchEvent(new Event('input', { bubbles: true })); }
      dernierChamp.focus();
    },
    selectionner_tout: () => {
      if (dernierChamp) { dernierChamp.focus(); dernierChamp.select(); return; }
      const plage = document.createRange(); plage.selectNodeContents(main());
      const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(plage);
    },
    ajouter: () => {
      const lien = lienAvecIcone('bi-plus') || lienAvecIcone('bi-plus-square');
      if (lien) window.location.href = lien.href;
      else if (document.getElementById('ajout-ligne')) document.getElementById('ajout-ligne').click();
      else signaler('Aucune création possible depuis cette fenêtre.');
    },
    modifier: () => {
      const lien = lienAvecIcone('bi-pencil');
      if (lien) window.location.href = lien.href; else signaler('Aucune fiche à modifier dans cette fenêtre.');
    },
    rechercher: () => {
      const champ = main().querySelector('input[name=q], input[name=numero], input[type=search], input[type=text]');
      if (champ) { champ.focus(); champ.select(); } else signaler('Pas de zone de recherche dans cette fenêtre.');
    },
    barre_verticale: () => {
      const masquee = document.body.classList.toggle('sans-barre-verticale');
      try { localStorage.setItem('erp-barre-verticale', masquee ? 'masquee' : 'visible'); } catch (e) {}
    },
  };
  try { if (localStorage.getItem('erp-barre-verticale') === 'masquee') document.body.classList.add('sans-barre-verticale'); } catch (e) {}

  window.erpAction = nom => { const action = ACTIONS[nom]; if (action) action(); };
  // Sur le bureau, la barre d'outils et le menu Édition agissent sur la fenêtre active (comme dans Sage)
  const TRANSMISES = ['ajouter', 'modifier', 'rechercher', 'imprimer', 'actualiser', 'couper', 'copier', 'coller', 'effacer',
                      'selectionner_tout', 'annuler'];
  document.querySelectorAll('[data-action]').forEach(el => {
    el.addEventListener('mousedown', e => e.preventDefault());   // garder la sélection du champ actif
    el.addEventListener('click', e => {
      e.preventDefault();
      const active = mdi() && mdi().active();
      if (active && TRANSMISES.includes(el.dataset.action) && active.iframe.contentWindow.erpAction) {
        active.iframe.contentWindow.erpAction(el.dataset.action);
        if (barre) { barre.classList.remove('active'); barre.querySelectorAll('.menu').forEach(m => m.classList.remove('ouvert')); }
        return;
      }
      const action = ACTIONS[el.dataset.action];
      if (action) action();
      if (barre) { barre.classList.remove('active'); barre.querySelectorAll('.menu').forEach(m => m.classList.remove('ouvert')); }
    });
  });

  // ------------------------------------------------------------------
  // Fenêtres ouvertes : chaque page consultée devient un onglet de l'espace de travail
  // ------------------------------------------------------------------
  const zone = document.getElementById('onglets-fenetres');
  if (zone && !dansFenetre) {
    const cle = 'erp-fenetres-' + zone.dataset.module, accueil = zone.dataset.accueil;
    const ici = location.pathname + location.search;
    const titre = (document.getElementById('fenetre-titre').textContent.trim() || document.title.split(' · ')[0]).trim();
    document.getElementById('fenetre-titre').textContent = titre;
    let fenetres = [];
    try { fenetres = JSON.parse(sessionStorage.getItem(cle) || '[]'); } catch (e) {}
    if (location.pathname !== accueil && !document.getElementById('acces-refuse')) {
      // Une même commande rouverte (autres filtres) reprend sa fenêtre au lieu d'en ouvrir une deuxième
      const existante = fenetres.find(f => f.url === ici || f.titre === titre);
      if (existante) existante.url = ici; else fenetres.push({ url: ici, titre });
      fenetres = fenetres.slice(-8);
    }
    const enregistrer = () => { try { sessionStorage.setItem(cle, JSON.stringify(fenetres)); } catch (e) {} };
    enregistrer();
    const fermer = url => {
      fenetres = fenetres.filter(f => f.url !== url); enregistrer();
      if (url === ici) location.href = fenetres.length ? fenetres[fenetres.length - 1].url : accueil;
      else afficher();
    };
    function afficher() {
      zone.innerHTML = '';
      fenetres.forEach(f => {
        const a = document.createElement('a');
        a.className = 'onglet-fenetre' + (f.url === ici ? ' courant' : '');
        a.href = f.url; a.title = f.titre;
        const s = document.createElement('span'); s.textContent = f.titre; a.appendChild(s);
        const x = document.createElement('button'); x.type = 'button'; x.title = 'Fermer'; x.innerHTML = '<i class="bi bi-x"></i>';
        x.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); fermer(f.url); });
        a.appendChild(x); zone.appendChild(a);
      });
    }
    afficher();
    // Déconnexion : les fenêtres ouvertes ne passent pas à l'utilisateur suivant
    document.getElementById('form-logout')?.addEventListener('submit', () => {
      try { Object.keys(sessionStorage).filter(k => k.startsWith('erp-fenetres-')).forEach(k => sessionStorage.removeItem(k)); } catch (e) {}
    });
    // Réduire / Agrandir-Restaurer, comme les fenêtres de Sage (double-clic sur la barre de titre = agrandir)
    const fenetre = document.querySelector('.fenetre');
    const reduire = document.getElementById('fenetre-reduire'), agrandir = document.getElementById('fenetre-agrandir');
    const majAgrandir = () => {
      const oui = document.body.classList.contains('fenetre-agrandie');
      agrandir.title = oui ? 'Restaurer' : 'Agrandir';
      agrandir.innerHTML = oui ? '<i class="bi bi-fullscreen-exit"></i>' : '<i class="bi bi-fullscreen"></i>';
    };
    try { if (localStorage.getItem('erp-fenetre-agrandie') === 'oui') document.body.classList.add('fenetre-agrandie'); } catch (e) {}
    const basculerAgrandir = () => {
      fenetre.classList.remove('reduite');
      const oui = document.body.classList.toggle('fenetre-agrandie');
      try { localStorage.setItem('erp-fenetre-agrandie', oui ? 'oui' : 'non'); } catch (e) {}
      majAgrandir();
    };
    majAgrandir();
    agrandir.addEventListener('click', basculerAgrandir);
    reduire.addEventListener('click', () => {
      const reduite = fenetre.classList.toggle('reduite');
      if (reduite && document.body.classList.contains('fenetre-agrandie')) basculerAgrandir(), fenetre.classList.add('reduite');
      reduire.title = reduite ? 'Restaurer' : 'Réduire';
      reduire.innerHTML = reduite ? '<i class="bi bi-window"></i>' : '<i class="bi bi-dash-lg"></i>';
    });
    document.querySelector('.fenetre-titre').addEventListener('dblclick', e => {
      if (!e.target.closest('.fenetre-boutons')) fenetre.classList.contains('reduite') ? reduire.click() : basculerAgrandir();
    });
    const bouton = document.getElementById('fenetre-fermer');
    if (bouton && location.pathname !== accueil) bouton.addEventListener('click', e => { e.preventDefault(); fermer(ici); });
    else if (bouton) bouton.hidden = true;
  }

  // Barre de navigation : choix du menu affiché
  const choix = document.getElementById('arbre-choix');
  if (choix) choix.addEventListener('change', () => {
    document.querySelectorAll('.arbre-menu').forEach(div => { div.hidden = div.dataset.menu !== choix.value; });
  });

  // ------------------------------------------------------------------
  // Page affichée dans une fenêtre interne du bureau
  // ------------------------------------------------------------------
  if (dansFenetre && window.parent.erpFenetres) {
    const parent = window.parent.erpFenetres, cadre = window.frameElement;
    const accueils = (window.ERP_MDI && window.ERP_MDI.accueils) || [];
    if (accueils.includes(location.pathname)) { window.top.location.href = location.href; return; }
    document.addEventListener('click', e => {
      const a = e.target.closest('a[href]');
      if (!a) return;
      if (a.getAttribute('href').startsWith('javascript:history.back')) {   // Annuler / Retour : revient en arrière ou ferme
        e.preventDefault(); parent.retour(cadre); return;
      }
      const url = new URL(a.href, location.href);
      if (url.origin === location.origin && (accueils.includes(url.pathname) || url.pathname === '/')) a.target = '_top';
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') parent.echap(cadre); });
    document.addEventListener('mousedown', () => parent.activerCadre(cadre), true);
  }
})();
