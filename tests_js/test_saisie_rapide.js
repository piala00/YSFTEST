"use strict";
const assert = require("node:assert/strict");
class Element {
  constructor(tag = "INPUT", nom = "", valeur = "") {
    this.tagName = tag; this.name = nom; this.value = valeur; this.type = "text";
    this.dataset = {}; this.listeners = {}; this.children = []; this.disabled = false; this.hidden = false;
    this.textContent = ""; this.clicks = 0;
  }
  addEventListener(n, h) { (this.listeners[n] ||= []).push(h); }
  async send(n, donnees = {}) {
    const ev = Object.assign({target: this, key: "", preventDefault() { this.prevented = true; }}, donnees);
    for (const h of this.listeners[n] || []) await h(ev);
    return ev;
  }
  dispatchEvent(ev) { for (const h of this.listeners[ev.type] || []) h({...ev, target: this}); }
  focus() { document.activeElement = this; }
  select() { this.selected = true; }
  click() { this.clicks++; }
  getClientRects() { return this.hidden ? [] : [{}]; }
  append(e) { this.children.push(e); }
  replaceChildren() { this.children = []; }
  setAttribute(k, v) { this[k] = v; }
}
global.document = {readyState: "loading", activeElement: null, addEventListener() {},
  createElement(tag) { return new Element(tag.toUpperCase()); }};
