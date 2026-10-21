# Matrice de couverture exhaustive — Pour ne rien oublier

## Règle du recensement

Le **niveau 1** est un menu Sage ; le **niveau 2** une commande documentée ; le **niveau 3** une fenêtre, un groupe ou un onglet attesté ; le **niveau 4** les champs/colonnes/icônes/boutons observés ; le **niveau 5** les options, effets, erreurs et droits testés. Ne jamais déclarer le niveau 5 « couvert » sur la seule base d'une liste fonctionnelle.

### Échelle d'avancement (distincte du niveau de preuve)

- **C0** : entrée à recenser.
- **C1** : nom dans la documentation de découpage.
- **C2** : rôle et dépendances expliqués par une source.
- **C3** : écrans/champs observés sur V12 concernée.
- **C4** : procédure guidée testée avec résultats et cas de bord.
- **C5** : diagnostic/erreurs, impacts et audit validés.

### Tableau de pilotage à compléter avec l'installation V12

| Menu | Inventaire documentaire | Onglets/champs observés | Procédures testées | Prochain manque |
|---|---|---|---|---|
| Fichier | C1 | À relever | À valider | Paramètres société et outils |
| Édition | Ergonomie classique | À relever | À valider | Contexte et raccourcis V12 |
| Structure | C1 | À relever | À valider | Fiches familles/articles/tiers/dépôts |
| Traitement | C1 | À relever | À valider | Cycle documentaire, stock, règlements |
| État | C1 | À relever | À valider | Filtres, modèles, totaux |
| Fenêtre | C1 | À relever | À valider | Personnalisation et préférences |
| ? | Ergonomie classique | À relever | À valider | Menu d'aide V12 exact |

## Couverture de chaque écran

`Menu → Sous-menu → Liste → Fiche → Onglet → Sous-onglet → Champ → Action → Effets → Erreurs → Droits → Source`

Créer pour chaque feuille des captures montrant **tous les onglets réellement présents** ; capturer menus contextuels et popups ; inspecter états grisés, listes déroulantes et permissions d'au moins deux rôles. Les pièces et identifiants doivent être anonymisés.

## Conditions pour annoncer « complètement documenté »

- Chaque ligne C5, preuves datées, version/édition/options connues ; cas standard + erreur ; chemin testé ; référence source.
- Des captures couvrant les options accessibles et les profils concernés.
- Un inventaire des fonctions **non disponibles** (édition, option ou droit) et des fonctions nouvelles V12.x.
- Audit final sans blocage sur 5 scénarios transverses : vente, achat, stock, financier, état.

La documentation de 2026 ne couvre **pas** automatiquement la présence de fonctions dans toutes les éditions : mettre à jour cette matrice dès évolution de version.
