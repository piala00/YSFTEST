# Passation / continuité — 2026-11-03

Document de reprise pour continuer le travail dans une nouvelle conversation (fenêtre
de contexte pleine). À coller en entier à l'IA qui reprend.

## Projet
- ERP OHADA (Cameroun), Django + Python. Deux éditions : **Commerce** (port 8000) et
  **Transport** (port 8100). L'édition est décidée par `settings.ERP_EDITION`
  (vide = dev/tests = tout monté ; "transport" / "commerce" = ce logiciel seul).
- Dépôt GitHub : **piala00/ysftest**. Branche de travail : **`ccr-5592a371-fusjt2`**
  (PAS `main`). Tout est commité et poussé à ce jour (HEAD = 626786a).
- Règles non négociables : `AGENTS.md` (français, données fictives seulement, rien
  d'inventé en fiscalité/paie, migrations additives, pas de `__regex`, ne jamais
  prétendre qu'un .exe Windows marche sans l'avoir compilé sous Windows).
- Mandat propriétaire : perfectionner le logiciel jusqu'à la livraison, pousser sur la
  branche, fusionner les PR Codex seulement si CI « Contrôle » verte + revue favorable.
  Autorisé à fusionner/déployer sans redemander (responsablement). Focus TRANSPORT.
- Lanceur compilé : `deploy/executable/erp_ohada.py` + `erp_ohada.spec`. Installateur
  Inno Setup : `deploy/installateur/erp_ohada.iss`. CI : `.github/workflows/controle.yml`.
- Avant de pousser : `python manage.py test --parallel 4` (toute la suite doit passer).

## Sécurité / licences (à respecter)
- Clé PUBLIQUE du propriétaire (base64) : `L7JRWfjuNAWtOk/yEI+MZnp/NlHR02IhdFUpFCTxVrQ=` ;
  empreinte SHA-256 : `DA36A89B5B432DD7CA7D03CB811F8AE806F4250A9CAA49FAEC62354488F8AD0B`.
  **Ne JAMAIS commiter ni transmettre le coffre privé.** La clé est injectée au build
  (workflow_dispatch de controle.yml avec inputs identite_publique + empreinte_sha256),
  jamais gravée dans le dépôt (`cle_editeur.CLES` reste vide).
- Build personnalisé du propriétaire : run 244 vert ; artefacts
  `ERP-OHADA-Transport-Personnalise-Installation`, etc. (expirent ~7 jours).

## Travail fait cette session (tout poussé)
- Ergonomie : saisie billet/colis en 2 colonnes (tout visible) ; saisie d'écriture façon
  Sage (cellules plates + journaux de caisse auto-contrepartie) ; **filtrage progressif**
  (combobox) dans tous les champs liste (`static/js/filtrage_liste.js`) ;
  écran **Comptabilisation (mise à jour)** avec barre de progression.
- T-24 : reversement de recette vers une caisse encore ouverte (à l'approbation).
- F-BKP-03 : sauvegarde de fin de journée agence → direction (chiffrée, boîte aux lettres).
- Correctif CI : le workflow « Contrôle » était cassé au démarrage (YAML : `:` dans un
  libellé d'étape) depuis la séparation — réparé ; CI de nouveau verte (run 243).
  **Correctif guichet** : le contrôle navigateur attendait une fenêtre de 380 px → 740 px
  (saisie 2 colonnes) ; assertions ajustées.
- Audit de cohérence « transport » : masqué « Contrôle de la liaison commerciale » en
  transport ; « Clients en compte » déplacé de Billetterie vers Colis.
- **Refonte démarrage façon Sage** (doc `docs/PROCEDURE_DEMARRAGE_SAGE.md`) :
  - **D1 ✅** premier démarrage vide, sans connexion → accueil « Créer / Restaurer une
    société » (`core:demarrage`, `templates/core/demarrage.html`). Middleware
    `PremiereConfigurationMiddleware` redirige vers `core:demarrage` tant qu'aucun admin.
  - **D2 ✅** création réordonnée : identité → rôle → base → **compte administrateur à la
    FIN** (`core:installation`, étape `compte` ; la base est appliquée à ce moment).
    L'assistant est accessible sans connexion (local) tant qu'aucun admin ; `installation.html`
    utilise le bloc public. Tests `apps/core/tests_premier_demarrage.py` réécrits.
  - **D3 ✅** essai 30 ouvertures : sauvegarde/restauration verrouillées sans licence (déjà
    en place via `fonctions_pro_disponibles`) + action **« Effacer la société »** (repartir
    à zéro, dans Administration du poste, confirmation EFFACER, local).
  - **D4 ✅** **Restaurer une société** au premier démarrage (`core:restaurer_societe`) :
    activer la licence (code ou .erplic) puis restaurer une sauvegarde .json, sans créer
    de société. Page de confirmation `templates/core/restauration_ok.html`.
  - **D5 ✅** multi-agences : déjà couvert par `apps/echanges/lots.py`
    (`ajouter_agence` crée le rang/compte de liaison + clé ; `fichier_installation` exporte ;
    l'agence importe via le rôle « agence » de l'assistant). Le fichier sort toujours du siège.
  - **D6 (logiciel) ✅** la **clé d'installation n'est plus exigée** :
    `licence.cle_installation_requise()` renvoie False ; l'essai marche sans clé ; contrôle
    par la licence. Tests licences adaptés.

## EN COURS / À REPRENDRE EN PRIORITÉ
1. **D6 (installateur) — EN ATTENTE DE L'IDÉE DU PROPRIÉTAIRE.** Il a dit : « l'installation
   se fait AVEC la clé d'installation, j'ai une idée pour la clé d'installation ». **Il faut
   d'abord lui demander son idée** (qui génère la clé, ce qu'elle vérifie — société/édition/
   postes/date, code court ou fichier, liée ou non à la licence). Aujourd'hui l'installateur
   `erp_ohada.iss` exige une **autorisation signée .erpinst** (PageAutorisation + vérification
   hors ligne) ; la CI teste le refus sans autorisation (`Refuser-Sans-Autorisation`). Selon
   son idée : adapter le .iss + le lanceur + la CI, puis recompiler (workflow_dispatch) pour
   validation Windows par lui. **Ne rien changer au .iss avant son idée.**
   NB : D6 logiciel a mis `cle_installation_requise()`=False ; si son idée réexige la clé à
   l'installation, réactiver au niveau installateur et régler le logiciel en conséquence.
2. **Bug « rien ne fonctionne » sur SON installation Windows** (séparé de la refonte). Le code
   marche (vérifié en DEBUG=0 : menus, fenêtres, vente d'un billet OK). Cause probable : cache
   navigateur ou service non redémarré après mise à jour. Il doit envoyer **une photo de l'écran
   ou F12 → Console** pour trancher. Toujours ouvert.

## Backlog restant (non prioritaire)
- G-SIM-04/05 : cadrer le simulateur autonome (terrain réel).
- Recompilation finale du setup une fois D6 tranché.
- Commerce : adaptation/ergonomie à reporter plus tard (après Transport).

## Comment reprendre
- Lire ce fichier + `docs/PROCEDURE_DEMARRAGE_SAGE.md` + les derniers commits.
- `python manage.py test --parallel 4` doit passer.
- Démo locale façon compilé : `ERP_EDITION=transport ERP_ASSISTANT=1 DEBUG=0` +
  `runserver --insecure` sur une base migrée → `/` redirige vers `/demarrage/`.
- CI/recompilation : workflow `controle.yml` (push ou workflow_dispatch avec la clé publique).
