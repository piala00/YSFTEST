// Régression des commandes génériques du bureau et des fenêtres de documents.
// Lancer : node tests_js/test_menus_actions.js (Node 18+)
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '../static/js/menus.js'), 'utf8');

function contexte(clipboard) {
  const ecouteurs = {}, messages = [], cibles = {}, compteurs = { impression: 0 };
  const champ = {
    value: 'ABCDE', selectionStart: 1, selectionEnd: 3,
    readOnly: false, disabled: false,
    matches: () => true,
    focus() { this.focuses = (this.focuses || 0) + 1; },
    setSelectionRange(debut, fin) { this.selectionStart = debut; this.selectionEnd = fin; },
    dispatchEvent() { this.evenements = (this.evenements || 0) + 1; },
  };
  const principale = { querySelector: selecteur => cibles[selecteur] || null };
  const document = {
    documentElement: { classList: { contains: () => false } },
    body: { appendChild: el => messages.push(el), classList: { add() {}, toggle: () => false } },
    getElementById: () => null,
    querySelector: selecteur => selecteur === 'main' ? principale : null,
    querySelectorAll: () => [],
    createElement: () => ({ textContent: '', remove() {} }),
    addEventListener: (nom, gestionnaire) => { ecouteurs[nom] = gestionnaire; },
  };
  const window = { location: { href: '' }, getSelection: () => '',
    print: () => { compteurs.impression++; } };
  const contexte = {
    document, window, navigator: { clipboard }, console, URL,
    localStorage: { getItem: () => null },
    setTimeout: () => {}, Event: class { constructor(nom) { this.type = nom; } },
  };
  vm.runInNewContext(source, contexte, { filename: 'menus.js' });
  ecouteurs.focusin({ target: champ });
  const action = nom => window.erpAction(nom);
  const message = () => messages.at(-1)?.textContent || '';
  return { champ, cibles, compteurs, action, message };
}

const attendre = () => new Promise(resolve => setImmediate(resolve));

