/* Barre de menus façon Sage 100c : un clic ouvre un menu, le survol passe d'un menu à l'autre,
   les sous-menus s'ouvrent en cascade, Échap ou un clic extérieur referme. */
(function () {
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
    fermer: () => { window.close(); window.location.href = '/'; },
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

  document.querySelectorAll('[data-action]').forEach(el => {
    el.addEventListener('mousedown', e => e.preventDefault());   // garder la sélection du champ actif
    el.addEventListener('click', e => {
      e.preventDefault();
      const action = ACTIONS[el.dataset.action];
      if (action) action();
      if (barre) { barre.classList.remove('active'); barre.querySelectorAll('.menu').forEach(m => m.classList.remove('ouvert')); }
    });
  });

  // Barre de navigation : choix du menu affiché
  const choix = document.getElementById('arbre-choix');
  if (choix) choix.addEventListener('change', () => {
    document.querySelectorAll('.arbre-menu').forEach(div => { div.hidden = div.dataset.menu !== choix.value; });
  });
})();
