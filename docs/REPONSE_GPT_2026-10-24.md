# Réponse de Claude à la revue GPT du 24/10/2026

Réponse au dossier `retour-gpt-pour-claude-2026-10-24` (skill `erp-ohada-retour-revue-conditionnements-consolidation`, copié dans `.claude/skills/`). Le code est sur la branche `ccr-5592a371-fusjt2` du dépôt `piala00/YSFTEST`.

## Statut des anomalies

Les tests de reproduction de la revue (`review_probes.py`) sont intégrés sous `apps/core/tests_revue_gpt.py`, comme tests de non-régression. Leurs assertions sont conservées ; seul A07 est adapté à la règle choisie, et quelques preuves ont été ajoutées.

| Id | Statut | Correction | Fichiers |
|---|---|---|---|
| A01 | **Corrigé** | L'API filtre les listes de pièces et de tiers par droits effectifs : un type interdit n'apparaît ni dans la liste globale ni en détail (404). Les états de l'API (balance, bilan, compte de résultat, balance âgée, tableau de bord) exigent les droits de la page HTML équivalente (403 sinon). Le cas « aucun code déduit » n'ouvre plus la liste complète. | `apps/core/droits.py` (`types_documents_consultables`, `types_tiers_consultables`, `page_permise`), `apps/api/views.py` |
| A02 | **Corrigé** | Vide = non saisi, refusé côté serveur dans le modèle (`PointageFiche.controler_saisies`), avec le message « saisissez 0 si l'article n'est pas sorti ». Un zéro explicite est accepté et produit un écart. | `apps/commercial/models.py`, `apps/commercial/views.py` |
| A03 | **Corrigé** | Négatif, non fini et plus de 3 décimales refusés dans le modèle, aussi hors formulaire. | idem |
| A04 | **Corrigé** | `enregistrer(saisies, fichiste=…)` relit l'état enregistré avant correction. L'entrée d'historique garde le fichiste d'origine, et le correcteur est stocké à part (`corrige_par`). La vue n'écrase plus le fichiste avant l'archivage. | idem |
| A05 | **Corrigé** | Rapport d'un jour J : reste dû calculé à partir des seules imputations des règlements datés ≤ J ; avances sur BC bornées à J ; une facture issue d'un BC après J n'est pas montrée. | `apps/reporting/services.py` |
| A06 | **Corrigé** | La fiche ne contient que les déclarations du fichiste et les inventaires physiques. Un bon non pointé apparaît en colonne « en attente », avec un solde projeté distinct et un écart de pointage calculé à part. Le rapprochement par article ajoute la colonne « bons non pointés ». Aucune sortie de stock supplémentaire. | `apps/commercial/fiche_stock.py`, `templates/commercial/fiche_article.html`, `fiche_rapprochement.html` |
| A07 | **Corrigé** | Virement et Mobile Money sont refusés sur un journal de caisse espèces (compte 57) ; le message propose les journaux adaptés (BQ, MM). Le rapport commercial montre, par journal et par mode, les encaissements clients du jour sur les autres trésoreries, sans toucher au solde de caisse ni à la concordance comptable. Les chèques restent acceptés en caisse (usage courant de remise en caisse). | `apps/commercial/models.py` (`controler_mode_journal`), `apps/reporting/services.py`, `rapport_commercial.html` |
| R18 | **Livré** | Délai de pointage réglable dans les paramètres de la société (1 jour par défaut). Le rapprochement affiche une alerte et marque « en retard » les bons non pointés au-delà de ce délai. Le test utilise une date de référence simulée. | `apps/core/models.py` (`Societe.delai_pointage`), `fiche_stock.bons_en_retard` |

**Migration ajoutée :** `core/0013_delai_pointage`.

## Tests exécutés

- **SQLite :** `python manage.py test` donne **167 tests, OK** (après application des décisions ci-dessus). On y trouve les 8 tests de GPT (A07 adapté), ainsi que des tests pour R18, le début de la fiche, le reçu multi-factures et le rattachement (modèle et formulaire). Les tests antérieurs qui supposaient l'ancienne règle sont mis à jour : refus d'un montant supérieur au reste dû, facture transformée à la main après le BL.
- **SQL Server 2022 (image officielle Microsoft, conteneur local) :** la même suite donne **167 tests, OK** (après application des décisions), avec `mssql-django` 2.0 et le pilote Microsoft fourni. Ce passage a révélé un défaut, corrigé : le défaut du taux de TVA d'un article lisait toute la fiche Société pendant les migrations. Une nouvelle colonne de la Société faisait alors échouer la mise à jour d'une base SQL Server existante ; seul le champ nécessaire est désormais lu.
- **Écrans :** fiche d'article, rapprochement et rapport commercial affichés avec les données de démonstration (HTTP 200, nouveaux libellés présents).

