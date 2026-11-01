"use strict";
const assert = require('node:assert/strict');
const {dimensionsSaisieRapide: taille} = require('../static/js/fenetres.js');
assert.deepEqual(taille('380', '720', {l:1600,h:900}), {l:380,h:720});
assert.deepEqual(taille('380', '720', {l:1024,h:600}), {l:380,h:600});
assert.deepEqual(taille('380', '720', {l:240,h:420}), {l:240,h:420});
for (const valeurs of [['',''], ['abc','720'], ['380','Infinity'], ['100','720']]) {
  assert.equal(taille(...valeurs, {l:1600,h:900}), null);
}
process.stdout.write('Dimensions guichet : bureau, petit écran et valeurs invalides OK\n');
