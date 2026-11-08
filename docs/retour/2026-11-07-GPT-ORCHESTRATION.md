# Réorganisation exécutable — GPT — 7 novembre 2026

## Audit vérifié

Référence : `407da8d59fb9b4caace3c32e7d820757288b5a6a`.
Les 10 derniers commits ajoutent des scénarios au même fichier
`tests/test_cloture_django_migree.py`. Le commit précédent branche ce scénario
dans la CI : ce sont des preuves supplémentaires, pas dix fonctionnalités livrées.
La CI [407](https://github.com/piala00/YSFTEST/actions/runs/42419157487)
contient 9 jobs réussis, dont deux partitions SQL Server, les deux éditions
Windows et l'activation compilée. Une étape ignorée n'est pas un test réussi.
Les erreurs SQL historiques ne sont pas déclarées résolues sur cette seule base.

Le workflow `controle.yml` ne déclenche pas les pushes `agent-*`.
Les pull requests déclenchent les contrôles. Les branches spécialisées doivent
donc fournir une PR vers `ccr-5592a371-fusjt2`, sans fusion automatique.
Le workflow SQLite spécialisé omettait les tests `tests/test_cloture*` de ses filtres.

## Sortie P0.3 proposée

Validation uniquement pour un SHA précis, jamais au nombre de commits :

1. Clôture N vers N+1 sur deux bases Django migrées : source inchangée,
   bilan d'ouverture rapproché, reports par tiers/axes et résultat équilibrés.
2. Référentiels, droits et historique Transport conservés ; écritures historiques
   non dupliquées ; catalogue et liens de dossiers cohérents.
3. Échec injecté / déséquilibre : annulation sans publication partielle ni perte
   du catalogue ; relance et conflit de destination contrôlés.
4. Suite `p03` complète verte, suite Django verte et CI complète du même SHA verte.
   Toute preuve manquante reste « à vérifier », sans nouveau micro-commit cosmétique.
5. Rapport QA avec commandes, codes retour, logs, SHA et anomalies restantes.
   Approbation humaine avant fusion ; aucune livraison implicite.

Ce document ne prononce pas la sortie P0.3. L'audit doit rapprocher chaque critère
des assertions existantes et signaler les trous précis avant d'ajouter des tests.

## Lots indépendants et contrats de travail

Les branches existent ; cela ne prouve aucune exécution d'assistant.
Vérification GitHub : les six pointent toutes sur `bbcf7a6d14eb4d8d0b7e14e25c278b5ee5d321cb`.
Comparaison à la référence : 11 commits de retard, aucun commit propre ; seulement
le workflow général et le scénario Django migré diffèrent. Aucun assistant
spécialisé n'est lancé par cette livraison. Les bases doivent être actualisées
par une opération explicitement revue, sans fusion automatique dans cette mission.
Avant travail : comparer chaque branche à la référence courante ; ne jamais
réinitialiser une branche divergente. Rapporter son SHA et ses changements propres.

| Branche | Lot et périmètre exclusif | Dépendance / preuve attendue |
|---|---|---|
| agent-audit-avancement | critères, matrice de preuves, docs/retour | lecture de tous les lots ; aucun changement métier |
| agent-qa-tests | sortie P0.3, tests transverses, CI et orchestration | autres lots fournissent leurs tests unitaires ; rapport par SHA |
| agent-comptabilite-ohada | rapprochement générale/analytique/reporting | comptes et fiscalité à valider par expert ; suite ohada |
| agent-sqlserver-donnees | compatibilité migrations et miroir | bases fictives seulement ; deux partitions CI, logs des crashs |
| agent-transport-metier | recette billets/colis/caisse et quotas interagences à spécifier | suite transport ; aucun changement du moteur de clôture |
| agent-windows-ux | parcours installation/mise à jour/désinstallation, messages | compilation Windows et preuves des deux éditions ; pas d'annonce sur test source seul |

Programme de Claude retrouvé dans l'issue #1 :
https://github.com/piala00/YSFTEST/issues/1#issuecomment-6467185601
Le lot 03 concerne le reporting Transport manquant ; le lot 04 est la recette
P0 des écritures, clôtures, ventes de billets et documents ; le lot 05 concerne
les menus sans action. Le lot 04 exige refus GET, droits 403, période clôturée,
double soumission et équilibre des écritures, puis correction des anomalies.
Réutiliser les travaux existants et les graphiques `data-graphique`.
La correspondance entre le libellé récent P0.4 et ce lot 04 n'est pas prouvée,
mais ce programme constitue le périmètre de travail retrouvé, sans lui substituer
les quotas ou immobilisations. Les scénarios indépendants sont répartis entre
comptabilité, Transport et QA ; seul le lot données modifie les migrations communes.

Chaque lot livre un ensemble cohérent code + tests + rapport dans une PR.
Pas de commit horaire obligatoire, pas de commit sans résultat nouveau,
pas de rebase/force-push des branches d'autrui. Ne pas fusionner ni déployer.

## Exécution sans secret ni fournisseur IA

Depuis la racine du checkout du lot (Python et requirements installés) :

```
python outils/orchestration.py p03
python outils/orchestration.py p03 --execute --jobs 1
python outils/orchestration.py ohada transport --execute --jobs 2
python outils/orchestration.py qa --execute --jobs 1
```

Le mode par défaut montre les commandes ; `--execute` lance des tests locaux,
pas des agents. Logs et rapport JSON sont regroupés dans un dossier horodaté
`work/preuves`. Environnements temporaires distincts, timeout et échecs propagés.
Chaque développeur utilise son checkout indépendant ; aucun checkout ni push
concurrent dans un même répertoire. SQL Server et Windows restent validés par
la CI existante sur des machines adaptées. Aucune clé OpenAI/Claude présumée.

## Correctifs issus de l'exécution locale

`verifier_base_sqlite` utilisait le contexte transactionnel d'une connexion sans
la fermer. Sous Windows, la base restait verrouillée et l'annulation échouait
avec WinError 32. Utilisation de `contextlib.closing` pour libérer le fichier.
Le test de ventilation compare désormais les lignes sans imposer leur ordre
d'insertion : les montants et axes restent strictement contrôlés.
Le workflow spécialisé couvre Linux et Windows et conserve les rapports P0.3.
Les scénarios de test fermaient eux aussi leurs connexions trop tard pour le
nettoyage Windows : fermeture explicite en conservant le contexte transactionnel.
Le scénario Transport minimal comptait deux fois les référentiels Transport dans
son remplacement des constantes ; les groupes sont désormais distincts.

Validation locale : Python 3.12, Windows, Django 6.1.3 dans un environnement
isolé. Après correctifs : **45 tests P0.3 réussis en 117,228 secondes**.
Les deux tests du lanceur réussissent. Aucun EXE recompilé localement.
La suite Django complète a terminé : **721 tests en 490,015 secondes,
14 erreurs et 17 ignorés**, code retour 1. Les erreurs ne sont pas toutes
des tests distincts : certaines se produisent aussi au nettoyage.
P0.3 reste ouvert tant que la suite et la CI du nouveau SHA ne sont pas vertes.

Travaux immédiatement attribuables à partir des diagnostics :

| Branche | Travail de suivi précis |
|---|---|
| agent-qa-tests | fermer les connexions des fixtures dans `tests_catalogue_societes`, `tests_miroir`, `tests_dossiers_parcours` ; rejouer les classes concernées sous Windows |
| agent-windows-ux | diagnostiquer les fichiers verrouillés dans `tests_executable` (restauration, rotation, sauvegardes) ; distinguer fuite du test et fuite du programme avant correction |
| agent-sqlserver-donnees | diagnostiquer `tests_base_donnees.BaseSQLiteTests.test_etat_verifier_reparer_et_changer_de_moteur` ; vérifier l'isolation des sous-processus et les environnements |

Ces erreurs Windows n'autorisent pas à conclure que la CI Linux actuelle est
rouge, ni que cette modification les a introduites : comparaison au parent
encore nécessaire. Le premier passage complet était en cours pendant les
corrections de fixtures P0.3 ; il constitue un diagnostic, pas une validation
immuable de tous les fichiers finaux. Aucune publication distante effectuée.
Le registre détaillé est conservé sur `gpt/pilotage-registre-demandes`, sous
`docs/pilotage/PLAN_DIRECTEUR.md`, et non dans le checkout courant. Relier chaque
lot aux exigences existantes de l'issue #24 avant d'ajouter un nouvel identifiant.

## Cinq automatisations : contraintes et limites d'accès

## Livraison du 8 novembre — validation complémentaire

Le lot ferme aussi explicitement les connexions des fixtures catalogue,
exécutable et miroir. Les chemins Windows des scénarios de changement de moteur
sont interpolés avec `repr`, pour éviter les échappements `\U` invalides.
La suite complète après ces corrections : 721 tests en 486,521 secondes,
5 échecs, 3 erreurs et 18 ignorés. Les 14 erreurs du premier passage ne
réapparaissent pas. Les huit échecs actuels présentent des refus de création
de liens (`os.link`, WinError 5) ou de connexion locale (WinError 10013).
Ils ne sont pas ignorés ni transformés en succès. La relance locale avec droits
étendus a été refusée par la politique de la session. Livraison en PR brouillon
explicitement demandée par le propriétaire ; validation CI complète encore
requise avant toute acceptation. Aucun installateur de production validé n'est
déduit de ces résultats locaux.

## État des automatisations

L'ancien chat décrit développement horaire, surveillance/livraison, QA quotidien,
coordination Claude et rapport hebdomadaire. Ce sont cinq rôles programmés,
pas cinq développeurs simultanés. Leur configuration et leur état actuels ne sont
pas accessibles ici : aucun `automations/*/automation.toml` local retrouvé.
Aucune tâche supprimée, désactivée ou modifiée ; aucune fréquence inventée.

Contrats recommandés à appliquer après lecture des vraies configurations :
développement = consommer un lot et livrer un résultat cohérent ; surveillance =
lecture CI et alerte sur changement, jamais fusion/déploiement ; QA = preuves du
SHA et diagnostic, sans réécrire les lots ; coordination = transmettre seulement
si canal et autorisation réels, sinon consigner le blocage ; hebdomadaire = bilan
des livrables et obstacles, sans nouveau commit de remplissage. Conserver les
identifiants, horaires, tâches et préférences de notification de l'utilisateur.