(async () => {
  let total = 0;
  const controler = (titre, action) => {
    action(); total++; console.log('OK : ' + titre);
  };
  {
    const env = contexte(undefined);
    env.action('copier'); await attendre();
    controler('copier sans presse-papiers préserve le texte', () => {
      assert.equal(env.champ.value, 'ABCDE');
      assert.match(env.message(), /indisponible/);
    });
  }
  {
    const env = contexte({ writeText: () => Promise.reject(new Error('refus')) });
    env.action('copier'); await attendre();
    controler('copier refusé donne une erreur contrôlée', () => assert.match(env.message(), /refusé/));
  }
  {
    let copie = '';
    const env = contexte({ writeText: texte => { copie = texte; return Promise.resolve(); } });
    env.action('copier'); await attendre();
    controler('copier utilise la sélection exacte', () => {
      assert.equal(copie, 'BC');
      assert.equal(env.champ.value, 'ABCDE');
    });
  }
  {
    const env = contexte({ readText: () => Promise.resolve('Z') });
    env.champ.readOnly = true; env.action('coller'); await attendre();
    controler('coller refuse un champ protégé', () => {
      assert.equal(env.champ.value, 'ABCDE');
      assert.match(env.message(), /protégé/);
    });
  }
  {
    const env = contexte({ readText: () => Promise.resolve('Z') });
    env.action('coller'); await attendre();
    controler('coller remplace seulement la sélection et émet input', () => {
      assert.equal(env.champ.value, 'AZDE');
      assert.equal(env.champ.evenements, 1);
    });
  }
  {
    let terminer;
    const env = contexte({ readText: () => new Promise(resolve => { terminer = resolve; }) });
    env.action('coller'); await attendre();
    env.champ.value = 'modifié';
    terminer('Z'); await attendre();
    controler('coller tardif ne détruit pas la saisie récente', () => {
      assert.equal(env.champ.value, 'modifié');
      assert.match(env.message(), /changé/);
    });
  }
  {
    const env = contexte(undefined);
    env.champ.disabled = true;
    env.action('effacer');
    controler('effacer refuse les champs désactivés', () => {
      assert.equal(env.champ.value, 'ABCDE');
      assert.match(env.message(), /protégé/);
    });
  }
  {
    const env = contexte(undefined);
    env.action('effacer');
    controler('effacer supprime seulement la sélection', () => assert.equal(env.champ.value, 'ADE'));
  }
  {
    const env = contexte(undefined);
    let appels = 0;
    env.cibles['[data-erp-action="modifier"]'] = {
      disabled: false, getAttribute: () => null, click: () => { appels++; },
    };
    env.action('modifier');
    controler('modifier cible la commande explicite de la fenêtre', () => assert.equal(appels, 1));
  }
  {
    const env = contexte(undefined);
    let appels = 0;
    env.cibles['[data-erp-action="ajouter"]'] = {
      disabled: false, getAttribute: () => null, click: () => { appels++; },
    };
    env.action('ajouter');
    controler('ajouter ouvre le choix du type dans la fenêtre', () => assert.equal(appels, 1));
  }
  {
    const env = contexte(undefined);
    env.cibles['[data-erp-action="imprimer"]'] = { disabled: true, getAttribute: () => null, click: () => { throw Error('Ne doit pas imprimer'); } };
    env.action('imprimer');
    controler('imprimer exige la sélection dans une liste', () => {
      assert.equal(env.compteurs.impression, 0);
      assert.match(env.message(), /Sélectionnez/);
    });
  }
  {
    const liste = fs.readFileSync(path.resolve(__dirname, '../templates/commercial/document_list.html'), 'utf8');
    const detail = fs.readFileSync(path.resolve(__dirname, '../templates/commercial/document_detail.html'), 'utf8');
    controler('les fenêtres exposent les actions explicites', () => {
      assert.match(liste, /data-erp-action="ajouter"/);
      assert.match(liste, /data-erp-action="modifier"/);
      assert.match(liste, /data-erp-action="imprimer"/);
      assert.match(liste, /dataset\.modifiable !== '1'/);
      assert.match(detail, /data-erp-action="modifier"/);
      assert.match(detail, /data-erp-action="imprimer"/);
    });
  }
  {
    const ecrans = [
      ['commercial/article_list.html', 'ajouter'],
      ['commercial/article_detail.html', 'modifier'],
      ['commercial/tiers_list.html', 'ajouter'],
      ['commercial/tiers_detail.html', 'modifier'],
      ['comptabilite/ecriture_list.html', 'ajouter'],
      ['comptabilite/journal_list.html', 'ajouter'],
      ['transport/billets.html', 'ajouter'],
      ['transport/departs.html', 'ajouter'],
    ];
    controler('huit fenêtres commerciales, comptables et transport ont leur action explicite', () => {
      for (const [fichier, action] of ecrans) {
        const template = fs.readFileSync(path.resolve(__dirname, '../templates', fichier), 'utf8');
        assert.ok(template.includes('data-erp-action="' + action + '"'), fichier + ' : ' + action);
      }
    });
  }

  {
    const saisie = fs.readFileSync(path.resolve(__dirname, '../templates/commercial/document_form.html'), 'utf8');
    const debut = '<script>\n(function commandesSaisieDocument() {';
    const d = saisie.indexOf(debut), f = saisie.indexOf('</script>', d);
    const script = saisie.slice(d + '<script>\n'.length, f);
    controler('nouvelle saisie : actions Fn, Informations et Pied réellement actives', () => {
      assert.ok(d >= 0 && f > d, 'Script des commandes de saisie');
      for (const id of ['doc-form-fonctions','doc-form-informations','doc-form-pied',
                        'doc-form-panneau-infos','piece-pied']) assert.ok(saisie.includes('id="' + id + '"'), id);
      assert.match(saisie, /data-doc-form-action="brouillon"/);
      assert.match(saisie, /data-doc-form-action="valider"/);
      assert.match(saisie, /data-doc-form-action="ajouter"/);
    });
    const ecouteurs = {};
    const element = id => ({
      id, hidden: id === 'doc-form-panneau-infos',
      attrs: {}, clicks: 0,
      addEventListener(evt, cb) { this[evt] = cb; },
      setAttribute(k, v) { this.attrs[k] = v; },
      click() { this.clicks++; },
      focus() { this.focuses = (this.focuses || 0) + 1; },
      scrollIntoView() { this.scrolls = (this.scrolls || 0) + 1; },
    });
    for (const id of ['doc-form-fonctions','doc-form-informations','doc-form-pied',
                      'doc-form-panneau-infos','piece-pied','ajout-ligne'])
      ecouteurs[id] = element(id);
    const enregistrer = element('enregistrer'), valider = element('valider');
    const actions = ['brouillon','valider','ajouter'].map(n => {
      const el = element(n); el.dataset = { docFormAction: n }; return el;
    });
    const formulaire = { querySelector(q) {
      return q === 'button[name="brouillon"]' ? enregistrer :
        q === 'button[name="valider"]' ? valider : null;
    } };
    ecouteurs['doc-form'] = formulaire;
    vm.runInNewContext(script, { document: {
      getElementById: id => ecouteurs[id],
      querySelectorAll: q => q === '[data-doc-form-action]' ? actions : [],
    }, console }, { filename: 'document_form.actions.js' });
    const info = ecouteurs['doc-form-informations'], panneau = ecouteurs['doc-form-panneau-infos'];
    info.click = info['click'];
    info.click();
    controler('Informations ouvre le panneau et met à jour aria-expanded', () => {
      assert.equal(panneau.hidden, false);
      assert.equal(info.attrs['aria-expanded'], 'true');
    });
    info.click();
    controler('Informations referme le panneau', () => {
      assert.equal(panneau.hidden, true);
      assert.equal(info.attrs['aria-expanded'], 'false');
    });
    ecouteurs['doc-form-pied'].click();
    controler('Pied déplace le focus sur les totaux', () => {
      assert.equal(ecouteurs['piece-pied'].focuses, 1);
      assert.equal(ecouteurs['piece-pied'].scrolls, 1);
    });
    actions[0]['click']();
    controler('Fonctions Enregistrer réutilise le bouton brouillon existant', () => assert.equal(enregistrer.clicks, 1));
    actions[1]['click']();
    controler('Fonctions Valider délègue au bouton à confirmation existant', () => assert.equal(valider.clicks, 1));
    actions[2]['click']();
    controler('Fonctions Ajouter délègue à ajout-ligne existant', () => assert.equal(ecouteurs['ajout-ligne'].clicks, 1));
    valider.disabled = true;
    actions[1]['click']();
    controler('Fonctions n’active pas les boutons désactivés', () => assert.equal(valider.clicks, 1));
  }
  console.log(total + ' contrôles OK');
})().catch(e => { console.error(e); process.exitCode = 1; });
