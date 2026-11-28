// Tests sans dépendance pour l'action « Édition > Couper ».
// Lancer : node tests_js/test_menus_couper.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.resolve(__dirname, '../static/js/menus.js'), 'utf8');

async function scenario(pressePapier, modificationPendantAttente = false) {
  const evenements = {};
  const messages = [];
  const champ = {
    value: 'ABCD', selectionStart: 1, selectionEnd: 3, readOnly: false, disabled: false,
    matches: () => true, focus() {},
    setSelectionRange(debut, fin) { this.selectionStart = debut; this.selectionEnd = fin; },
    dispatchEvent() {},
  };
  const document = {
    documentElement: { classList: { contains: () => false } },
    getElementById: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener(nom, action) { evenements[nom] = action; },
    createElement: () => ({ remove() {} }),
    body: { appendChild(el) { messages.push(el); }, classList: { add() {} } },
  };
  const window = {};
  const contexte = { document, window, navigator: { clipboard: pressePapier },
    localStorage: { getItem: () => null }, setTimeout: () => {}, location: {}, console, URL,
    Event: class { constructor(nom) { this.type = nom; } } };
  vm.runInNewContext(code, contexte);
  evenements.focusin({ target: champ });

  if (modificationPendantAttente) {
    let terminer;
    contexte.navigator.clipboard = { writeText: () => new Promise(resolve => { terminer = resolve; }) };
    window.erpAction('couper');
    champ.value = 'ABCD-modifié';
    terminer();
  } else {
    window.erpAction('couper');
  }
  await Promise.resolve();
  await Promise.resolve();
  return { champ, messages };
}

(async () => {
  let resultat = await scenario(undefined);
  assert.equal(resultat.champ.value, 'ABCD');
  assert.ok(resultat.messages.at(-1)?.textContent.includes('indisponible'));

  resultat = await scenario({ writeText: () => Promise.reject(new Error('Interdit')) });
  assert.equal(resultat.champ.value, 'ABCD');
  assert.ok(resultat.messages.at(-1)?.textContent.includes('refusé'));

  let texteCopie = '';
  resultat = await scenario({ writeText: texte => { texteCopie = texte; return Promise.resolve(); } });
  assert.equal(texteCopie, 'BC');
  assert.equal(resultat.champ.value, 'AD');

  resultat = await scenario({}, true);
  assert.equal(resultat.champ.value, 'ABCD-modifié');
  assert.ok(resultat.messages.at(-1)?.textContent.includes('champ a changé'));

  console.log('4 scénarios « Couper » : OK');
})().catch(err => { console.error(err); process.exitCode = 1; });
