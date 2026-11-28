# U7 — Synchroniser une société Sage entière, puis basculer vers l’ERP

## Exigence confirmée

Le 24 octobre 2026, l’utilisateur exige une reprise complète et liée de Gestion commerciale et Comptabilité Sage dans son ERP : « importer tout », dont plans de tiers, journaux et plans analytiques, puis continuer à utiliser le logiciel. Ce besoin n’est pas satisfait par un import clients/articles/soldes ni par une archive consultable seule. Une reprise partielle peut servir de lot technique mais ne peut être présentée comme la livraison finale demandée.

## Clarification U7 : synchronisation, puis remplacement

L’utilisateur précise ensuite qu’il s’agit de synchroniser les données Sage de gestion commerciale et comptabilité, afin que l’utilisateur puisse abandonner Sage et poursuivre dans l’ERP. Cette clarification prévaut sur l’idée d’un import ponctuel. « Toutes les solutions commerciales » étend le besoin aux périmètres réellement utilisés ; établir l’inventaire des produits et modules. Ne pas prétendre qu’un connecteur Sage 100 couvre automatiquement Sage X3, Paie ou un autre produit.

Le sens proposé pour réaliser ce besoin est Sage → ERP durant la transition, suivi d’un basculement où l’ERP devient le système de saisie. Aucune demande de réécriture vers Sage ou de synchronisation bidirectionnelle permanente n’est confirmée. La fréquence, les produits/versions exacts et la durée de coexistence restent à arrêter. Le fonctionnement hors ligne de l’ERP doit rester possible après la bascule.

## Cycle de synchronisation proposé

1. Définir un connecteur par produit/version/schéma réellement présent, les périmètres et la propriété des objets. Préserver le dossier Sage en lecture seule pour le connecteur ; toutes les transformations et écritures se font dans la zone de préparation puis l’ERP.
2. Réaliser un chargement initial cohérent de toute la société, pas seulement des soldes. Établir un instant de référence et une méthode éprouvée pour ne perdre aucune modification survenue pendant ce chargement (snapshot puis delta cohérent ou interruption contrôlée). Ne pas supposer que des dates de modification existent sur chaque table.
3. Synchroniser ensuite créations, modifications, annulations et suppressions autorisées. Vérifier les capacités réellement disponibles : suivi de changements SQL, journaux ou comparaison de snapshots ; ne pas activer CDC/Change Tracking sur la production sans conception et autorisation adaptées. Un simple filtre « date supérieure au dernier passage » ne constitue pas une garantie exhaustive.
4. Donner à chaque objet une clé source stable (produit, dossier, type, identifiant) et une correspondance cible ; utiliser lots, versions/empreintes et points de reprise durables. Relancer le même lot ne crée ni nouvelle facture ni nouveau reçu. Ne pas comparer seulement les noms ou numéros de pièce, réutilisables entre journaux/exercices/agences.
5. Intégrer des ensembles cohérents : en-tête et lignes, pièce et transformations, facture et lien comptable, règlement et affectations. Ne publier comme utilisable aucun ensemble incomplet ; conserver les dépendances en attente et signaler l’état de synchronisation. Valider durablement avant d’avancer le point de reprise. Une arrivée dans un ordre différent ne doit pas perdre la relation.
6. Traiter les annulations comme des faits métier traçables ; ne pas supprimer des pièces ERP historiques par cascade sur simple absence d’un export filtré. Distinguer vraie suppression source, filtre et échec d’extraction. Préserver les preuves et règles de clôture.
7. Pendant la coexistence, proposer un périmètre miroir en consultation ou des règles de propriété strictes : pas de modifications concurrentes libres des mêmes pièces dans Sage et l’ERP. Des essais ERP se font dans un environnement séparé. Si une double saisie opérationnelle est demandée, spécifier la résolution métier des conflits avant de l’activer ; ne pas appliquer « dernier écrit gagnant » aux données financières.
8. Afficher par dossier/module le dernier lot reçu ET appliqué, son instant métier, erreurs, volumes et retard. « Connexion réussie » n’est pas « société synchronisée ». Après interruption, reprendre sans doublons et relancer des contrôles complets périodiques.
9. Préparer une bascule à blanc puis une fenêtre finale : arrêter les nouvelles saisies Sage, achever les synchronisations, contrôler les états et reliquats, ouvrir la saisie dans l’ERP. Geler la source Sage pour la consultation/archivage. Ne pas laisser un ancien connecteur écraser ensuite les opérations créées dans l’ERP ; toute correction tardive devient une procédure contrôlée.
10. Prouver l’autonomie : l’ERP doit savoir exploiter tous les objets repris sans appel obligatoire à Sage, à ses exécutables ou à ses Objets Métiers pour l’activité normale. Vérifier les PDF, éditions, règles comptables, stocks, historiques et droits ; conserver les archives et moyens de consultation requis. Ne pas promettre la suppression immédiate de toute installation/licence Sage sans vérifier les dépendances et obligations applicables.

