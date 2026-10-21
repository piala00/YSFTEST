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

  // Commandes d'interface (Fichier › Imprimer, Fermer)
  document.querySelectorAll('[data-action]').forEach(el => el.addEventListener('click', e => {
    e.preventDefault();
    if (el.dataset.action === 'imprimer') window.print();
    if (el.dataset.action === 'actualiser') window.location.reload();
    if (el.dataset.action === 'fermer') { window.close(); window.location.href = '/'; }
  }));

  // Barre de navigation : choix du menu affiché
  const choix = document.getElementById('arbre-choix');
  if (choix) choix.addEventListener('change', () => {
    document.querySelectorAll('.arbre-menu').forEach(div => { div.hidden = div.dataset.menu !== choix.value; });
  });
})();
