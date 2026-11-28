# Alignement de l'ERP sur les documents terrain (transport interurbain, Cameroun)

Étude des documents réels d'exploitation d'une société de transport de voyageurs + messagerie
(caisse d'agence, états de fin de session, feuille de route par départ, fiche carburant, courriers).
**Aucune donnée réelle ici** : seulement les *concepts* métier et les écarts avec l'ERP, pour
piloter les évolutions. Règle AGENTS : rien d'inventé en montants/règles — à fixer par le propriétaire.

## 1. Feuille de route par départ (« Mouvements des véhicules »)
Par **départ** (un véhicule, un trajet, une heure) :
- **Recettes** : passagers (guichet), bagages, **ramassages** (passagers pris en route), brute.
- **Dépenses déduites de la brute** : **retenue** (commission société, ex. 15 %), **ration**
  (équipage), **carburant**, **rabateurs** (personnes payées pour remplir le car), entretien/réparation,
  autres → **reste net** (pour le véhicule / propriétaire) + **cumul**.

## 2. Caisse d'agence
- **Report du solde antérieur**, **versements** de recettes (fins de session, chauffeurs),
  dépenses dont **laverie** par véhicule (avec **quote-part** société), retenues diverses,
  **reste net** + cumul.

## 3. État de fin de session (par agent / caisse)
En-tête : agence, **n° de session**, agent, nom de la caisse, **heures d'ouverture/fermeture**,
journée. Puis :
- **Liste des réservations** : n° ticket, client, trajet, course (destination + heure), **catégorie**
  (Classique / VIP), **siège**, heure de saisie, tarif.
- **Récapitulatif** : nombre de tickets et montant par trajet/catégorie ; **remboursements**
  (réservations annulées, en négatif) ; **dépenses** payées depuis le guichet (en négatif) ;
  **total net** de la journée/session.
- Par réservation : **avance / relicat / net à payer** (acompte, monnaie rendue, solde dû).
- Réconciliation agent : brut passagers, brut bagages, recette messagerie, ration, transit,
  carburant, annulé, autres, **manquants / surplus**, solde.

## 4. Fiche carburant
Par plein : date, heure, **immatriculation véhicule**, **chauffeur**, **trajet**, somme, **cumul**.

## 5. Messagerie / courrier
Suivi par **reçu** : date, destinataire, n° reçu, destination, libellé, quantité, prix unitaire, montant.
Documents de courrier regroupés par destinataire.

## Écarts avec l'ERP (ce qui est à faire évoluer)
| Concept terrain | Présent dans l'ERP | Évolution proposée |
|---|---|---|
| Retenue / commission société | ✅ oui | — |
| Transit / correspondance | ✅ oui | — |
| Recette au départ par véhicule, bagages, messagerie/colis | ✅ oui | — |
| **Ramassages** (recette en route) | ❌ non | Catégorie de recette distincte du guichet, au départ |
| **Rabateurs** (payés pour remplir le car) | ❌ non | Dépense par départ, imputée au véhicule |
| **Laverie** (+ quote-part société) | ❌ non | Dépense récurrente par véhicule, à la caisse d'agence |
| **Ration** (repas équipage) | ⚠️ à confirmer | Dépense par départ ou par session |
| **Manquants / surplus** (écart de caisse) | ❌ non | Champ de réconciliation à la clôture de session + comptabilisation |
| **Dépenses payées depuis le guichet** dans le récap de session | ⚠️ partiel | Intégrer au récap de fin de session |
| **Avance / relicat / net à payer** par réservation | ⚠️ à confirmer | Réservation avec acompte et solde |
| **Édition « État de fin de session »** au format terrain | ⚠️ partiel | Aligner la mise en page (en-tête, liste, récap, remboursements, dépenses) |
| **Fiche carburant** (véhicule + chauffeur + trajet + cumul) | ⚠️ à confirmer | Édition dédiée depuis le module garage/carburant |

## Règles métier à fixer par le propriétaire (rien d'inventé)
1. **Rabateurs** : montant fixe par départ, % de la recette, ou par passager ? Fixé par qui ?
2. **Ration** : fixe par départ ou par session ? À la charge du véhicule (propriétaire) ou de la société ?
3. **Laverie** : quote-part société (% ou montant) ? Fréquence (par lavage / par jour) ?
4. **Ramassages** : tarif selon le tronçon (même grille que le guichet) ou prix libre saisi à bord ?
5. **Manquants / surplus** : qui valide ? Comptabilisation (à la charge de l'agent / compte d'attente) ?

## Ordre de réalisation proposé
1. Feuille de route par départ : **ramassages** (recette) + **rabateurs** / **laverie** / **ration** (dépenses).
2. Clôture de session : **manquants / surplus** + **dépenses du guichet** + édition alignée.
3. Fiche carburant dédiée ; réservations avec acompte (avance / relicat / net à payer).

Chaque étape : modèle + saisie + comptabilisation (toute écriture analytique issue d'une écriture
générale validée) + édition ressemblant au document terrain + tests, avec les montants/règles saisis
par le propriétaire (jamais inventés).
