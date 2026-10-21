---
name: sage100-objets-metiers-v5-v12
description: "Expert Sage 100 Objets Métiers (SDK COM) V5–V12, introspection locale, lecture/écriture métier, transactions, authentification, compatibilité et tests."
---

# Sage 100 Objets Métiers — intégration COM et modèle métier

## Rôle
Utiliser le **SDK Sage 100 Objets Métiers** lorsque le besoin dépasse les lectures SQL : créer une pièce, gérer un règlement, enregistrer un tiers, appliquer les validations métier. Ce n'est **pas** simplement un module d'interface Windows et ce n'est **pas** une API REST générique. Le nom exact des COM ProgIDs, interfaces, propriétés et méthodes dépend du SDK installé : ne jamais les inventer.

## Source primaire
La bibliothèque technique Sage contient le « Manuel des objets métiers », les « Modifications Objets Métiers », « Manuel sur les programmes externes » et les structures SQL : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020. Le manuel référencé au 21/10/2026 contient une révision « V12 Objets métiers v12.25 » (lien de PDF Sage sous accès variable). Toujours suivre la version du poste.

## Démarche obligatoire
1. Obtenir l'installateur et la documentation SDK autorisés correspondant **à chaque build** V5–V12, licence, environnement Windows et version Sage.
2. Inspecter les références TypeLib enregistrées, GUID, versions, bitness 32/64, ProgIDs avec `resources/outils/inventaire_com_windows.py` — **aucune création d'objet ni ouverture de dossier**.
3. Relever les interfaces, classes, factories, énumérations et signatures depuis le manuel et des définitions de types réellement installées ; produire `interfaces.csv` versionné. **Ne pas deviner les noms des méthodes.**
4. Environnement de test : société fictive, comptes de service à droits minimes, sauvegarde et isolation.
5. Décrire, pour chaque opération : constructeur/connexion (d'après manuel), préconditions, validations, comportement persistance/transactions, messages, fermeture, rollback et éventuelles conséquences (stock/compta).
6. Développer un adaptateur par version, avec tests idempotence, collisions, conflits de période, pertes réseau, factures dupliquées, et mécanismes de reprise.
7. Aucune écriture directe SQL dans des tables Sage comme solution de contournement.

## Cas de test SDK nécessaires
- Connexion société autorisée ; fermeture/libération des références COM et erreurs d'authentification.
- Lire référentiel client/article ; créer/modifier sans casser les clés/comptes associés.
- Générer devis/commande/livraison/facture ; chaîne et numérotation Sage ; tarifs et taxes.
- Retour/avoir, document lié, stock corrigé selon règles.
- Création écriture comptable équilibrée, journal fermé, exercice clos, validation.
- Tentative doublon, permissions insuffisantes, produit bloqué, client solvabilité dépassée.
- Transactions partielles et sortie avec erreur : état durable et traces vérifiées.

## Standards connecteur ERP
Composant Windows isolé (`sage_adapter_host`), file de commandes, événements signés, journal de corrélation, clés d'idempotence, sérialisation si requise par licence/SDK, horodatage et remontée d'erreurs non tronquées. Retenter seulement les opérations idempotentes ou celles dont l'absence de résultat a été prouvée. Ne jamais supposer qu'un COM est thread-safe ou utilisable en service sans validation.

## Interop Python
Pour Python Windows, `pywin32`/`comtypes` sont des pistes techniques, à valider contre la bibliothèque officielle. Si application 64 bits et composants uniquement 32 bits : passer par un service hors-process approprié plutôt que présumer leur compatibilité. Documenter les ProgIDs exacts depuis le registre local.

## Preuves requises
Version SDK, composant installé, GUID, signature exacte, références officielles, résultat de test, écritures/stock dans Sage, erreur gérée et rollback. Sans cette preuve, une méthode SDK est **À VÉRIFIER**.