global.Event = class { constructor(type) { this.type = type; } };
const saisie = require("../static/js/saisie_rapide.js");
function formulaire(reponse = {personnes: [], limite: false}) {
  const champs = [new Element("SELECT", "depart", "1"), new Element("INPUT", "telephone"), new Element("INPUT", "voyageur"),
    new Element("INPUT", "piece_identite"), new Element("INPUT", "prix", "5000"), new Element("INPUT", "personne"),
    new Element("INPUT", "csrfmiddlewaretoken", "csrf-fictif")];
  champs[5].type = champs[6].type = "hidden";
  const [depart, tel, nom, piece, prix, selection] = champs;
  const choix = new Element("SELECT"), label = new Element("LABEL"), message = new Element("DIV"); label.hidden = true;
  const nouveau = new Element("BUTTON"), chercherNom = new Element("BUTTON"), principal = new Element("BUTTON");
  principal.name = "imprimer"; principal.value = "1";
  const ouvrir = new Element("BUTTON");
  const correspondance = {"[data-contact-message]":message, "[data-contact-choix]":choix,
    "[data-contact-choix-label]":label, "[data-recherche-nom]":chercherNom, "[data-nouvelle-personne]":nouveau};
  const zone = {dataset: {telephone:"telephone", nom:"voyageur", piece:"piece_identite", selection:"personne"},
    querySelector: s => correspondance[s]};
  const form = new Element("FORM"); form.dataset.contactsUrl = "/contacts/rechercher/";
  form.elements = {namedItem: n => champs.find(c=>c.name===n) || null};
  form.querySelectorAll = s => s === "[data-contact]" ? [zone] : s === "button" ? [principal, ouvrir] : champs;
  form.querySelector = s => s === "[data-enchaine]" ? principal : tel;
  const appels = [];
  global.fetch = async (url, opts) => { appels.push({url,opts}); return {ok:true, json:async()=>reponse}; };
  saisie.installer(form);
  return {form, depart, tel, nom, piece, prix, selection, choix, label, message, nouveau, principal, ouvrir, appels};
}
const personne = (nom, id="1") => ({id, nom, telephone:"699000001", piece_identite:"DEMO-1234"});
async function main() {
  let total = 0;
  async function test(nom, f) { await f(); total++; process.stdout.write("OK " + nom + "\n"); }
  await test("Entrée avance d'un champ", async()=>{ const x=formulaire(); await x.form.send("keydown", {key:"Enter",target:x.nom}); assert.equal(document.activeElement,x.piece); });
  await test("Entrée respecte les boutons explicites", async()=>{ const x=formulaire(); const e=await x.form.send("keydown",{key:"Enter",target:x.ouvrir}); assert.equal(e.prevented,undefined); assert.equal(x.principal.clicks,0); });
  await test("Entrée laisse les listes choisir leur valeur", async()=>{ const x=formulaire(); for(const cible of [x.depart,x.choix]) assert.equal((await x.form.send("keydown",{key:"Enter",target:cible})).prevented,undefined); assert.equal(x.principal.clicks,0); });
  await test("composition et zones de texte préservées", async()=>{ const x=formulaire(); for(const e of [{target:new Element("TEXTAREA")},{target:x.nom,isComposing:true}]) assert.equal((await x.form.send("keydown",{key:"Enter",...e})).prevented,undefined); });
  await test("fin de formulaire déclenche l'impression", async()=>{ const x=formulaire(); await x.form.send("keydown",{key:"Enter",target:x.prix}); assert.equal(x.principal.clicks,1); });
  await test("double soumission bloquée, intention conservée", async()=>{ const x=formulaire(); await x.form.send("submit",{submitter:x.principal}); const e=await x.form.send("submit",{submitter:x.principal}); assert.equal(e.prevented,true); assert.equal(x.form.children[0].name,"imprimer"); assert.equal(x.principal.disabled,true); });
  await test("coordonnées uniques sans reprise du prix", async()=>{ const x=formulaire({personnes:[personne("Alice Démo")],limite:false}); x.tel.value="699000001"; await x.tel.saisieRecherche(); assert.equal(x.nom.value,"Alice Démo"); assert.equal(x.piece.value,"DEMO-1234"); assert.equal(x.selection.value,"1"); assert.equal(x.prix.value,"5000"); assert.equal(x.appels[0].opts.method,"POST"); assert.equal(x.appels[0].opts.headers["X-CSRFToken"],"csrf-fictif"); assert.equal(x.appels[0].url.includes("699"),false); });
  await test("téléphone partagé : choix obligatoire", async()=>{ const x=formulaire({personnes:[personne("Alice"),personne("Bob","2")],limite:false}); x.tel.value="699000001"; await x.tel.saisieRecherche(); assert.equal(x.nom.value,""); assert.equal(x.selection.value,""); assert.equal(x.label.hidden,false); x.choix.value="1"; await x.choix.send("change"); assert.equal(x.nom.value,"Bob"); assert.equal(x.selection.value,"2"); });
  await test("nouvelle personne au même numéro", async()=>{ const x=formulaire({personnes:[personne("Alice")],limite:false}); x.tel.value="699000001"; await x.tel.saisieRecherche(); await x.nouveau.send("click"); await x.tel.saisieRecherche(); assert.equal(x.nom.value,""); assert.equal(x.selection.value,""); assert.equal(x.tel.value,"699000001"); });
  await test("saisie manuelle jamais écrasée", async()=>{ const x=formulaire({personnes:[personne("Alice")],limite:false}); x.tel.value="699000001"; x.nom.value="Nom saisi"; await x.tel.saisieRecherche(); assert.equal(x.nom.value,"Nom saisi"); assert.equal(x.selection.value,""); });
  await test("numéro inconnu : aucune réutilisation", async()=>{ const x=formulaire(); x.tel.value="699000001"; await x.tel.saisieRecherche(); assert.equal(x.nom.value,""); assert.equal(x.selection.value,""); });
  await test("réponse ancienne ignorée", async()=>{ const x=formulaire(); let premiere;
    global.fetch=async(url,opts)=>opts.body.get("telephone")==="699000001" ? new Promise(r=>{premiere=r;}) : {ok:true,json:async()=>({personnes:[personne("Bob","2")],limite:false})};
    x.tel.value="699000001"; const attente=x.tel.saisieRecherche(); x.tel.value="699000002"; await x.tel.saisieRecherche(); premiere({ok:true,json:async()=>({personnes:[personne("Alice")],limite:false})}); await attente; assert.equal(x.nom.value,"Bob"); });
  await test("panne de recherche : saisie toujours possible", async()=>{ const x=formulaire(); global.fetch=async()=>({ok:false}); x.tel.value="699000001"; await x.tel.saisieRecherche(); assert.match(x.message.textContent,/saisie manuelle/); assert.equal(x.principal.disabled,false); });
  process.stdout.write(total + " scénarios JavaScript réussis\n");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
