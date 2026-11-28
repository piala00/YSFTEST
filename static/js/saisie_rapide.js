/* Saisie du guichet : recherche locale, clavier et protection du double clic. */
(function (global) {
  "use strict";
  function visibles(form) {
    return Array.from(form.querySelectorAll("input, select, textarea")).filter(function (e) {
      return !e.disabled && e.type !== "hidden" && !e.hidden && e.getClientRects().length > 0;
    });
  }
  function suivant(form, element) {
    var liste = visibles(form), i = liste.indexOf(element) + 1;
    while (i < liste.length && liste[i].dataset.contactRempli === "1") i++;
    if (i < liste.length) {
      liste[i].focus();
      if (liste[i].tagName === "INPUT" && liste[i].type !== "number") liste[i].select();
    } else {
      var bouton = form.querySelector("[data-enchaine]");
      if (bouton && !bouton.disabled) bouton.click();
    }
  }
  function installerContact(form, zone) {
    var tel = form.elements.namedItem(zone.dataset.telephone);
    var nom = form.elements.namedItem(zone.dataset.nom);
    var piece = zone.dataset.piece ? form.elements.namedItem(zone.dataset.piece) : null;
    var selection = form.elements.namedItem(zone.dataset.selection);
    var message = zone.querySelector("[data-contact-message]");
    var choix = zone.querySelector("[data-contact-choix]");
    var label = zone.querySelector("[data-contact-choix-label]");
    var personnes = [], compteur = 0, minuterie, controle, manuelle = false;
    function info(texte) { message.textContent = texte; }
    function masquer() { label.hidden = true; choix.replaceChildren(); }
    function annuler() {
      compteur++;
      clearTimeout(minuterie);
      if (controle) controle.abort();
      masquer(); selection.value = "";
    }
    function appliquer(p, explicite) {
      var champs = [[nom, p.nom], [piece, p.piece_identite || ""]];
      if (!explicite && champs.some(function (c) {
        return c[0] && c[0].value && c[0].value !== c[1] && c[0].dataset.contactRempli !== "1";
      })) return false;
      tel.value = p.telephone;
      champs.forEach(function (c) {
        if (!c[0]) return;
        c[0].value = c[1];
        c[0].dataset.contactRempli = c[1] ? "1" : "";
        c[0].dataset.contactValeur = c[1];
        c[0].dispatchEvent(new global.Event("change", {bubbles: true}));
      });
      selection.value = p.id;
      info("Coordonnées retrouvées — vérifiez et corrigez si nécessaire.");
      masquer();
      return true;
    }
    async function rechercher(parNom) {
      if (manuelle && !parNom) return false;
      var telephone = tel.value.trim(), nomCherche = parNom ? nom.value.trim() : "";
      if ((!parNom && telephone.replace(/\D/g, "").length < 7) || (parNom && nomCherche.length < 3)) {
        info(parNom ? "Saisissez au moins trois caractères du nom." : "");
        return false;
      }
      var numero = ++compteur, nomAvant = nom.value, pieceAvant = piece ? piece.value : "";
      clearTimeout(minuterie);
      if (controle) controle.abort();
      controle = new global.AbortController();
      var requete = controle;
      var delai = setTimeout(function () { requete.abort(); }, 2500);
      info("Recherche…");
      try {
        var corps = new global.URLSearchParams({telephone: parNom ? "" : telephone, nom: nomCherche,
          nature: form.elements.namedItem("nature") ? form.elements.namedItem("nature").value : "COLIS"});
        var csrf = form.elements.namedItem("csrfmiddlewaretoken");
        var reponse = await global.fetch(form.dataset.contactsUrl, {method: "POST", credentials: "same-origin",
          cache: "no-store", signal: controle.signal, headers: {"X-CSRFToken": csrf.value}, body: corps});
        if (!reponse.ok) throw new Error("Recherche refusée");
        var donnees = await reponse.json();
        if (numero !== compteur || (!parNom && tel.value.trim() !== telephone)) return false;
        personnes = donnees.personnes;
        masquer();
        if (!personnes.length) { info("Aucune personne trouvée — poursuivez la saisie."); return false; }
        var intact = nom.value === nomAvant && (!piece || piece.value === pieceAvant);
        if (!parNom && personnes.length === 1 && !donnees.limite && intact && appliquer(personnes[0], false)) return false;
        var vide = global.document.createElement("option");
        vide.value = ""; vide.textContent = "Choisir une personne…"; choix.append(vide);
        personnes.forEach(function (p, i) {
          var option = global.document.createElement("option");
          option.value = String(i);
          option.textContent = p.nom + " — " + p.telephone + (p.piece_identite ? " — pièce …" + p.piece_identite.slice(-4) : "");
          choix.append(option);
        });
        label.hidden = false;
        info(donnees.limite ? "Plus de dix personnes : précisez le nom pour affiner." : "Sélectionnez la bonne personne, ou choisissez Nouvelle personne.");
        return true;
      } catch (erreur) {
        if (numero === compteur) info("Recherche indisponible — la saisie manuelle reste possible.");
        return false;
      } finally { clearTimeout(delai); }
    }
    tel.addEventListener("input", function () {
      annuler(); manuelle = false;
      [nom, piece].forEach(function (champ) {
        if (!champ) return;
        if (champ.dataset.contactRempli === "1" && champ.value === champ.dataset.contactValeur) champ.value = "";
        champ.dataset.contactRempli = "";
      });
      info(""); minuterie = setTimeout(function () { rechercher(false); }, 250);
    });
    nom.addEventListener("input", function () { selection.value = ""; nom.dataset.contactRempli = ""; });
    if (piece) piece.addEventListener("input", function () { piece.dataset.contactRempli = ""; });
    choix.addEventListener("change", function () {
      if (choix.value !== "" && personnes[Number(choix.value)]) {
        appliquer(personnes[Number(choix.value)], true);
        suivant(form, tel);
      }
    });
    zone.querySelector("[data-recherche-nom]").addEventListener("click", function () {
      manuelle = false;
      rechercher(true).then(function (multiple) { if (multiple) choix.focus(); });
    });
    zone.querySelector("[data-nouvelle-personne]").addEventListener("click", function () {
      annuler(); manuelle = true; nom.value = "";
      if (piece) piece.value = "";
      [nom, piece].forEach(function (c) { if (c) c.dataset.contactRempli = ""; });
      info("Nouvelle personne : ses coordonnées seront mémorisées après l'enregistrement."); nom.focus();
    });
    tel.saisieRecherche = function () { return rechercher(false); };
    tel.saisieChoix = choix;
  }
  function installer(form) {
    if (form.dataset.saisieInstallee) return;
    form.dataset.saisieInstallee = "1";
    form.querySelectorAll("[data-contact]").forEach(function (zone) { installerContact(form, zone); });
    form.addEventListener("keydown", async function (ev) {
      var e = ev.target;
      if (ev.key !== "Enter" || ev.shiftKey || ev.isComposing || e.tagName === "TEXTAREA" || e.tagName === "SELECT" || e.tagName === "BUTTON" || e.tagName === "A") return;
      ev.preventDefault();
      if (e.saisieRecherche) {
        var multiple = await e.saisieRecherche();
        if (global.document.activeElement !== e) return;
        if (multiple) { e.saisieChoix.focus(); return; }
      }
      suivant(form, e);
    });
    form.addEventListener("submit", function (ev) {
      if (form.dataset.envoi === "1") { ev.preventDefault(); return; }
      form.dataset.envoi = "1"; form.setAttribute("aria-busy", "true");
      if (ev.submitter && ev.submitter.name) {
        var intention = global.document.createElement("input"); intention.type = "hidden";
        intention.name = ev.submitter.name; intention.value = ev.submitter.value; form.append(intention);
      }
      form.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
    });
    var paiement = form.elements.namedItem("paiement");
    if (paiement) paiement.addEventListener("change", function () {
      if (paiement.value === "COMPTE") form.querySelector("[data-complements]").open = true;
    });
    var depart = form.elements.namedItem("depart"), champs = visibles(form);
    var premier = depart && !depart.value ? depart : form.querySelector("[data-contact] input:not([type=hidden])");
    if (premier || champs[0]) (premier || champs[0]).focus();
  }
  function demarrer() { global.document.querySelectorAll("form[data-saisie-rapide]").forEach(installer); }
  if (typeof module !== "undefined" && module.exports) module.exports = {installer: installer, suivant: suivant};
  if (global.document) {
    if (global.document.readyState === "loading") global.document.addEventListener("DOMContentLoaded", demarrer);
    else demarrer();
  }
})(typeof window !== "undefined" ? window : globalThis);
