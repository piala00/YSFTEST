# 04 — Rapport journalier : simplicité visuelle, un ou plusieurs comptes-caisses

## Objectif utilisateur

Un seul **rapport simple en tableaux** par agence et par jour, imprimable noir et blanc, sans widgets/KPI/graphiques. Plusieurs caisses dans une agence ne doivent pas rendre le rapport illisible.

### En-tête commun

Compagnie ; agence ; date ; responsable ; statut ouverture/clôture ; dernière synchronisation ; date/heure de génération ; devise XAF/FCFA. Si une seule caisse, indiquer `Caisse : Principale`. Si plusieurs, afficher `Toutes les caisses` et option d'édition caisse isolée.

### Sections et ordre

1. **Billetterie — départs de la journée** : véhicule/code, gamme Classique/VIP, trajet, places, tarif unitaire réel, total, sous-total. Par voyage/segment/tarif. Montants de ventes **non égaux par défaut aux encaissements du jour**.
2. **Bagages voyageurs payants** : véhicule, libellé, destination, quantité, montant, total.
3. **Colis / courrier** : distinct des bagages, uniquement si pertinent ; recettes encaissées et activité transportée ont leurs dates propres.
4. **Sorties réalisées** : date/pièce, désignation, véhicule/service concerné, `payeur/caisse` et montant, avec sous-total, en distinguant espèces des paiements non-espèces pour le rapprochement.
5. **Situation de caisse par caisse (si plusieurs)** : ouverture, entrées externes espèces, sorties externes espèces, transferts reçus/émis, remises, solde fin théorique, espèces comptées, écart.
6. **Synthèse générale de l'agence** : total encaissements externes par moyen, total paiements externes par moyen, net externe de la journée, total espèces physiquement en caisses, fonds en transit séparés, fonds reversés et fonds restant à reverser ; pièces et signatures.

Les **transferts internes** apparaissent au besoin dans un tableau court distinct, mais sont exclus du calcul des recettes/dépenses externes agrégées. Une émission et sa réception ne produisent pas deux recettes.

### Rendu mono-caisse

Afficher un unique mini-tableau « Caisse principale » et éviter une section artificielle « répartition par caisses ».

### Rendu multi-caisses (illustration)

| Caisse | Ouverture | Entrées externes | Sorties externes | Transferts nets | Solde fin |
|---|---:|---:|---:|---:|---:|
| Billetterie | 0 | 500 000 | 20 000 | 0 | 480 000 |
| Courrier | 0 | 250 000 | 10 000 | 0 | 240 000 |
| Garage | 100 000 | 0 | 80 000 | 0 | 20 000 |
| Centrale | 0 | 300 000 | 100 000 | 0 | 200 000 |
| **TOTAL** | **100 000** | **1 050 000** | **210 000** | **0** | **940 000** |

Si `transferts nets` inclus, afficher signe et somme nulle **uniquement lorsque toutes les réceptions sont terminées** ; les sommes en transit exigent ligne séparée pour rapprocher.

### Différences sémantiques sur la conclusion du rapport

- **Recettes d'exploitation** : billets/colis/bagages effectués selon période d'exploitation.
- **Recettes encaissées** : paiements externes réellement perçus pendant la journée.
- **Solde de caisse** : fonds physiquement détenus après les mouvements, y compris fonds d'ouverture.
- **Recette nette journalière** : flux encaissé externe moins paiements externes du jour (indicateur de trésorerie, pas profit).
- **Montant reversé** : somme des remises physiques validées, indépendamment du résultat d'exploitation.
- **Reste à reverser** : seulement selon solde physique, fonds de caisse autorisé et transferts/transit ; jamais déduit de toutes les ventes sans rapprochement.

### Droits et UX

- Agent : voir ses sessions/sa caisse ; chef : voir toutes les caisses de son agence ; direction : voir agrégats de toutes les agences et zoom caisse ; comptable : contrôle et exports autorisés.
- Filtres obligatoires : `date`, `agency_id` limité par droits, `cashbox_id = ALL | id` si plusieurs ; éventuellement mode d'édition `consolidé | caisse`.
- PDF et impression A4, pagination, sous-totaux en gras, montants alignés, indication explicite « état provisoire » si synchronisation incomplète.
- Prévoir un bouton « Voir détail » ouvrant les pièces sources, mais l'impression reste **uniquement tabulaire**.
