// Régression de l'interface Actions des 21 familles de pièces (template partagé).
// Exécuter : node tests_js/test_document_actions.js
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const listing = fs.readFileSync(path.resolve(__dirname, '../templates/commercial/document_list.html'), 'utf8');
const detail = fs.readFileSync(path.resolve(__dirname, '../templates/commercial/document_detail.html'), 'utf8');
const mark = '{% block scripts %}<script>';
const start = listing.indexOf(mark), end = listing.indexOf('</script>', start);
assert(start >= 0 && end > start, 'Script de la liste introuvable');
const script = listing.slice(start + mark.length, end);

function prepare() {
  const boutons = {};
  for (const nom of ['ouvrir', 'modifier', 'valider', 'transformer', 'reglement',
                     'acompte', 'ecriture', 'imprimer', 'annuler', 'fermer']) {
    boutons[nom] = { disabled: true, click: null,
      addEventListener(nomEvenement, cb) { this[nomEvenement] = cb; } };
  }
  const lignes = [
    { dataset: { url: '/piece/1/', modifiable: '1', modifier: '/piece/1/modifier/',
       valider: '/piece/1/valider/', annuler: '/piece/1/annuler/',
       imprimer: '/piece/1/imprimer/', transformer: '0', reglement: '', acompte: '', ecriture: '' } },
    { dataset: { url: '/piece/2/', modifiable: '0', modifier: '/piece/2/modifier/',
       valider: '/piece/2/valider/', annuler: '/piece/2/annuler/',
       imprimer: '/piece/2/imprimer/', transformer: '1',
       reglement: '/reglements/nouveau/?document=2', acompte: '',
       ecriture: '/comptabilite/ecriture/2/' } },
    { dataset: { url: '/piece/3/', modifiable: '0', modifier: '/piece/3/modifier/',
       valider: '/piece/3/valider/', annuler: '/piece/3/annuler/',
       imprimer: '/piece/3/imprimer/', transformer: '1', reglement: '',
       acompte: '/reglements/nouveau/?commande=3', ecriture: '' } },
  ].map(row => Object.assign(row, {
    listeners: {}, attrs: {},
    classList: { add() {}, remove() {} },
    setAttribute(k, v) { this.attrs[k] = v; },
    addEventListener(k, cb) { this.listeners[k] = cb; },
  }));
  const forms = {
    'form-valider': { action: '', submissions: 0, submit() { this.submissions++; } },
    'form-annuler': { action: '', submissions: 0, submit() { this.submissions++; } },
  };
  const filtres = { hidden: true, querySelector: () => ({focus() {}}) };
  const elements = {
    grille: { querySelectorAll(sel) {
      return sel === 'tbody tr[data-url]' ? lignes : [];
    } },
    'liste-etat': { dataset: { total: '3' }, textContent: '' },
    'liste-criteres': filtres, 'plus-criteres': { addEventListener() {} },
    'liste-filtrer': { addEventListener() {} },
    ...forms,
  };
  const location = { href: '' };
  const window = { location, openCalls: [], open(url, target) {
    this.openCalls.push({url, target});
  } };
  window.parent = window;
  const env = { document: {
    getElementById: id => elements[id],
    querySelector(sel) {
      const match = sel.match(/^\[data-liste="([^"]+)"\]$/);
      return match ? boutons[match[1]] : null;
    } },
    window, location, history: { back() {} }, confirm: () => true, console };
  vm.runInNewContext(script, env, { filename: 'document_list.inline.js' });
  return { boutons, lignes, forms, window, filtres,
    confirmer: fn => { env.confirm = fn; },
    choisir: i => lignes[i].listeners.click(),
    cliquer: nom => boutons[nom].click(),
  };
}
let n = 0;
const ok = (lib, f) => { f(); n++; console.log('OK : ' + lib); };

const s = prepare();
ok('aucun bouton métier actif sans sélection', () => {
  for (const nom of ['modifier','valider','transformer','reglement','acompte','ecriture','annuler']) {
    assert.equal(s.boutons[nom].disabled, true, nom);
  }
});
s.choisir(0);
ok('brouillon : modifier/valider/annuler seulement', () => {
  for (const nom of ['modifier','valider','annuler']) assert.equal(s.boutons[nom].disabled,false,nom);
  for (const nom of ['transformer','reglement','acompte','ecriture']) assert.equal(s.boutons[nom].disabled,true,nom);
});
s.cliquer('modifier');
ok('modifier ouvre le brouillon choisi', () => assert.equal(s.window.location.href, '/piece/1/modifier/'));
s.confirmer(() => false);
s.cliquer('valider');
ok('validation annulée par utilisateur : aucun POST', () => assert.equal(s.forms['form-valider'].submissions, 0));
s.confirmer(() => true);
s.cliquer('valider');
ok('validation confirmée : POST vers la pièce sélectionnée', () => {
  assert.equal(s.forms['form-valider'].submissions,1);
  assert.equal(s.forms['form-valider'].action,'/piece/1/valider/');
});
s.cliquer('annuler');
ok('annulation : POST distinct, sans supprimer physiquement', () => {
  assert.equal(s.forms['form-annuler'].submissions,1);
  assert.equal(s.forms['form-annuler'].action,'/piece/1/annuler/');
});
s.choisir(1);
ok('facture validée : pas de revalidation ni annulation de brouillon', () => {
  for (const nom of ['modifier','valider','annuler','acompte']) assert.equal(s.boutons[nom].disabled,true,nom);
  for (const nom of ['transformer','reglement','ecriture']) assert.equal(s.boutons[nom].disabled,false,nom);
});
s.cliquer('reglement');
ok('règlement : ouverture de la saisie pour la facture sélectionnée', () =>
  assert.equal(s.window.location.href,'/reglements/nouveau/?document=2'));
s.cliquer('ecriture');
ok('écriture : consultation de l’écriture déjà créée', () =>
  assert.equal(s.window.location.href,'/comptabilite/ecriture/2/'));
s.cliquer('transformer');
ok('transformer : ouvrir les choix sur la fiche, sans créer de pièce', () =>
  assert.equal(s.window.location.href,'/piece/2/#piece-transformer'));
s.choisir(2);
s.cliquer('acompte');
ok('commande validée : acompte rattaché à la commande', () =>
  assert.equal(s.window.location.href,'/reglements/nouveau/?commande=3'));
ok('libellés fidèles aux traitements, sans double comptabilisation', () => {
  assert(!listing.includes('data-liste="supprimer"'));
  assert(listing.includes('Annuler le brouillon'));
  assert(detail.includes("Voir l'écriture comptable"));
  assert(!detail.includes('> Comptabiliser</a>'));
});
ok('vérifier liens, choix de transformation et formulaires POST', () => {
  for (const item of ['data-valider=', 'data-ecriture=', 'data-transformer=',
                      'data-reglement=', 'data-acompte=', 'id="form-valider"',
                      'id="form-annuler"']) assert(listing.includes(item), item);
  assert(detail.includes('id="piece-transformer"'));
});
console.log(n + ' tests des actions documentaires : OK');
