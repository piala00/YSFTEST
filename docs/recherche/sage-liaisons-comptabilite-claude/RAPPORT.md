# Ce qui relie les modules, et ce qui doit rester distinct

## Résultat de l’étude

Il faut analyser une liaison à cinq niveaux : identité de l’entreprise, adresse du dossier technique, partage du référentiel, traitement comptable et autorisations. Un rapprochement de noms ne démontre aucun de ces cinq niveaux à lui seul. Le registre des faits donne les résultats documentaires sans les transformer en règles universelles.

La question « créer un tiers dans Gestion commerciale le crée-t-il en Comptabilité ? » demande d’abord d’identifier l’architecture réelle. Dans un même dossier SQL, on doit vérifier le référentiel commun et les écrans accessibles ; avec un connecteur ou deux systèmes séparés, on doit vérifier une transmission, son sens et sa réussite. **Ce raisonnement est une inférence d’architecture à partir de F01, F22 et F29 ; la visibilité de tous les champs dans toutes les versions reste U04.**

## 1. Fichier, base et société

Se reporter aux faits F01 et F03–F05 pour les distinctions techniques. Ne pas considérer MAE et GCM comme nécessairement deux bases SQL indépendantes. Ne pas supposer non plus que toutes les sociétés du serveur partagent une seule base. Pour auditer un dossier, consigner l’instance, la base, les fichiers logiques, le contexte société et l’emplacement des documents.

F20 et F43 montrent deux situations différentes : nom technique distinct et initialisation d’une information depuis un dossier associé. Aucune preuve ne permet ici d’affirmer qu’un changement de nom réécrit automatiquement tous les paramètres de tous les logiciels.

**Question des noms identiques :** la recherche n’a pas établi une obligation générale d’égalité des noms SQL, noms de fichiers et raison sociale. Elle n’a pas non plus établi une condition universelle d’égalité exacte de l’activité et de la forme juridique. Un conseil de dépannage trouvé sur un forum n’a pas été retenu comme règle technique. U02 prescrit un test contrôlé de cette hypothèse.

## 2. Référentiel commun et comptabilisation

F06–F07 et F14–F15 distinguent disponibilité des données et exécution d’un traitement comptable. Pour Claude, cela implique deux chaînes fonctionnelles séparées : gérer le référentiel et produire les écritures. Une fiche tiers valide n’est pas une preuve de facture comptabilisée. Un journal d’export généré n’est pas une preuve de lot intégré.

Utiliser la cartographie pour les sens des flux. Le rapport ne déduit pas que toutes les relations sont bidirectionnelles. Les engagements, règlements, factures et calculs d’immobilisations ne doivent pas partager un même indicateur générique « synchronisé » dans l’ERP proposé.

## 3. Création et modification des tiers

Lire `CYCLE_TIERS.md`. Les faits F22, F29, F33 et F44–F45 établissent des contraintes différentes selon les produits et les opérations. Le nom commercial d’un tiers ne suffit donc pas à concevoir une clé d’échange fiable. Conserver une identité technique propre à chaque société source et une correspondance explicite vers la cible est une recommandation ERP.

Les valeurs par défaut doivent être distinguées des obligations du modèle et des autorisations de l’utilisateur. Une interface peut préremplir une information que le contrat documentaire requiert ; cela ne signifie pas que l’intégrateur doit inventer une valeur ou exécuter un INSERT direct.

## 4. Paramètres et effets dans le temps

La matrice des impacts comporte une ligne par changement à examiner. Les faits F11–F13 documentent des paramètres commerciaux précis ; ils ne permettent pas d’annoncer la rétroactivité ou la non-rétroactivité de tous les champs. Les règles de l’ERP proposé conservent donc les choix appliqués au document et demandent une action explicite pour recalculer une pièce autorisée.

Traiter séparément : tiers, article, catégorie comptable, taxe, journal, période et modèle de comptabilisation. Pour chaque nouvelle écriture ERP, conserver les paramètres effectivement appliqués. Pour une pièce historique, distinguer données originales, PDF conservé et rendu produit par une réimpression actuelle. Les effets exacts dans Sage restent à observer lorsqu’ils ne sont pas documentés.

## 5. Droits : plusieurs contrôles indépendants

F02 et F04 ne doivent pas être fusionnés : la règle du Driver Sage ODBC n’est pas celle des Objets Métiers. F32 concerne le compte, les applications et les autorisations ; F37 est historique et concerne le secret. Ni un mot de passe partagé ni l’ouverture réussie du dossier ne prouve l’autorisation de créer, transformer, comptabiliser ou payer.

La matrice des droits est une proposition de contrôle pour l’ERP. Elle sépare l’utilisateur humain, le service d’intégration, le moteur SQL et les services distants. Une protection de menu Sage ne doit pas être présumée appliquée par une connexion SQL directe ; vérifier explicitement cette frontière avant de concevoir l’extraction.

## 6. Point critique : règlements unifiés

F08–F10 sont à lire ensemble. La fiche mélange une description ancienne et une mise en garde de version. Pour une cible V12, ne pas coder le comportement ancien sur la seule phrase évoquant SQL. Prévoir la recette d’un règlement partiel, d’un règlement final, de son association et de son intégration commerciale. Tester aussi la réexécution afin d’éviter un doublon dans le système conçu par Claude.

## 7. Périmètre des autres logiciels Sage

Les lignes L03 à L16 donnent des mécanismes différents : calculs de biens, schémas de règlements, lecture de balance, export de paie, console, connecteur API, service CRM, ActiveX Batigest et lecture pour reporting. L17–L18 exposent les éléments non couverts. Les références de X3 et FRP 1000 décrivent leur comptabilité propre ; elles ne démontrent pas une passerelle vers Sage 100 Comptabilité.

Pour une extension future, exiger un contrat par couple source/cible avec version, licence, sens, déclencheur, objets, correspondance des codes, droits, mode d’échec et protocole de reprise. Ne pas créer une option unique « Liaison Sage » qui cacherait ces différences.

## 8. Limites et valeur d’utilisation

Le livrable donne une base de conception et un protocole de vérification ; il ne certifie pas une installation ni une compatibilité de production. Les types SQL physiques, les droits effectifs V12, certains comportements de propagation et l’atomicité native des transferts restent ouverts. Les références françaises servent à comprendre les mécanismes ; les comptes, identifiants légaux et exigences fiscales de l’ERP OHADA doivent être validés dans leur contexte local.

La valeur nouvelle par rapport aux dossiers précédents est l’analyse transversale des modules, des identités, des canaux et des effets du paramétrage. Les fichiers de ce paquet ont été rédigés pour ce thème ; les anciens tableaux d’écrans et de tarifs d’hébergement n’y sont pas repris.