### Recette spécifique de synchronisation, proposée et non exécutée

Charger une société puis modifier une fiche, livrer partiellement un BC, comptabiliser une facture, affecter un règlement, modifier une ventilation analytique et annuler une pièce autorisée dans Sage ; vérifier la propagation exacte de chaque ensemble et de ses liens. Répéter les lots, couper le réseau, interrompre le chargement et le reprendre ; aucun double effet de stock, caisse ou écriture. Tester une suppression réelle versus un objet absent d’un export filtré. Vérifier les écritures liées créées après leur facture, les corrections, documents personnalisés et pièces jointes. À la bascule, déconnecter la source Sage puis créer/livrer/facturer/régler et produire les états dans l’ERP seul. Tant qu’un objet obligatoire est indisponible opérationnellement, la bascule complète reste bloquée et n’est pas annoncée livrée.

## Faisabilité et limite actuelle

La migration est réalisable en principe par extraction, correspondances et chargement contrôlé. Une sauvegarde SQL Sage n’est pas directement une base utilisable par un ERP au modèle différent. Aucune migration complète n’a été développée ni exécutée dans cette livraison. L’existence d’un schéma documentaire V12.20 ne prouve ni le schéma réel V9/V10 d’un client ni la prise en charge par notre ERP de chaque fonction Sage. Définir les éditions, versions, modules, personnalisations et dossiers réellement présents avant de certifier la couverture.

## Inventaire obligatoire de couverture

Les lignes suivantes sont un périmètre métier à inventorier, pas une liste de tables physiques observées. Évaluer chaque élément présent et ses relations.

