# Menus05.1 — consolidation de l'inventaire existant

Codex, 31 octobre 2026. Q-002 / ANO-P-001, coordination #24 et #1. Lot documentaire uniquement, sans nouvel inventaire ni nouvelle analyse Sage.

## Résultat

La matrice globale ne contenait que son en-tête. Elle reprend désormais les **427 identifiants distincts** du recensement Commercial déjà livré : 227 commandes terminales, 25 conteneurs de menus, 175 occurrences HTML. Aucun nouvel identifiant et aucun doublon ajouté. Un conteneur n'est pas compté comme une commande terminale ; les contextes HTML distincts ne sont pas supprimés au motif qu'ils portent le même libellé.

Le CSV historique `RECENSEMENT_BOUTONS_COMMERCIAL.csv` reste inchangé, SHA-256 `2b253f46727ddb052707338a511b26a20fd93a2cedb98026c4ef4cc30680fb17`. Les colonnes originales de la matrice restent en place ; trois colonnes ajoutent le snapshot contenant la source (`ae724335`), le fichier et la ligne CSV d'origine. Ce snapshot identifie la version du fichier réutilisée, pas une nouvelle exécution de son générateur. Chaque ID permet de retrouver toutes les données d'origine sans les recopier intégralement.

Les champs inconnus (méthode HTTP, vue, effets métier, rôle, preuve Sage) restent à qualifier. Une cible est reprise comme route uniquement si elle est un chemin déclaré. Les anciens marqueurs `DOC-V12` restent des marqueurs historiques, sans certifier un comportement Sage par action. Les états historiques « grisé », « inactif » ou « non testé » ne deviennent pas des anomalies actuelles confirmées.

Quatre entrées sont reliées aux preuves partielles déjà disponibles : **BC-00273** validation et **BC-00276** annulation des documents (#28), **BC-00367** rattachement et **BC-00377** enregistrement des règlements (#30). Leurs méthodes, services et tests sont tracés ; les limites SQL de #30 restent celles de sa PR. Ces liens ne remplacent ni le parcours de toutes les variantes d'interface, ni la comparaison avec Sage.

## Contrôles exécutés

Lecture aller-retour avec le parseur CSV Python ; 427 lignes et 427 ID uniques ; identifiants, ordre, libellés et chemins rapprochés ligne par ligne avec la source ; références de lignes 2 à 428 ; empreinte source inchangée ; quatre liens de preuves partielles ; `git diff --check` réussi. Aucun nouveau test logiciel, parcours navigateur ou relevé Sage n'est revendiqué pour cette consolidation documentaire.

Les **427 lignes restent `A_TESTER_ERP`**, même celles possédant une preuve partielle. **Zéro `CONFORME_PROUVE`.** La matrice n'est plus vide ; l'audit global reste incomplet : autres modules, contextes d'activation, droits, preuves navigateur et comportements Sage restent à couvrir par lots. Aucune exhaustivité ni acceptation propriétaire déduite de ces nombres.

Aucune fusion, aucun déploiement ni donnée de production modifiée.
