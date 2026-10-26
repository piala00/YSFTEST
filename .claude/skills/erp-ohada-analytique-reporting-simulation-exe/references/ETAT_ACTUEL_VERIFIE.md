# Audit documentaire rapide de l'archive reçue — 26 octobre 2026

**Base** : archive `ERP-OHADA-Commerce-Windows-Comptabilite-7-Chiffres.zip` téléversée dans cette conversation. Inspection statique de fichiers ; **aucun test d'exécution ni vérification de l'état du dépôt ou du site Render**. Indications de chemins relatifs à `ERP-OHADA-Commerce/logiciel/`.

## Composants constatés

| Fonction | Fichier(s) existant(s) | Observation / écart |
|---|---|---|
| Quatre entrées bureau | `desktop/shell.py` (`MODULES`) et `desktop/lanceur.py` | Commercial, Comptabilité générale, Comptabilité analytique, Reporting existent dans la version corrigée ; vérifier les écrans réels et droits. |
| Modules web | `apps/core/navigation.py`, `apps/core/accueil.py`, `apps/comptabilite/urls_analytique.py` | Module analytique séparé à l'écran, sources générales communes. |
| Comptabilité générale | `apps/comptabilite/models.py`, `services.py` | `Ecriture`, `LigneEcriture`, `SectionAnalytique`, normalisation de comptes à 7 chiffres et `balance_analytique`. |
| Lignes analytiques | `apps/comptabilite/models.py` | Une `LigneEcriture` a une `section` (FK), un `vehicule` (FK). La `SectionAnalytique.plan` est aujourd'hui une chaîne de caractères avec code unique global. Rien dans ce constat ne prouve un moteur multi-axes avec allocations simultanées pondérées. |
| Reporting commerce | `apps/reporting/services.py`, `views.py` | Ventes, achats, clients, balance âgée, tableau de bord, rapport commercial ; inventaire non exhaustif des états métier. |
| Reporting transport | `apps/transport/reporting.py` | Comparaison de deux périodes selon 5 axes codés : agence, gamme, ligne, véhicule, propriétaire. **Pas de preuve de dix plans consultables.** |
| Analytique Transport | `apps/transport/analytique.py` | Analyse des véhicules et propriétaires déjà disponible, à préserver. |
| Simulation | `apps/transport/management/commands/simulation.py` | Argument `--mois`, génération de dates d'un **seul mois** et appel unique `fin_de_mois` ; l'aide dit « Simule un mois ». Simulation isolée dans SQLite `simulation*.sqlite3`. |
| Simulation Windows | `deploy/windows/7-SIMULATION.bat` | Lance en dur septembre 2026 et fournit une base de démonstration, sur le port local 8001. |
| Compilation | `desktop/COMPILER.bat` | PyInstaller produit **cinq** EXE par `--onefile` : Commercial, Comptabilité, Analytique, Reporting, OHADA (lanceur). Le lanceur compilé appelle les **quatre exécutables frères** dans `desktop/shell.py:lancer_module()`. **Cela ne prouve pas qu'un seul EXE OHADA suffise, ni qu'il embarque le backend Django.** |
| Hébergement | `render.yaml`, `Dockerfile`, `deploy/` | Déploiement serveur séparé du client Windows ; garder séparation claire. |

## Points techniques à corriger / surveiller

1. Le modèle d'analyse multi-plans doit **référencer une ligne générale**, pas créer d'écritures financières dupliquées ; maintenir compatibilité FK `section`/`vehicule` pendant migration.
2. L'existence d'un champ `plan` texte et de cinq axes pour le reporting ne vaut pas mise en place des dix plans analytique Transport.
3. `simulation.py` appelle `preparer` une fois, `journee` chaque jour et `fin_de_mois` une seule fois. Étendre l'itération mensuelle et ne recréer ni capital ni société/contrats à chaque nouveau mois ; faire `fin_de_mois` à **chaque mois**.
4. Le script en place possède `--forcer` susceptible de désactiver des protections : le réserver aux tests internes et rendre impossible un lancement dangereux en production.
5. Le script `COMPILER.bat` fait `pip install pyinstaller` au moment de chaque compilation, sans pipeline de test, signature, validation de dépendances ou garantie de fichiers statiques Django. Préférer environnement reproductible, `.spec` versionné, manifest des ressources et contrôle d'intégrité.
6. `desktop/shell.py` construit les chemins des EXE frères ; pour viser un **unique** exécutable, router les modules au sein du même processus, ou maintenir un pack `onedir` complet avec plusieurs EXE clairement déclaré. Faire la distinction entre **EXE client** et **application web serveur**.
7. Certaines clés d'exemple de la simulation utilisent des préfixes comptables courts ; cela peut être compatible avec la normalisation à sept chiffres, mais doit être testé ; ne jamais renuméroter des comptes par `str.zfill` à gauche.

## Ce qui n'a pas été établi

- Schéma actuel du dépôt GitHub à la date où Claude appliquera ce Skill.
- Existence exacte des dix plans ou des exports dans un autre ERP Transport autonome.
- Compatibilité du build PyInstaller sur Windows vierge, présence des assets et de l'API.
- Conformité légale OHADA/CGI de tous les états et formules proposés.