| Domaine | Contenu à reprendre et vérifier |
| --- | --- |
| Société | Identité, coordonnées, identifiants, devises, exercices, périodes, paramètres, numérotations, établissements/agences, options et champs personnalisés. |
| Comptes généraux | Plan comptable complet, intitulés, options de suivi, comptes collectifs et correspondances. Préserver les codes comme chaînes, sans renumérotation implicite. |
| Tiers | Plan tiers clients/fournisseurs/autres, comptes rattachés, contacts, adresses, banques, conditions de paiement, plafonds et échéances, statuts, représentants et informations libres. |
| Journaux | Codes, types, intitulés, comptes de contrepartie, numérotation et paramètres des journaux. |
| Comptabilité | Écritures et lignes, pièces et références, exercices historiques disponibles, reports et à-nouveaux, échéances, lettrages partiels/complets, devises, taux, rapprochements bancaires et états de validation/clôture disponibles. |
| Analytique | Plans/axes, sections, hiérarchies si présentes, modèles de répartition, pourcentages, ventilations effectives par écriture, budgets et réalisations si présents. Ne pas reprendre uniquement les libellés des axes. |
| Taxes et modèles | Taux, comptes, règles, registres disponibles, modèles de saisie, abonnements et automatismes. Traduire leur logique vers le moteur ERP ; ne pas exécuter des automatismes Sage importés comme du code de confiance. |
| Articles | Familles, références, codes-barres, unités et conversions, conditionnements, gammes, tarifs et remises, fournisseurs, catégories comptables/tarifaires et règles de taxes. |
| Stocks | Dépôts/emplacements, mouvements, stocks et valeurs, réservations, lots/séries et péremptions si présents, inventaires, transferts et transit. Conserver quantités et valeurs par unité et date de reprise. |
| Achats/ventes | Devis, BC, BL, factures, retours, avoirs et documents internes disponibles ; en-têtes, lignes, statuts, quantités livrées/facturées restantes, transformations et liens entre pièces. |
| Règlements | Reçus, versements, avances, affectations, reliquats non imputés, moyens de paiement, trésoreries, liens aux factures/BC et aux écritures comptables. Un versement réel reste unique. |
| Autres référentiels | Commerciaux/collaborateurs, transporteurs, ressources et objets réellement utilisés, selon modules présents. Ne pas assimiler Paie, Immobilisations ou X3 à des tables forcément incluses dans un dossier Sage 100 Gescom/Comptabilité. |
| Preuves et états | Pièces jointes, PDF, liens documentaires et modèles d’impression ; modèles d’états et rapports personnalisés à convertir. Vérifier les fichiers externes, pas seulement le contenu SQL. |
| Utilisateurs et droits | Identités historiques, groupes et habilitations à rapprocher des rôles ERP. Traduction contrôlée des droits, comptes réinitialisés ou identité fédérée appropriée ; ne pas promettre de réutiliser les mots de passe Sage. |
| Traçabilité | Identifiants source, auteur et dates disponibles, validation/annulation et historique réellement stocké. Si l’auteur d’origine est absent, afficher « non disponible dans la source », conserver l’importateur séparément, ne pas inventer d’auteur. |

Prévoir pour chaque objet : source réelle, volume, dépendances, cible, règle de conversion, contrôle, statut (repris et utilisable / à adapter / bloqué / absent source), preuve et décision. Une archive brute conserve la preuve mais ne remplace pas la disponibilité opérationnelle exigée. Ne pas accepter silencieusement une ligne rejetée ni clore la migration tant qu’un périmètre obligatoire reste bloqué.

## Architecture proposée

1. **Diagnostic** : reconnaître produit/version/édition, moteur SQL, schémas et types réels, dossiers liés, exercices, extensions et fichiers externes. Utiliser le Skill sage100-sql-hebergement pour le protocole de lecture seule ; ne pas imposer ses colonnes V12.20 à une base V9.
2. **Copie cohérente** : sauvegarde et restauration dans un environnement isolé, avec pièces documentaires nécessaires et test de restauration. Conserver une source de référence datée. Un fichier .bak est à restaurer dans SQL Server compatible avant extraction ; il ne se charge pas directement dans PostgreSQL/SQLite. Ne pas donner au navigateur un accès administrateur à SQL Server ; prévoir un agent/importateur autorisé à proximité de la copie.
3. **Extraction** : lire la copie ou une connexion source limitée à la lecture, inventorier aussi paramètres et éléments hors base. Choisir extraction SQL documentée et/ou interfaces Sage adaptées au périmètre et licences ; un export standard ne garantit pas tous les objets. Préserver types, décimales, codes, encodages et dates ; journaliser les anomalies.
4. **Zone de préparation** : conserver valeurs source et correspondances stables société/dossier/objet/identifiant. Transformer sans modifier Sage. Détecter références orphelines, doublons, valeurs invalides et objets non couverts.
5. **Chargement dépendant** : référentiels société/exercices/comptes/journaux/analytique et tiers/articles, puis documents/lignes/mouvements/écritures, enfin relations, affectations, lettrages et justificatifs. L’ordre exact dépend du schéma réel. Chargements transactionnels, reprenables et idempotents, avec identifiants de lot.
6. **Recette** : rapprocher les états et totaux Sage/ERP sur la même date, le même périmètre et les mêmes règles. Échantillonner les liens métier et tester l’usage réel d’une société migrée.
7. **Bascule** : migration à blanc, traitement des écarts, sauvegarde, arrêt de saisie Sage pour la bascule finale, extraction finale cohérente ou delta prouvé, derniers contrôles puis ouverture ERP. Une fois de nouvelles opérations saisies dans l’ERP, un retour à Sage nécessite une procédure de reprise de ces opérations ; une ancienne sauvegarde seule ferait perdre ces nouvelles opérations.

