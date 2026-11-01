# Passation et continuité du travail (relais Claude ↔ GPT)

> **But.** Permettre à une IA (Claude ou GPT) de **reprendre le travail là où l'autre l'a laissé**,
> sans rien recommencer. Quand la limite d'usage d'une IA approche, elle **met à jour ce document**
> et le propriétaire le **colle à l'autre IA** pour continuer. Le propriétaire fait l'aller-retour.
>
> **Règle du relais.** Celui qui détient le relais : (1) lit ce document en entier ; (2) lit
> `AGENTS.md` et les docs cités ; (3) travaille ; (4) **avant de rendre la main**, met à jour la
> section « État d'avancement » et ajoute une entrée au « Journal de passation » ci-dessous.
>
> **GPT ne peut pas pousser sur GitHub depuis un chat.** Répartition réelle : GPT **conçoit, écrit
> le code et les décisions** dans le chat ; le propriétaire **relaie** à Claude ; Claude **applique,
> teste et pousse**. Inversement, Claude peut préparer une tâche que GPT affinera. Le dépôt et la CI
> restent la source de vérité.

## 1. Coordonnées du projet

- **Dépôt** : `piala00/YSFTEST` (privé).
- **Branche de travail** : **`ccr-5592a371-fusjt2`** (PAS `main`, qui ne contient que le 1ᵉʳ fichier).
  Chaque IA peut travailler sur sa branche (`gpt/<sujet>` pour GPT) et proposer par pull request vers
  cette branche ; en pratique Claude pousse directement sur `ccr-5592a371-fusjt2`.
- **Logiciel** : ERP OHADA (Cameroun), Django + Python. Deux éditions : **Commerce** (port 8000),
  **Transport** (port 8100). Plan comptable 7 chiffres ; Comptabilité générale + analytique (10 plans
  Transport). Base SQLite + miroir SQL Server (commande `miroir`).
- **Tester avant de pousser** : `python manage.py test --parallel 4` (toute la suite doit passer ;
  ~644 tests). Dire précisément ce qui a été réellement lancé.
- **CI GitHub** : workflow **« Contrôle »** (`.github/workflows/controle.yml`) : tests Linux,
  tests SQL Server 2022, et jobs Windows (compilation .exe + installateur Inno Setup + outil de
  licences). Rien n'est fusionné si un job échoue. Artefacts conservés 7 jours.

## 2. Règles non négociables (résumé d'`AGENTS.md`)

- Jamais de **données réelles** de la société dans le dépôt ; uniquement de la simulation.
- Jamais d'écriture dans une base d'un autre logiciel (Sage) : lecture seule.
- Rien d'inventé en **fiscalité/paie** ; marquer « à valider par l'expert-comptable ».
- Pour l'argent : jamais « la dernière écriture gagne » ; toute écriture analytique provient d'une
  écriture **générale validée**.
- Migrations **additives** ; migrations de données via `schema_editor.connection.alias`.
- Pas de filtre `__regex` (incompatible SQL Server) : préfixes (`startswith`).
- Textes du logiciel et messages de commit **en français**.
- Ne jamais prétendre qu'un `.exe` Windows marche sans l'avoir compilé sous Windows (la CI le fait).

## 3. Architecture d'interconnexion (le point le plus important)

Voir **`docs/INTERCONNEXION_SYNCHRONISATION.md`**. En bref : **un seul moteur** (identités stables,
lots signés idempotents), **trois canaux** (dossier partagé, relais en ligne, fichier porté), **trois
modes** combinables :
1. **Serveur central en ligne** — la direction (chef comptable, expert-comptable) se connecte de
   n'importe où par navigateur.
