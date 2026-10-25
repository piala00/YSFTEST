# 01 — Gabarit officiel de rapport journalier d'agence

## En-tête minimal

```text
[LOGO/NOM COMPAGNIE]     RAPPORT JOURNALIER — AGENCE DE [NOM]
Date d'activité : JJ/MM/AAAA  N° rapport : RJ-[AG]-[DATE]-[VERSION]
Chef d'agence : ...        Caisse(s) : ...        État : PROVISOIRE / CLÔTURÉ
Dernière synchronisation : ...          Généré le : ...
```

## Tableau A — Billetterie / départs effectués par l'agence

| Code véhicule | Nom du véhicule | Service | Trajet | Départ/voyage | Places | Prix unitaire FCFA | Total FCFA |
|---|---|---|---|---|---:|---:|---:|
| C-001 | Car 01 | Classique | Bertoua → Yaoundé | V001 08:00 | 30 | 7 000 | 210 000 |
| V-004 | Car 04 | VIP | Bertoua → Garoua-Boulaï | V002 10:00 | 20 | 12 000 | 240 000 |
| C-009 | Car 09 | Classique | Bertoua → Abong-Mbang | V003 14:00 | 10 | 5 000 | 50 000 |
| **TOTAL** | | | | | **60** | | **500 000** |

Prix et montants **fictifs**. Une ligne par `(agence départ, trip_id, véhicule, segment/trajet, gamme, prix réellement pratiqué)` ; en cas de plusieurs prix, plusieurs lignes de départ/tarif. Le « nombre de places » correspond aux billets/sièges pertinents selon règle configurée (`embarqué` ou `vendu`). Le statut du billet doit être explicite dans le moteur ; éviter de compter annulés/remboursés.

## Tableau B — Bagages payants des voyageurs

| Code véhicule | Désignation des bagages | Destination | Qté | Montant FCFA |
|---|---|---|---:|---:|
| C-001 | Carton supplémentaire | Yaoundé | 1 | 10 000 |
| V-004 | Bagage excédentaire | Garoua-Boulaï | 1 | 5 000 |
| C-009 | Sac volumineux | Abong-Mbang | 1 | 8 000 |
| **TOTAL** | | | **3** | **23 000** |

Le document d'origine contient aussi `bagage_id`, `trip_id`, `ticket_id`, `payment_id`, poids/franchise, agent et référence d'encaissement ; ces colonnes techniques ne s'affichent pas toutes par défaut dans le rapport simple. Si les bagages du jour concernent aussi des départs ultérieurs, distinguer vue d'exploitation du jour et vue de caisse : pas de double addition.

## Tableau C — Expéditions de colis (facultatif si agence exploite la messagerie)

| N° bordereau | Désignation | Destination | Véhicule/voyage si connu | Montant encaissé FCFA |
|---|---|---|---|---:|
| ... | ... | ... | ... | ... |
| **TOTAL COLIS** | | | | **...** |

L'encaissement du colis ne prouve pas son chargement dans le véhicule ce jour : distinguer date de paiement et rattachement au trajet réel. Les bagages des passagers ne figurent jamais ici.

## Tableau D — Sorties effectives de caisse

| N° pièce | Désignation | Affectation | Paiement | Montant FCFA |
|---|---|---|---|---:|
| S001 | Carburant | C-001 | Espèces | 45 000 |
| S002 | Péage | V-004 | Espèces | 12 000 |
| S003 | Fournitures de bureau | Agence | Espèces | 6 000 |
| **TOTAL SORTIES** | | | | **63 000** |

**Ne lister ici que les décaissements**, sur une plage de date de caisse, pas les achats à crédit ni les charges calculées (amortissements, paie à payer, ventilation analytique sans paiement).

## Tableau E — Caisse et montant à reverser

| Désignation | Montant FCFA |
|---|---:|
| Total billets encaissés le jour | 500 000 |
| Total bagages encaissés le jour | 23 000 |
| Total colis encaissés le jour | 0 |
| **TOTAL ENCAISSEMENTS DU JOUR** | **523 000** |
| Dont espèces | 443 000 |
| Dont Mobile Money / banque | 80 000 |
| Solde espèces à l'ouverture | 0 |
| Total sorties payées en espèces | 63 000 |
| **ESPECES DISPONIBLES AVANT REVERSEMENT** | **380 000** |
| Espèces effectivement reversées | 380 000 |
| Espèces restant à la caisse (théorique) | 0 |
| Espèces comptées après reversement | 0 |
| **ÉCART DE CAISSE** | **0** |
| **RECETTE NETTE TOUS MOYENS (hors solde antérieur)** | **460 000** |

Dans cet exemple : billetterie = 420 000 espèces + 80 000 électronique ; bagages = 23 000 espèces ; sorties = 63 000 espèces. Les chiffres d'exploitation A/B et d'encaissement E coïncident **uniquement par hypothèse** : ventes et paiements réalisés le même jour dans la même agence. En production ce n'est pas garanti ; utiliser les paiements pour le tableau E.

Signatures : préparé par le caissier ; vérifié par le chef d'agence ; visa du comptable ; heure et statut de clôture.

## Présentation

- Ordre impératif : entête → tableau billets → bagages → (colis facultatifs) → sorties → caisse → signatures.
- Fond blanc, texte noir, en-têtes discrets, bordures fines. Largeurs raisonnables ; montants alignés à droite, groupes de milliers et FCFA une fois dans l'en-tête.
- Titre et date clairement visibles, aucun graphique ni bloc décoratif ; lignes du tableau et totaux sur toutes les pages imprimées.
- Prévoir pagination automatique, répétition des en-têtes de colonne, « page x/y », et ne pas tronquer les lignes.
- Montrer « Aucune opération » quand un tableau est vide, pas masquer silencieusement une section attendue.

## Adaptation multi-caisses (25 octobre 2026)

Pour une agence avec plusieurs caisses, insérer après le tableau des sorties un tableau simple « Situation par caisse » : **Caisse | Solde ouverture | Encaissements espèces externes | Sorties espèces externes | Transferts nets | Remises | Solde théorique | Solde compté | Écart**, puis un **TOTAL AGENCE**. Une agence à caisse unique affiche seulement la ligne de sa caisse principale et le résumé final. Les tableaux voyageurs/bagages/colis ne changent pas ; aucun diagramme. Les paiements banque/Mobile Money sont présentés dans la synthèse externe par moyen, sans augmenter le solde espèces physique.

