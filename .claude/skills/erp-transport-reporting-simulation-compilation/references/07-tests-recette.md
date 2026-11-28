# 07 — Matrice d'acceptation et contrôles bloquants

| ID | Scénario | Attendu |
|---|---|---|
| R01 | Menu comptabilité analytique | Les 10 plans et leurs sections sont affichés, chaque plan présente les états communs |
| R02 | Plan véhicules → BUS001 → mois donné | Compte exploitation, balance et grand livre, mêmes pièces et montants |
| R03 | Plan gares → Bertoua → date personnalisée | Imputation correcte agence exploitante / vendeuse |
| R04 | Plan propriétaires → partenaire fixe+variable | Résultat véhicules distinct du compte financier et des retraits, contrat daté |
| R05 | Comparatif octobre/septembre | Périodes indépendantes, variation calculée, pas division par zéro |
| R06 | Comparatif même période N-1 | Chiffres provenant de clôtures/écritures de chaque exercice |
| R07 | Comptabilité générale versus analytique | Pour tout axe : GL = imputé + non affecté + exclusions justifiées |
| R08 | 10 axes simultanés | Aucun double comptage en consolidant plusieurs dimensions |
| R09 | Journée caisse unique vs multi-caisses | Synthèse juste, transfert interne neutre en CA et charges |
| R10 | Colis / bagage / billet encaissé avant voyage | Dates prestation et règlement correctement séparées |
| R11 | 3, 6, 12 mois simulés | Une seule société ; paie et arrêtés comptables à chaque mois, totaux vérifiés |
| R12 | Passage décembre/janvier et février bissextile | Aucun mois tronqué, années/exercices corrects |
| R13 | 15 véhicules partenaires parmi 60 | Pas de confusion avec autres fournisseurs, propriétaires historiques conservés |
| R14 | Achat fournitures/garage | Engagement et stock distincts de charge consommée sur véhicule |
| R15 | Projet dans DB réelle | Simulation refusée ; migrations jamais silencieuses |
| R16 | GUI Windows exe + serveur exe | Lanceurs compilés, WSGI actif, templates/CSS présents, connexion client fonctionnelle |
| R17 | Windows machine vierge non admin | Pas de dépendance au Python développeur ; config externe, logs, sauvegardes |
| R18 | Synchronisation agence absente | Reporting marqué provisoire, fraîcheur des données affichée |
| R19 | Plan comptable 7 chiffres | Aucune écriture déplacée ; simulation conversion et tests collisions |
| R20 | Autorisations et export | Un propriétaire ne voit pas d'autres comptes, un caissier ne voit pas les écritures interdites |

### Méthode de validation
Exécuter unitaires, intégration API, DB PostgreSQL ou SQL Server si c'est la base cible, tests d'interface et pack Windows. Conserver les logs (ne pas y laisser de secrets), numéros de versions, captures, artefacts et résultats datés. Ne jamais écrire « test réussi » sans preuve d'exécution. Les tests de simulation ne remplacent pas la validation du schéma SYSCOHADA, des règles fiscales et contrats réels.
