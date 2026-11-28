---
name: erp-transport-caisses-multi-agences
description: Mettre à jour l'ERP Transport Afrique Centrale pour gérer un nombre configurable de caisses par agence (une caisse partagée dans une petite agence, plusieurs caisses spécialisées au siège ou en grande agence), les sessions, paiements, transferts internes, rapprochements et rapports journaliers simples, avec droits, comptabilité OHADA et synchronisation offline-first. Utiliser pour chaque besoin de trésorerie/caisses par service, centralisation, clôture, reversement ou multi-agences.
---

# Caisses multi-agences — mise à jour du projet ERP Transport Afrique Centrale

## Décision utilisateur validée

- **Chaque agence a une configuration indépendante du nombre de caisses**, sans limite « petite/grande/siège » codée en dur.
- Petite agence : en général **une seule caisse commune** à la billetterie, aux courriers/bagages et aux opérations autorisées d'autres services.
- Grande agence : **plusieurs caisses facultatives** selon organisation, service ou usage.
- Agence installée au siège : **plusieurs caisses possibles** (billetterie, courrier, garage, centrale, etc.) et la direction peut superviser la trésorerie ; **ne pas confondre agence du siège et direction centrale**.
- Chaque service reste autonome dans son module. Le **service auteur d'une opération** est distinct de **la caisse qui l'encaisse ou la paye**. Une dépense garage n'est pas nécessairement payée par la caisse garage ; une facture n'est pas un décaissement.
- **Rapport journalier d'agence = tableaux faciles à lire** avec billetterie, bagages, colis séparés, sorties, encaissements et situation caisse, plus un récapitulatif **par caisse** si plusieurs caisses. Une petite agence ne doit pas afficher un tableau artificiel de 5 caisses vides.
- Consolidation siège : toutes les caisses des agences, mais les transferts internes ne créent **ni recettes d'exploitation ni nouvelles dépenses**.
- Séparer flux espèces / banque / Mobile Money. La notion de caisse physique est indépendante des comptes de paiement électroniques, même s'ils sont contrôlés par un même caissier.

## Invariants critiques

1. `service_id` ≠ `cashbox_id` ≠ `agency_id` ≠ `payment_account_id` ; ne jamais les fusionner dans le modèle de données.
2. Une opération métier validée a un ID immuable et des pièces sources. Les règlements associés ont leur propre ID. Un fait payé une fois n'est jamais payé deux fois par réessai ou synchronisation.
3. Les caisses sont créées et affectées à une entité légale/agence, avec état, devise, droits, responsables, sessions et historique de changements.
4. Toute **mouvance d'espèces** est attribuée à une caisse source/destination identifiable. Un virement bancaire ou règlement Mobile Money ne modifie pas le contenu physique d'une caisse.
5. Transfert de caisse à caisse : une sortie source + une entrée destination sous **un même `transfer_id`**, sans recette ou charge d'exploitation. Cycle d'état contrôlé, gestion « en transit » en cas de réception tardive.
6. Dépenses proposées par les services et paiements réalisés sont deux événements différents : `expense_approved` ne donne pas automatiquement `cash_disbursed`.
7. Session par caissier et/ou plage de travail suivant paramétrage ; ouverture, comptage, clôture, écarts et validations traçables.
8. Séparer **rapport activité/départs** de **rapport trésorerie/encaissements** ; un billet payé hier et transporté aujourd'hui n'est pas encaissé deux fois.
9. Chaque caisse locale continue les opérations qu'elle a autorité d'effectuer hors connexion, journal d'événements sécurisé et réconciliation idempotente au siège.
10. Les rôles direction/chef d'agence/comptabilité contrôlent droits de visibilité, de caisse et opérations exceptionnelles, côté API et base de données.

## Consulter les références spécialisées

1. [Configuration des agences, types de caisses et rôles](references/01-organisation-caisses-agences.md)
2. [Chaînes métier interservices et mouvements de caisse](references/02-workflows-mouvements-transferts.md)
3. [Règles comptables, moyens de paiement et formules](references/03-comptabilite-rapprochement.md)
4. [Rapport journalier agence une/multi-caisses](references/04-rapport-journalier-simple.md)
5. [Modèle de données, commandes/API et migrations](references/05-data-api-migrations.md)
6. [Offline-first, sécurité et contrôle](references/06-offline-securite.md)
7. [Tests, audit du dépôt et plan d'implémentation](references/07-tests-implementation.md)
8. [Exemple imprimable HTML deux configurations](examples/rapport_caisse_agence_exemple.html)

## Ordre d'exécution Claude Code

1. **Auditer le code existant** : référentiels agences/services, caisses, paiements, sessions, dépôt local, synchronisation, rapports, droits, schémas, migrations et tests. Lister **existant / absent / incompatible** ; aucune destruction de données.
2. Introduire si nécessaire le découplage service ↔ caisse ↔ moyen de paiement avec migrations conservatrices, adaptation des anciens mouvements à la caisse historique et aucun double enregistrement.
3. Ajouter configuration caisse par agence, rôle/caissier, session, caisse de défaut facultative, paiement et transfert atomique/idempotent.
4. Adapter billets, colis, garage, paie et dépenses pour qu'ils référencent la caisse de paiement/encaissement **sans recréer la pièce métier**.
5. Étendre les tableaux journaliers simples avec sections par caisse et un total agence ; permettre rapport caisse individuel, rapport agence, supervision siège.
6. Préserver axes analytiques : agence d'encaissement ≠ agence d'exploitation, véhicule, voyage, partenaire et gamme Classique/VIP.
7. Tester mono-caisse, multi-caisses, transferts, dépôt au siège, espèces vs Mobile Money, périodes, droits, offline et rejouabilité. Indiquer les tests réellement réalisés.
8. Restituer fichiers modifiés, migrations, preuves de tests et risques résiduels. **Ne pas prétendre que le projet a été modifié si seule la présente documentation a été générée.**

## Intégration aux référentiels antérieurs

Complète : `/erp-transport-afrique-centrale`, `/erp-transport-plan-analytique`, `/erp-transport-rapport-journalier-agence`. En cas de conflit sur les caisses, la présente spécification prévaut **pour la configuration et les transferts de trésorerie**, sans supprimer les règles de rapports et de comptabilité des autres référentiels.

## Commande

> Applique `/erp-transport-caisses-multi-agences` à mon projet existant. Audite d'abord, puis ajoute la configuration d'une ou plusieurs caisses par agence, l'affectation des caissiers, les mouvements et transferts internes, les rapprochements et les tableaux journaliers simples consolidant les caisses sans double comptage. Conserve tous les modules existants, les règles comptables OHADA, le plan analytique, les véhicules Classique/VIP distincts et la synchronisation hors ligne. Implémente les tests et fournis les modifications réalisées.