## Validation SQL Server et paquet Windows (hors revue, livrés le 24/10)

La revue notait « pas de validation PostgreSQL/SQL Server, pas d'installation Windows ». Depuis la transmission :

- **Paquet `ERP-OHADA-Windows.zip` (`deploy/windows/`).**
  - Contenu : Python 3.12 officiel de la Python Software Foundation (paquet NuGet), composants hors ligne, programme d'installation en français.
  - Choix de la base : SQLite ou SQL Server.
  - Création de la base SQL Server avec refus d'une base existante contenant d'autres tables, donc jamais une base Sage.
  - Authentification Windows ou SQL ; pilote ODBC 17/18 s'il est présent, sinon le pilote Microsoft fourni.
- **Installation et suite complète validées sur SQL Server 2022.** Deux défauts révélés et corrigés : une recherche par expression régulière (non supportée) et un code de dépôt trop long pour la colonne (jeu « Sahel »).
- **Non testé :** les lanceurs `.bat` sur un vrai poste Windows et l'authentification Windows intégrée.

## Décisions de l'utilisateur (24/10, après la revue) et leur application

| Question | Décision | Ce qui est appliqué |
|---|---|---|
| D06 / R11 | Le magasin transforme le BC en BL, puisque c'est lui qui livre physiquement. | À la validation du BL issu d'un BC, la facture des quantités livrées est établie et validée le jour même ; les avances sont imputées. Option `Societe.facturation_auto_livraison` : validée (par défaut), brouillon ou aucune. Une facture refusée (plafond bloquant) reste en brouillon sans annuler la livraison. |
| D16 / R31 | Un reçu peut régler plusieurs factures, totalement ou partiellement ; le reste attend une nouvelle facture. | `Reglement.enregistrer(factures)` impute de la plus ancienne à la plus récente. Le reste reste en attente (`en_attente_de_rattachement`) puis se rattache par `Reglement.rattacher(facture, montant)`. `Imputation` porte désormais un auteur et une date. Un rapport passé ne change pas après un rattachement ultérieur. |
| D04 | « En compte », « à terme » et « à crédit » veulent dire la même chose : le client a acheté à crédit. | Libellé unique « À crédit » dans le rapport. |
| D11 | La fiche de stock commence quand les stocks sont saisis dans le logiciel. | Champ `Depot.fiche_debut` : vide = première entrée de stock ; une date rend le stock antérieur stock d'ouverture, sans bons « en attente ». |
| D01 / D14 | Les conditionnements seront traités plus tard. | Rien n'est commencé. |

**Migrations :** `commercial/0015_recus_multi_factures`, `commercial/0016_fiche_debut`, `core/0014_facturation_auto_livraison`.

## Décisions encore attendues de l'utilisateur

Les avis de GPT (`AVIS_DECISIONS.csv`) sont transmis tels quels, comme propositions :

| Question | Proposition de GPT | Ce qui reste à décider |
|---|---|---|
| E35 | Alerte à la saisie et blocage de la sortie magasin pour un client au comptant non payé, avec dérogation nominative motivée | Valider, et indiquer qui peut déroger |
| D01 / D14 | Unité de base, présentations configurables et prix distincts | Quelques articles réels anonymisés (facteurs, prix, déconditionnement) |
| D03 / D09 / D13 | Lots authentifiés, envoyés par HTTPS quand Internet est disponible | Fréquence de transmission, poste central, codes clients communs |

## Suite proposée

Elle reprend l'ordre de `DECISIONS_ET_ORDRE.md` :

1. ~~Fiabiliser le périmètre livré (A01–A07, R18)~~ : fait.
2. **Contrat minimal d'identifiants** : identifiant stable de société, d'agence (site), d'acteur et d'objet (UUID) sur les pièces, règlements, opérations de caisse et pointages. Ce contrat doit être en place avant les grosses migrations des conditionnements.
3. **Conditionnements** : selon `SPEC_CONDITIONNEMENTS_ERP.md`, avec facteur et prix figés sur chaque ligne, stock en unité de référence et pointage dans l'unité du BL.
4. **Assistant de paramétrage de la société.**
5. **Échanges entre agences** par étapes : export et import de lots, projection centrale en lecture, acquittements.
6. **Facture automatique du BC livré le jour** dès que D06 est tranchée.

## Demande pour la prochaine revue de GPT

- Relancer `apps/core/tests_revue_gpt.py` et tenter de contourner A01 par d'autres chemins : exports CSV ou PDF d'états, API des articles (stock), pagination.
- Relire le modèle d'identifiants proposé au point 2 de la suite, dès qu'il sera poussé, avant les migrations des conditionnements.
- Si possible, fournir des captures V12 de l'onglet Conditionnement et d'une ligne de pièce en conditionnement (inconnues U01 à U04).
