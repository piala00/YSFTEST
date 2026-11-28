# Portée et lecture des types

Ce dossier répond à R12 et R13. Les 20 colonnes explicitement nommées dans R12 sont présentes dans le catalogue ; des clés et champs de contrôle complètent la reprise. Le filtre universel de simulation n’est pas établi. Les types physiques et l’état de l’ERP en ligne n’ont pas été inspectés.

## Trois niveaux à conserver

| Niveau | Exemple | Ce qui est établi |
|---|---|---|
| Manuel Sage | `CT_Intitule`, chaîne, maximum 69 | Structure logique V12.20, M01 PDF 56 |
| SQL du dossier | type système, octets, précision, collation, NULL | À relever avec MS01 ; non observé ici |
| Modèle ERP | choix PostgreSQL et règles métier | Décision de développement et recette, pas une définition Sage |

`Numérique : Entier` ne prouve pas à lui seul `smallint`, `int` ou `bit`. `Réel double` n’est pas une attestation du DDL installé. Le manuel décrit aussi une couche d’accès et des champs virtuels. Un indice `cbIndice` ne doit pas devenir aveuglément une colonne SQL. Les métadonnées SQL donnent des octets pour `max_length` ; elles ne se confondent pas avec le nombre maximal de caractères utilisateur. La nullabilité et un champ obligatoire dans l’application sont deux notions distinctes. Sources : M01 et MS01.

Les pages du CSV sont les pages PDF comptées dès la couverture, suivies de la pagination imprimée. M01 a 447 pages, couverture V12.20, actualisation juillet 2026. Les symboles, longueurs et domaines sont des faits techniques ciblés ; le manuel n’est pas redistribué dans le paquet.

## Conséquences pour l’ERP

Conserver les identifiants comme texte. Garder séparément valeur brute source, valeur normalisée et motif de rejet. Choisir explicitement précision et arrondi des montants dans l’ERP après relevé source et contrôle de totaux ; ne pas déclarer ce choix comme type natif Sage. Ne pas tronquer un libellé pour forcer un import. Les comptes de total ne doivent pas recevoir les écritures de détail.

`CT_ControlEnc` présente les codes 0 automatique, 1 selon risque, 2 bloqué ; les valeurs internes de l’ERP « aucun / avertir / bloquer » ne sont donc pas une correspondance numérique directe certifiée. `CG_Lettrage` est une option du compte, pas une lettre de rapprochement. `AR_UniteVen` vaut un indice 1 à 30, pas « kg » ou « carton ». `N_CatTarif` vaut un indice 1 à 32. Sources : M01, pages indiquées dans le catalogue.

Les contraintes documentaires ajoutées peuvent éclairer le dossier d’écrans de l’étape 3, mais ne prouvent ni leur disposition ni les astérisques visibles. Ce dossier ne remplace aucun catalogue déjà livré. Il ne réalise pas la consolidation officielle de GTC et ne modifie pas l’ERP privé.
