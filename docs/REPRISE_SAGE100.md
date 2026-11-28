# Reprise d'un dossier Sage 100 SQL Server dans l'ERP

Référence : skill `sage100-sql-server-structure-v5-v12` (catalogue documentaire du manuel « Structure des bases
Sage 100 V12.20 »). **Sage n'est jamais modifié** : on lit, on exporte en CSV, l'ERP importe.

## Ce qui est repris (tout le dossier : comptabilité et gestion commerciale)

| Données | Table Sage | Dans l'ERP |
|---|---|---|
| `depots` | F_DEPOT | Dépôts (le dépôt principal Sage devient le dépôt principal) |
| `familles` | F_FAMILLE | Familles d'articles (type 0 uniquement) |
| `comptes` | F_COMPTEG | Plan comptable (comptes de détail ; comptes de total ignorés) |
| `journaux` | F_JOURNAUX | Journaux : achats, ventes, trésorerie (avec compte), général → OD ; situation exclue |
| `sections` | F_COMPTEA | Plans et sections analytiques (même code dans deux plans : préfixé du n° de plan) |
| `taxes` | F_TAXE | Taux de taxes (sens, taux, compte) |
| `tiers` | F_COMPTET | Clients et fournisseurs, compte collectif, payeur, catégorie tarifaire, plafond d'encours |
| `articles` | F_ARTICLE | Articles, famille, suivi de stock, prix |
| `tarifs` | F_ARTCLIENT | Prix par catégorie tarifaire (tarifs propres à un client signalés, non repris) |
| `stocks` | F_ARTSTOCK | Stock d'ouverture par dépôt, valorisé au coût Sage, mini / maxi |
| `ecritures` | F_ECRITUREC | Écritures de l'exercice en cours jusqu'à la bascule, **ligne à ligne** : pièces, libellés, tiers, **lettrage** ; norme nationale, journaux de situation exclus |
| `analytique` | F_ECRITUREA | Ventilations analytiques (premier plan : l'ERP a une section par ligne) |
| `documents`, `lignes` | F_DOCENTETE, F_DOCLIGNE | Pièces en cours (devis, commandes, BL non facturés, retours…), factures non soldées, et historique depuis la date choisie ; **n° Sage conservé**, ni stock ni écriture générés |
| `echeances` | F_DOCREGL | Échéance et reste dû de chaque facture |
| `reglements`, `imputations` | F_CREGLEMENT, F_REGLECH | Règlements non imputés : « en attente de rattachement » ; part déjà réglée des factures |
| `soldes` | F_ECRITUREC | Variante : soldes d'ouverture seuls (si les écritures détaillées ne sont pas reprises) |

Non repris : gammes, lots et séries, tarifs propres à un client, budgets, pièces archivées, fabrication.

## Synchronisation pendant la transition, puis bascule (U7)

Ce n'est pas un import unique : l'ERP devient une **copie synchronisée** du dossier Sage, puis le remplace.

1. **Choix du dossier** (ERP › Fichier › *Reprise d'un dossier existant*) : **serveur** (ordinateur), puis **instance
   SQL** (détectée par le registre Windows sur le poste local et par le service SQL Server Browser, UDP 1434, sur le
   réseau ; vide = instance par défaut ; saisie libre si la détection échoue), puis **base de données** (liste des bases
   de l'instance qui contiennent un dossier, avec la raison sociale lue dans P_DOSSIER). Le dossier synchronisé est
   mémorisé (`ORDINATEUR\INSTANCE/BASE`) et reproposé ; un autre est refusé.
   **Simulation** : rapport complet, rien n'est enregistré.
2. **Première synchronisation** (taper `SYNCHRONISER`) : la société passe en mode *copie synchronisée* (badge orange
   dans la barre du haut, avec l'heure de la dernière synchronisation). La saisie continue dans Sage ; l'ERP refuse
   les validations de pièces, règlements, opérations de caisse, inventaires et écritures, pour éviter les doubles
   saisies. Consultation, états et contrôles sont disponibles.
3. **Synchronisations suivantes** : à la main (même bouton) ou automatiquement toutes les heures
   (`6-SYNCHRONISATION-AUTOMATIQUE.bat`, commande `python manage.py synchroniser_dossier` : même serveur, instance et
   base que la première synchronisation ; compte SQL éventuel : `SYNCHRO_UTILISATEUR`, `SYNCHRO_MOT_DE_PASSE` dans `.env`). Chaque passage
   reporte les **créations, modifications et suppressions** : fiches mises à jour ; écritures et pièces comparées par
   clé d'origine et empreinte (seules celles qui ont changé sont refaites, le n° ERP est conservé) ; stock aligné
   par des ajustements tracés ; une facture qui a disparu de la liste des non soldées est soldée, une pièce en cours
   transformée dans Sage est marquée transformée. Un passage non conforme est annulé en entier.
4. Chaque passage (simulation ou synchronisation, manuel ou automatique) est consigné : date, données jusqu'au,
   conformité, volumes créés · mis à jour · supprimés, rapport complet (tableau *Derniers passages*).
5. **Bascule** : arrêter la saisie dans Sage, synchroniser une dernière fois, vérifier, puis taper `BASCULER`.
   La bascule exige que le dernier passage soit une synchronisation conforme. La synchronisation s'arrête
   définitivement, la saisie s'ouvre dans l'ERP ; l'événement est inscrit au journal d'audit.

Un poste ne synchronise qu'un dossier : un autre dossier est refusé (pas de mélange). Le nom « Sage » n'apparaît
pas dans le logiciel (« ancien logiciel », « dossier d'origine »).

## Deux façons de lire Sage

1. **Lecture directe (recommandée)** : ERP › Fichier › *Reprise d'un dossier existant* (administrateur), ou
   `python manage.py reprise_sage --serveur .\INSTANCE --base DOSSIER --debut-exercice 2026-01-01 --date-bascule 2026-10-31`.
   L'ERP lit d'abord les colonnes présentes (INFORMATION_SCHEMA), n'exécute que des SELECT (toute autre instruction est
   refusée par le code) et se connecte en `ApplicationIntent=ReadOnly`.
2. **CSV** : `python manage.py reprise_sage --sql` donne le script d'export ; un fichier par donnée, puis `--dossier`.

Jeu de test fictif : `apps/core/reprise_sage/exemple_sql/base_sage_fictive.sql` (base Sage fictive à monter sur un
SQL Server de test) et `apps/core/reprise_sage/exemple_complet/` (les mêmes données en CSV, utilisées par les tests).

## Procédure

1. **Sur une copie de test du dossier Sage**, avec un compte SQL en lecture seule : ouvrir
   `apps/core/reprise_sage/export_sage100_lecture_seule.sql` (ou `python manage.py reprise_sage --sql`),
   régler `@DebutExercice` et `@DateBascule`, exécuter, enregistrer chaque grille dans le CSV indiqué.
2. Toutes les colonnes figurent au catalogue V12.20. Sur une version plus ancienne, si une colonne facultative
   n'existe pas, la retirer de la requête (les obligatoires sont listées par `--correspondance`).
3. Dans l'ERP (base neuve, `init_erp` fait, exercice ouvert à la date de bascule) :

       python manage.py reprise_sage --dossier exports --date-bascule 2027-01-01

   C'est une **simulation** : rien n'est enregistré. Lire le rapport.
4. Rapprocher avec Sage à la même date : balance générale (totaux = `soldes.csv`), balance des tiers,
   inventaire valorisé (quantité et valeur = contrôles « stock » du rapport).
5. Quand tout est conforme : relancer avec `--appliquer` (et `--rapport reprise.txt` pour garder la trace).
   Si un contrôle est en écart, l'import est annulé en entier.
6. Recommencer sur la base réelle le jour de la bascule. L'import est rejouable : les fiches sont mises à jour,
   le stock et les soldes d'ouverture ne sont jamais passés deux fois.

Jeu d'exemple fictif : `apps/core/reprise_sage/exemple/`.

## Contrôles du rapport

- Quantité totale et valeur du stock : Sage (F_ARTSTOCK) = ERP après reprise.
- Équilibre des soldes Sage : total débit = total crédit, sinon blocage.
- Soldes repris dans le journal AN = soldes nets de `soldes.csv`.
- Anomalies ligne par ligne : stock négatif, article ou dépôt inconnu, compte hors plan SYSCOHADA (non
  numérique ou classe 0), tiers inconnu dans les soldes, plusieurs dépôts principaux.

## Points de prudence (skill)

- Statut des colonnes : « DOCUMENTÉ V12.20 » = présent dans le manuel V12.20, **pas** observé sur votre
  installation ; « À CONFIRMER » = absent du catalogue. Les versions V5 à V11 ne sont pas attestées.
- `stocks.csv` reprend AS_QteSto seule : ne pas y ajouter quantités réservées, commandées ou préparées (RGX001).
- `soldes.csv` part du **premier jour de l'exercice en cours** (à-nouveaux compris). Partir du début du dossier
  compterait deux fois les exercices clôturés.
- `soldes.csv` prend la **date comptable** (période JM_Date + jour EC_Jour), pas EC_Date qui est la date de
  saisie ; il garde la norme nationale (EC_Norme 0 ou 1, jamais l'IFRS seule) et écarte les journaux de
  situation (JO_Type = 4). Ces filtres sont déduits du manuel V12.20 (skill `sage100-sql-hebergement`) :
  la comparaison avec la balance Sage les valide. Bascule conseillée en début d'exercice.
- CT_Encours est un plafond, pas un solde : le solde de chaque tiers vient des écritures.

## Correspondance des colonnes

```

depots.csv ← F_DEPOT
  DE_No           obligatoire DOCUMENTÉ V12.20  C067         Code du dépôt
  DE_Intitule     obligatoire DOCUMENTÉ V12.20  CX071        Intitulé
  DE_Principal    facultatif  DOCUMENTÉ V12.20  CX077        Dépôt principal (1 = oui)
  DE_Ville        facultatif  DOCUMENTÉ V12.20  CX075        Ville

familles.csv ← F_FAMILLE
  FA_CodeFamille  obligatoire DOCUMENTÉ V12.20  C068         Code famille
  FA_Intitule     obligatoire DOCUMENTÉ V12.20  CX001        Libellé
  FA_Type         facultatif  DOCUMENTÉ V12.20  C069         Seul le type 0 (famille de détail) est repris

comptes.csv ← F_COMPTEG
  CG_Num          obligatoire DOCUMENTÉ V12.20  C085         Numéro de compte
  CG_Intitule     obligatoire DOCUMENTÉ V12.20  M01 V12.20   Intitulé du compte

tiers.csv ← F_COMPTET
  CT_Num          obligatoire DOCUMENTÉ V12.20  C070         Code tiers
  CT_Intitule     obligatoire DOCUMENTÉ V12.20  M01 V12.20   Raison sociale
  CT_Type         obligatoire DOCUMENTÉ V12.20  M01 V12.20   0 = client, 1 = fournisseur ; les autres types sont ignorés
  CG_NumPrinc     facultatif  DOCUMENTÉ V12.20  M01 V12.20   Compte collectif
  CT_Ville        facultatif  DOCUMENTÉ V12.20  M01 V12.20   Ville
  CT_Telephone    facultatif  DOCUMENTÉ V12.20  M01 V12.20   Téléphone
  CT_EMail        facultatif  DOCUMENTÉ V12.20  M01 V12.20   E-mail
  CT_Sommeil      facultatif  DOCUMENTÉ V12.20  M01 V12.20   1 = en sommeil (repris inactif)
  CT_NumPayeur    facultatif  DOCUMENTÉ V12.20  M01 V12.20   Tiers payeur (égal à CT_Num quand le tiers règle lui-même)

articles.csv ← F_ARTICLE
  AR_Ref          obligatoire DOCUMENTÉ V12.20  C058         Référence
  AR_Design       obligatoire DOCUMENTÉ V12.20  C060         Désignation
  FA_CodeFamille  facultatif  DOCUMENTÉ V12.20  C059         Famille
  AR_SuiviStock   facultatif  DOCUMENTÉ V12.20  CX015        0 = sans suivi de stock, autre valeur = suivi
  AR_Sommeil      facultatif  DOCUMENTÉ V12.20  IX006        1 = en sommeil (repris inactif)
  AR_PrixAch      facultatif  DOCUMENTÉ V12.20  M01 V12.20   Prix d'achat HT
  AR_PrixVen      facultatif  DOCUMENTÉ V12.20  M01 V12.20   Prix de vente HT

stocks.csv ← F_ARTSTOCK
  AR_Ref          obligatoire DOCUMENTÉ V12.20  C061         Article
  DE_No           obligatoire DOCUMENTÉ V12.20  C062         Dépôt
  AS_QteSto       obligatoire DOCUMENTÉ V12.20  CX032        Quantité en stock (ni réservée, ni commandée : règle RGX001)
  AS_MontSto      obligatoire DOCUMENTÉ V12.20  CX033        Valeur du stock : coût d'entrée = AS_MontSto / AS_QteSto
  AS_QteMini      facultatif  DOCUMENTÉ V12.20  CX030        Stock minimum du dépôt
  AS_QteMaxi      facultatif  DOCUMENTÉ V12.20  CX031        Stock maximum du dépôt

soldes.csv ← F_ECRITUREC
  CG_Num          obligatoire DOCUMENTÉ V12.20  C080         Compte général
  CT_Num          obligatoire DOCUMENTÉ V12.20  C081         Compte tiers (vide si aucun)
  Debit           obligatoire DOCUMENTÉ V12.20  C077 + C078  Somme EC_Montant où EC_Sens = 0
  Credit          obligatoire DOCUMENTÉ V12.20  C077 + C078  Somme EC_Montant où EC_Sens = 1
```
