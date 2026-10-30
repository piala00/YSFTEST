'use strict';
const assert=require('node:assert/strict');
const {filtrer}=require('../static/js/recherche_depart.js');
const options=[{value:'1',gamme:'VIP',recherche:'DEP001|VIP|VI 123|Étoile Alpha'},
 {value:'2',gamme:'CLASSIQUE',recherche:'DEP002|CLASSIQUE|AB 456|Alpha Express'},
 {value:'3',gamme:'VIP',recherche:'DEP003|VIP|AC 789|Alpha Premium'}];
const ids=(s,g=['VIP','CLASSIQUE'])=>filtrer(options,s,g).map(o=>o.value);
assert.deepEqual(ids('vi'),['1','3']);
assert.deepEqual(ids('a'),['1','2','3']);
assert.deepEqual(ids('ab'),['2']);
assert.deepEqual(ids('alpha prem'),['3']);
assert.deepEqual(ids('eto'),['1']);
assert.deepEqual(ids('DEP002'),['2']);
assert.deepEqual(ids('', ['VIP']),['1','3']);
assert.deepEqual(ids('', []),[]);
console.log('Recherche départ : préfixes, accents, combinaison de mots et filtres OK');