L’import des historiques ne doit pas appeler aveuglément les validations ordinaires : elles risquent de recréer stock, écritures et trésorerie. Distinguer documents déjà comptabilisés, mouvements et écritures importés, documents non comptabilisés et reliquats opérationnels. Les pièces soldées historiques peuvent rester protégées ; les commandes non livrées, factures non réglées et mouvements restant à traiter doivent continuer normalement selon leurs états importés.

## Contrôles indispensables proposés

- Par exercice/journal/compte : volumes, débits, crédits, balance, à-nouveaux et égalité des états avec la source. Un équilibre débit/crédit seul ne prouve pas que tout a été repris.
- Par tiers et facture : reste dû, avances, échéanciers, lettrages et règlement partiellement affecté ; comparer auxiliaires et collectifs, signaler les écarts source sans les corriger en silence.
- Par axe/section : allocations et résultats analytiques ; aucune ventilation perdue par reprise du seul plan.
- Par article/dépôt/lot : quantités, valeurs, réservations et transit. Ne pas additionner le stock d’ouverture de bascule et l’ensemble des anciens mouvements comme deux apports de stock.
- BC partiellement livré/facturé, retour/avoir et paiement : continuité des reliquats et liens, absence de deuxième encaissement ou mouvement.
- Facture déjà comptabilisée : consultation du lien vers l’écriture, sans nouvelle comptabilisation. Pièce non comptabilisée : traitement futur uniquement selon statut vérifié.
- Dates de clôture et permissions conservées selon la cible ; on ne rouvre pas implicitement l’historique Sage parce qu’il est importé.
- PDF/justificatifs : ouverture réelle depuis la facture et l’écriture, pas seulement un chemin Windows devenu invalide.
- Relancer le même lot après interruption : aucune duplication ; réconciliation des volumes et erreurs ; aucune ligne disparue sans justification.
- Après reprise, créer un nouveau document, livrer un reliquat, régler une ancienne facture, éditer balance et rapport commercial ; vérifier la numérotation et les incidences une seule fois.

Tous ces tests sont proposés et non exécutés. Pour confirmer une reprise complète d’une société, fournir le rapport exhaustif des objets, les écarts résolus et les preuves sur une copie réelle.

## Sources officielles consultées le 24 octobre 2026

S1 — Structure Sage 100 V12.20, publication mise à jour juillet 2026 : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113095648937 . Référence documentaire de départ, pas certification de couverture ni observation de la base client.
S2 — Sauvegarder/restaurer depuis Sage 100, fonctions disponibles depuis 100c 2.00 : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=211010150079345 . L’assistant sauvegarde la société ouverte pour les applications concernées ; cela ne réalise pas une conversion vers notre ERP.
S3 — Formats d’import Sage versionnés : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=211010160114075 . Les formats Gescom et Comptabilité diffèrent selon version ; aucun export universel exhaustif vers notre ERP n’est établi.
S4 — Documents PDF dans Sage Partner Cloud : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230323140847923 . Dans ce contexte, les PDF sont dans un répertoire externe et FILESTREAM n’est plus utilisé. Inventorier le mode réel de stockage au lieu d’imposer une seule règle à toutes les installations.
