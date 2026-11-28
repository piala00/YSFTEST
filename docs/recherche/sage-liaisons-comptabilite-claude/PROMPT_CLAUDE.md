# Instruction à transmettre à Claude avec ce dossier

Étudie ce dossier pour améliorer la liaison entre les modules de mon ERP OHADA privé et sa comptabilité. Préserve les menus, options, calculs et données existants. Ce travail ne concerne pas le projet officiel de consolidation Sage de GTC.

Commence par README.md, RAPPORT.md et le registre FAITS_DOCUMENTES.csv. Retrouve les sources et leur version dans SOURCES.csv. Les sources sans build ne prouvent pas V12, les guides historiques ne constituent pas une certification actuelle et les mécanismes X3/FRP 1000/Sage 50 ne sont pas ceux de Sage 100.

Analyse ensuite les liaisons, le cycle des tiers, les impacts du paramétrage société et la matrice des droits. Distingue les faits Sage des propositions ERP. Ne déduis pas une synchronisation automatique de tous les champs ni une liaison universelle de tous les produits.

Avant de coder, examine le code actuel et livre :

1. Un tableau correspondance « exigence / code existant / manque / modification proposée / preuve ou décision ERP ».
2. Un modèle explicite pour société juridique, agence, dossier technique, module et connecteur, avec nom affiché distinct de la clé de liaison.
3. Les règles de création et modification des tiers : identité, unicité, rôle, collectif, payeur, catégorie, autorisations et conservation de l’historique.
4. Les droits de configuration, consultation, création, validation, comptabilisation, export, approbation et paiement, contrôlés côté serveur par société et dans les tâches différées.
5. Le cycle de production comptable, les rapprochements, la prévention des doublons, la gestion d’échec partiel et la reprise après interruption.
6. Les changements limités nécessaires et des tests métier adaptés aux scénarios du dossier.

N’invente ni champs SQL physiques, ni FK, ni passerelle native. Ne modifie aucune base Sage par SQL. Si une intégration réelle à Sage est demandée, fais vérifier sa version, son canal, ses droits et sa compatibilité avant toute écriture. Ne transforme pas les exemples français en règles OHADA ou en obligations fiscales camerounaises.

Conserve les questions d’INCONNUES ouvertes jusqu’à preuve. Les scénarios fournis n’ont pas été exécutés sur Sage. Explique ce que tu peux réaliser dans l’ERP à partir du contrat proposé et ce qui exige encore une observation native.