2. **Serveur local par agence + synchro** (hors-ligne d'abord, Tailscale) — l'épine dorsale.
3. **Import/export de fichiers** (zéro réseau ; sauvegarde fin de journée).

## 4. Dossier licences / identité éditeur (sensible — bien lire)

- **Clé privée (coffre du propriétaire)** : ne figure **JAMAIS** dans le dépôt, l'exécutable ni
  l'installateur. Ne jamais la demander, la recevoir ou la commiter.
- **Clé publique du propriétaire** (sans danger, sert seulement à *vérifier*) :
  - base64 : `L7JRWfjuNAWtOk/yEI+MZnp/NlHR02IhdFUpFCTxVrQ=`
  - empreinte SHA-256 : `DA36A89B5B432DD7CA7D03CB811F8AE806F4250A9CAA49FAEC62354488F8AD0B`
- **Mécanisme** (à respecter absolument) : le dépôt garde `apps/licences/cle_editeur.py` **VIDE**
  (`CLES = []`). L'identité n'est **PAS** gravée dans le code source : elle est **injectée à la
  compilation**. Un build personnalisé se lance par **`workflow_dispatch`** du workflow « Contrôle »
  avec les entrées `identite_publique` (base64 ci-dessus) et `empreinte_sha256` (empreinte ci-dessus).
  → artefacts `ERP-OHADA-Transport-Personnalise-Installation`,
  `ERP-OHADA-Commerce-Personnalise-Installation`, `ERP-OHADA-Licences-PROPRIETAIRE`.
  *(Graver la clé en dur dans `cle_editeur.py` casse la CI : les builds de test injectent une identité
  fictive et refusent si une vraie clé est déjà présente. Déjà arrivé, déjà corrigé.)*
- **Deux méthodes d'installation** (côté client) : fichier `.erplic` signé, ou clé d'activation
  collée. L'étape « clé » refuse désormais un champ vide (corrigé).

## 5. État d'avancement (à tenir à jour à chaque passation)

**Logiciels produits** : ERP Transport (~85 %), ERP Commerce (~70 %, adaptation reportée),
Gestionnaire de licences (~90 %), outils installateur (~90 %), Simulateur autonome (~15 %, à bâtir).
Le passage à « livré » pour les ERP = **test Windows du propriétaire** avec son identité.

**Fait récemment (session Claude du 01/11/2026)**
- Adoption de la base Codex comme socle de `ccr-5592a371-fusjt2` (commit `90aeed5`).
- Q2 « report automatique des absents » ré-appliqué (option Paramètres transport).
- Correctif installateur : l'étape « clé » refuse un champ vide (`controle.py` + `erp_ohada.iss`).
- Doc d'architecture d'interconnexion créé.
- Identité : clé publique du propriétaire reçue et vérifiée (empreinte OK) ; mécanisme d'injection
  au build confirmé (voir §4). Dépôt laissé **sans clé gravée** (correct).

**En cours**
- Produire les installateurs **personnalisés** (identité du propriétaire) via `workflow_dispatch`,
  puis donner au propriétaire les liens des 3 artefacts à tester (les 2 méthodes d'activation).

## 6. Backlog priorisé (avec contexte)

- **P0 — Livraison test Windows** : build personnalisé (§4) → le propriétaire installe, signe un
  `.erplic` avec son coffre, active par les deux méthodes. C'est la validation qui fait passer à « livré ».
- **T-24** (à faire valider par le propriétaire avant de coder) : la recette d'un **point de vente
  intermédiaire** va à la **prochaine agence encore ouverte** qui encaisse, pas à l'agence de
  rattachement fixe (cas Bertoua→Ndokayo). Touche la compta → spec à confirmer. Réf :
  `docs/CONCEPTION_DEPART_COMPTABILISATION.md` Q4.
- **T-23** : écran « Comptabilisation / transfert » façon Sage avec **barre de progression** ; garder
  l'automatique. Réf Q3 du même doc. À cadrer : quel traitement afficher (synchro agences↔direction ?
  miroir SQL Server ? re-vérification ?).
- **F-BKP-03** : sauvegarde de **fin de journée** d'une agence **→ direction**, en un geste, via le
  canal import/export (teste le système de sauvegarde). S'appuie sur `apps/core/sauvegarde.py` + échanges.
- **Mise en ligne du serveur central (Mode 1)** : procédure d'hébergement sécurisé (HTTPS, auth,
  licence) pour l'accès navigateur de la direction. Préférer Tailscale à l'exposition publique.
- **G-SIM-04/05** : simulateur **autonome** multi-agences avec imprévus (logiciel séparé, comme le
  gestionnaire de licences). La simulation existe déjà *dans* l'ERP (commande + société importable).

## 7. Comment rendre la main (checklist)

1. Mettre à jour §5 (état) et le backlog §6 si besoin.
2. Ajouter une entrée au Journal ci-dessous : date, sens (Claude→GPT ou GPT→Claude), ce qui a été
   fait, la **prochaine étape précise**, et tout code/décision produit (ou son emplacement).
3. Si du code a été écrit hors dépôt (dans un chat GPT), le **joindre intégralement** pour que Claude
   l'applique et le teste ; ne jamais résumer du code à appliquer.
4. Ne jamais inclure la clé privée / le coffre.

## 8. Journal de passation

| Date | Sens | Fait | Prochaine étape |
|---|---|---|---|
| 2026-11-01 | Claude (en cours) | Q2, correctif installateur clé vide, doc interconnexion, identité vérifiée et mécanisme d'injection confirmé (dépôt sans clé gravée). Retour arrière de la gravure en dur (CI re-verte). | Lancer le build personnalisé par `workflow_dispatch` (§4) une fois la CI du push verte, puis donner au propriétaire les liens des installateurs à tester. |
