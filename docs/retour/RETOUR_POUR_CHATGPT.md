# Retour de Claude Code à partager avec ChatGPT

« Voici l'ERP Transport après audit et modifications. Les fichiers joints représentent le code source complet expurgé
des secrets, avec les migrations et les tests. Voici les fonctionnalités réellement vérifiées, les résultats et les
anomalies restantes. Merci d'examiner la cohérence GA → analytique → reporting, et les achats / stocks / paie /
partenaires. »

## 1. Identification du projet
- Dépôt `YSFTEST`, branche `ccr-5592a371-fusjt2` (commit indiqué dans le nom de l'export et `MANIFESTE.txt`).
- Django 6.1.2, Python 3.13 ; SQLite (par défaut, WAL), PostgreSQL ou SQL Server (mssql-django) ; paquet Windows hors ligne.
- Interface web « bureau » à fenêtres internes, menus de type Sage (Fichier, Édition, Structure, Traitement, Etat).

## 2. Architecture examinée
| Application | Rôle |
|---|---|
| `apps/core` | Société (activité, système comptable normal / SMT), agences, numérotation par agence, droits (logiciel, menu), portail |
| `apps/comptabilite` | Plan SYSCOHADA, journaux, écritures (une seule source monétaire), états normal et SMT, analytique par section |
| `apps/commercial` | Tiers, articles, dépôts, ventes, achats (demande, commande, réception, facture), stock CMUP, caisse |
| `apps/transport` | Gares, lignes (arrêts, gamme), véhicules (flotte datée), départs, billets (tronçons, bagages), colis, caisses et sessions, clôtures, rapport journalier A4, dépenses autorisées par le siège, imprévus, analytique, reporting comparatif |
| `apps/garage` | Pleins (consommation), ordres de réparation, magasin (stock permanent au CMUP, achats pour le stock / un véhicule / une immobilisation, sorties) |
| `apps/personnel` | Employés, rubriques de paie (sans taux imposé), bulletins, paiement, ventilation du salaire sur les véhicules |
| `apps/partenaires` | Contrats propriétaires versionnés, décomptes, compte propriétaire séparé, avances, retraits, relevés |
| `apps/echanges` | Synchronisation hors ligne par fichiers signés (HMAC), outbox, inbox idempotente, relais par le siège |

Schéma : `SCHEMA_BASE.md`. Routes : `LISTE_DES_ROUTES.md`. Comptes et analytique : `MAPPING_JOURNAUX_ET_ANALYTIQUE.md`.

## 3. Écarts trouvés
Voir `AUDIT_ECARTS.md` (EXISTANT / PARTIEL / ABSENT / BLOQUANT, avec fichiers et tests).

## 4. Modifications de cette mise à jour
| Sujet | Contenu | Migration |
|---|---|---|
| Reporting sur les états | catalogue de tous les états généraux et analytiques ; évolution de la société ; comparaison de deux périodes et tableau mensuel sur tout axe ; classements ; CSV ; mêmes chiffres que les états (testé) | — |
| Simulation sur plusieurs mois | 1 à 24 mois, sur plusieurs exercices ; assurance des véhicules ; saisonnalité ; bilan mois par mois | — |
| Programme exécutable | `deploy/executable` (lanceur + spécification PyInstaller), `9-COMPILER-EXECUTABLE.bat` (compilation Windows sans Internet) ; vérifié par une construction et un démarrage sous Linux | — |
| Plan analytique complet | Comptabilité analytique : axes gares, véhicules, propriétaires, gammes, lignes, voyages, activités, contrats et plans de sections ; balance de chaque axe avec non affecté et rapprochement ; six états par élément (exploitation, comptes, grand-livre, évolution, croisé, comparaison) ; périodes en un clic ; CSV. Voir `docs/COMPTABILITE_ANALYTIQUE_ETATS.md`. Repris de l'archive 7 chiffres : refus des comptes trop longs, client bureau analytique ; non repris : inversion de l'ordre des modules (régression), doubles adresses | — |
| Plan à 7 chiffres | longueur des comptes par société (7 pour un nouveau dossier), numéros complétés par des zéros à droite, recherche par numéro court conservée, commande de conversion avec contrôle des collisions ; reprise : plan d'origine tel quel | `core 0021` |
| Deux modules comptables | « Comptabilité générale » et « Comptabilité analytique » (Véhicules, Propriétaires, sections) sur une seule comptabilité | — |
| Magasin du garage | inventaire permanent : achat D 33x, sortie D charge (véhicule) / C 33x au CMUP ; achat direct pour un véhicule ; immobilisation ; pièce du magasin sur l'ordre de réparation | `garage 0002` |
| Compte du véhicule | relevé du propriétaire : compte en cours depuis le dernier arrêté, arrêt à la demande, retrait si positif, compensation si négatif ; contrat « salaire mensuel fixe » | `partenaires 0003` (libellés) |
| Simulation | commande `simulation` : un mois joué par le logiciel dans un dossier séparé ; `7-SIMULATION.bat`, `8-SUPPRIMER-SIMULATION.bat` | — |
| Anomalies RJ | caisse négative bloquante, transfert limité aux espèces, départ futur refusé, heure réelle de départ, rapprochement des billets, car des colis, Mobile Money 552 | `transport 0014` |
| Propriétaires | compte 467 séparé du 401, contrats variable / fixe + variable / avance sur variable, plancher contractuel, décompte en deux écritures, avances, retraits autorisés, relevé par nature | `transport 0015`, `partenaires 0002` |
| Plus tôt (même journée) | bagages payants, système SMT, dépenses autorisées par le siège, imprévus de voyage, reporting comparatif, analytique Véhicules / Propriétaires, flottes Classique / VIP | `transport 0009` à `0013`, `core 0020` |

Toutes les migrations sont additives ; aucune donnée existante n'est supprimée ou renumérotée.

## 5. Résultats sur le rapport RJ-AG-20261026
- Les six anomalies relevées sont traitées (tableau de `AUDIT_ECARTS.md` § 1).
- Le cas d'origine (transfert de 500 000 avec 620 000 − 282 000 en caisse) est maintenant **refusé** au transfert. Une caisse négative issue d'une autre cause bloque la clôture et s'affiche en tête du rapport.
- Le rapport distingue les départs du jour (date de départ, heure réelle) et la caisse (date de paiement), avec un rapprochement chiffré.

## 6. Simulation septembre 2026
Les CSV fournis ont été validés (`BILAN_SIMULATION_SEPTEMBRE_2026.md`). La simulation est maintenant **jouée par le logiciel
lui-même** (`python manage.py simulation`), jour après jour, dans un dossier séparé : ventes de billets et bagages,
colis, départs et arrivées, carburant, magasin, réparations, loyers autorisés, versements en banque, paie, décomptes et
règlements des propriétaires. Résultats et contrôles : `BILAN_SIMULATION_RESULTATS.md`.

## 7. Achats et stock
Gestion commerciale : demande d'achat, commande, réception, facture fournisseur, avoirs, règlements, dépôts, transferts,
inventaires, CMUP (inventaire intermittent, inchangé). Magasin du garage : inventaire permanent ; au moment de l'achat, chaque
ligne est destinée au stock, à un véhicule précis ou aux immobilisations ; la sortie du stock passe la charge, sur le
véhicule s'il est indiqué.

## 8. Comptabilité, partenaires, sécurité, hors ligne
- Entièrement codé et testé : source unique, analytique sur la ligne d'écriture, rapprochement affecté / non affecté,
  propriétaires (exemples A et B du skill), caisses et clôtures, échanges hors ligne idempotents (4 bases).
- Partiel : droits par agence (ABAC), portail partenaire, autorisation des retraits par le siège via les échanges.
- À développer : quotas de sièges inter-agences, fichier des immobilisations et amortissements.

## 9. Décisions ouvertes
1. Plan comptable de la société (tous les comptes sont des propositions).
2. Pour les contrats propriétaires : rôle de la société (exploitant ou intermédiaire pour le compte du propriétaire), et
   traitement fiscal (retenues, TVA) — à fixer avec l'expert-comptable.
3. Répartition des charges communes (clés) et droits par agence.

## 10. Sécurité et packaging
Voir `SECURITE_ET_EXPORT.md` ; manifeste et empreinte SHA-256 dans `MANIFESTE.txt` de l'export.
