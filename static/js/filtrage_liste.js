// Filtrage progressif des champs liste (façon Sage) : en tapant dans un champ
// déroulant, la liste se réduit aux lignes qui contiennent le texte saisi
// (accents et casse ignorés). Le <select> d'origine reste la source de vérité
// (valeur envoyée au serveur) ; on l'habille d'un champ de recherche.
(function () {
  'use strict';
  var SEUIL = 6; // en dessous, le déroulant natif suffit (oui/non, quelques choix)

  function sansAccent(s) {
    return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function options(sel) {
    return Array.prototype.map.call(sel.options, function (o, i) {
      return { i: i, val: o.value, txt: o.text, rech: sansAccent(o.text) };
    });
  }

  function habiller(sel) {
    if (sel.dataset.combo || sel.multiple || sel.disabled) return;
    if (sel.options.length < SEUIL) return;
    if (sel.closest('[data-no-combo]')) return;
    // Champs déjà pourvus de leur propre recherche (ex. sélection de départ).
    if (sel.matches('[data-depart-select], [data-recherche], [data-no-combo]')) return;
    sel.dataset.combo = '1';
    sel.classList.add('combo-select-cache');

    var wrap = document.createElement('span');
    wrap.className = 'combo';
    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control combo-input';
    input.autocomplete = 'off';
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-expanded', 'false');
    var menu = document.createElement('ul');
    menu.className = 'combo-menu';
    menu.hidden = true;

    function libelleCourant() {
      var o = sel.options[sel.selectedIndex];
      return (o && sel.selectedIndex > -1 && o.value !== '') ? o.text : '';
    }
    input.value = libelleCourant();
    input.placeholder = libelleCourant() || (sel.options[0] ? sel.options[0].text : '');

    var liste = options(sel);
    var actif = -1;

    function fermer() {
      menu.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      actif = -1;
    }

    function choisir(val, txt) {
      sel.value = val;
      input.value = (val === '') ? '' : txt;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      fermer();
    }

    function construire(filtre) {
      var f = sansAccent(filtre);
      menu.innerHTML = '';
      var n = 0;
      liste.forEach(function (o) {
        if (f && o.rech.indexOf(f) === -1) return;
        var li = document.createElement('li');
        li.className = 'combo-item';
        li.textContent = o.txt || '—';
        li.dataset.val = o.val;
        if (o.val === sel.value) li.setAttribute('aria-selected', 'true');
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          choisir(o.val, o.txt);
        });
        menu.appendChild(li);
        n++;
      });
      if (!n) {
        var vide = document.createElement('li');
        vide.className = 'combo-vide';
        vide.textContent = 'Aucun résultat';
        menu.appendChild(vide);
      }
      menu.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      actif = -1;
    }

    function surligner(delta) {
      var items = menu.querySelectorAll('.combo-item');
      if (!items.length) return;
      if (menu.hidden) construire('');
      actif = (actif + delta + items.length) % items.length;
      items.forEach(function (it, k) { it.classList.toggle('actif', k === actif); });
      items[actif].scrollIntoView({ block: 'nearest' });
    }

    input.addEventListener('focus', function () { construire(''); input.select(); });
    input.addEventListener('input', function () { construire(input.value); });
    input.addEventListener('blur', function () {
      // On restaure le libellé réel si la saisie n'a pas abouti à un choix.
      setTimeout(function () { input.value = libelleCourant(); fermer(); }, 120);
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); surligner(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); surligner(-1); }
      else if (e.key === 'Enter') {
        var it = menu.querySelector('.combo-item.actif') || menu.querySelector('.combo-item');
        if (!menu.hidden && it) { e.preventDefault(); choisir(it.dataset.val, it.textContent); }
      } else if (e.key === 'Escape') { fermer(); }
    });

    sel.after(wrap);
    wrap.appendChild(input);
    wrap.appendChild(menu);
    // Si la valeur du <select> change par programme (contrepartie auto, etc.),
    // on met le libellé à jour.
    sel.addEventListener('change', function () {
      liste = options(sel);
      if (document.activeElement !== input) input.value = libelleCourant();
    });
  }

  function balayer(racine) {
    (racine || document).querySelectorAll('select').forEach(habiller);
  }
  // Exposé pour les écrans qui ajoutent des lignes (saisie d'écriture).
  window.ERP_filtrage_liste = balayer;

  document.addEventListener('DOMContentLoaded', function () { balayer(document); });
  if (document.readyState !== 'loading') balayer(document);
})();
