---
name: erp-transport-simulation-complete
description: Auditer et améliorer un ERP de transport interurbain camerounais via un rapport journalier concret, une simulation reproductible de 8 agences, 300 employés, 60 bus (15 partenaires), 5 véhicules courrier, achats, stocks, paie, comptabilité générale source unique, analytique et reporting sur 30 jours. À utiliser pour la mise à jour du projet existant et préparer un retour complet et expurgé pour analyse collaborative avec ChatGPT.
---

# ERP TRANSPORT AFRIQUE CENTRALE — Skill d'audit et de simulation intégrale

## Objectif et ordre de priorité
1. **AUDITER LE VRAI CODE DU PROJET AVANT TOUTE MODIFICATION**. Repérer modules, tables, interfaces, fichiers, synchronisation offline, dettes, caisses, auth et journaux. Les exemples n'autorisent jamais à inventer que des fonctions existent déjà.
2. Charger [01_rj.pdf et audit](references/01-rapport-rj-audit.md), produire sa restitution en **comptabilité générale**, **comptabilité analytique** (Véhicules et Propriétaires), **reporting** et afficher les incohérences.
3. Faire tourner la simulation complète [02 société](references/02-societe-simulation.md) avec `python .claude/skills/erp-transport-simulation-complete/scripts/generate_demo.py`; tous les CSV fictifs sont inclus dans `examples/demo_2026_09/`. Relancer le générateur uniquement dans un environnement de démonstration isolé.
4. Implémenter / améliorer de façon additive les flux [03 achats](references/03-achats-stocks-approvisionnement.md), [04 comptabilité](references/04-comptabilite-generale-source.md), [05 analytique](references/05-analytique-vehicules-partenaires.md), [06 reporting](references/06-reporting-periodes-agences.md), [07 paie](references/07-rh-paie-mensuelle.md) et [08 offline](references/08-caisses-offline-permissions.md).
5. Tester selon [09 critères](references/09-tests-recette-acceptation.md) et le validateur `scripts/validate_demo.py`. Réconcilier GA/analytique/stocks/caisse/paie/partenaires.
6. Fournir au maître d'ouvrage un **retour complet** suivant [10 collaboration](references/10-collaboration-retour-projet.md) : rapport d'audit, modifications du projet, tests, vues/captures utiles, structure SQL et **ZIP complet du projet avec secrets exclus**. Ne jamais envoyer une base réelle sans autorisation expresse.

## Contraintes contractuelles non négociables
- La comptabilité générale est **l'unique source des écritures monétaires**. Une ventilation analytique porte `source_gl_line_id`, se rattache à une ligne GL comptabilisée, et **ne crée jamais de nouvelle charge ni de nouveau produit**.
- Les données opérationnelles non financières (trajets, sièges, kilomètres) peuvent enrichir les analyses sans écriture GA.
- **Deux rubriques analytiques visibles uniquement** : `Véhicules` et `Propriétaires de véhicules`. Agences, lignes, gammes, voyages, services et contrats restent dimensions / filtres du moteur et du reporting.
- **60 véhicules voyageurs** aux gammes exclusives CLASSIQUE/VIP, dont **15 appartenant à des partenaires**, et **5 véhicules de fret courrier** ; affectations et propriétaires historisés. Les coasters et minibus peuvent être VIP ; le type de carrosserie ne détermine pas automatiquement la gamme.
- **8 agences, 300 salariés, un mois calendaire complet** ; agents spécialisés et petites agences pouvant mutualiser la caisse. Tous les nombres/prix/salaires/contrats sont FICTIFS.
- Achats **centralisés ou locaux configurables** : demande → consultation/devis → comparaison → bon de commande → réception/contrôle → facture rapprochée → dette fournisseur → paiement → stock → consommation ou immobilisation. Achat ≠ consommation ; livraison inter-agence ≠ nouvelle charge.
- Recette voyage/jour/agence ≠ encaissement/jour/agence. Billets encaissés ailleurs ou antérieurement : pas de double comptabilisation.
- Modes caisse espèces/Mobile Money/banque distincts ; transferts internes ≠ ventes/charges ; interdiction de solde de caisse physique négatif sans anomalie explicite.
- Gestion hors connexion : transaction locale validée, outbox, identifiants globaux et idempotence, quotas de sièges et statut de synchronisation ; ne jamais promettre zéro conflit sans coordination.
- Ne pas remplacer ni effacer silencieusement les données du logiciel réel. Faire sauvegardes, migrations additives, contrôles RBAC et tests avant déploiement.
- Tout état présenté comme définitif provient de journaux clos/validés ; les chiffres provisoires restent marqués.
- Barèmes CNPS/IRPP/TVA et imputations SYSCOHADA : ne jamais affirmer les taux/découpages de simulation comme officiels. Validation d'un comptable camerounais avant production.

## Mission immédiate de Claude Code
1. Commencer par `git status`, l'inventaire des fichiers, le schéma et une sauvegarde sans secrets ; ne pas écraser le projet.
2. Comparer le projet à chaque exigence de ce Skill dans `AUDIT_ECARTS.md`, avec `EXISTANT / PARTIEL / ABSENT / BLOQUANT`.
3. Implémenter progressivement dans une branche de travail ; conserver tous les changements et lister les tests réellement exécutés.
4. Faire des démonstrations séparées « Journalier RJ-1 » et « Septembre 2026 : 8 agences, 300 salariés ».
5. Remettre `RETOUR_POUR_CHATGPT.md`, un plan de fichiers, un schéma SQL, un journal des tests et le ZIP anonymisé `RETOUR_CLAUDE_CODE_ERP_TRANSPORT.zip`.

## Index des références
- [01 Rapport réel de démonstration & anomalies](references/01-rapport-rj-audit.md)
- [02 Entreprise fictive, flotte, huit agences, mois complet](references/02-societe-simulation.md)
- [03 Achats, pièces, fournitures, carton et ruban adhésif, stocks](references/03-achats-stocks-approvisionnement.md)
- [04 Journal général et écritures](references/04-comptabilite-generale-source.md)
- [05 Comptes analytiques véhicules et partenaires](references/05-analytique-vehicules-partenaires.md)
- [06 Reporting comparatif et clôture](references/06-reporting-periodes-agences.md)
- [07 Trois cents salariés et fin de mois](references/07-rh-paie-mensuelle.md)
- [08 Caisse unique/multiple, offline et habilitations](references/08-caisses-offline-permissions.md)
- [09 Recette fonctionnelle / tests / rapprochements](references/09-tests-recette-acceptation.md)
- [10 Protocole Claude Code ↔ ChatGPT, retour complet](references/10-collaboration-retour-projet.md)
- [11 Modèle de données / APIs](references/11-schema-api-mapping.md)
- [12 Sources officielles et limites](references/12-sources-limites.md)

Les anciens Skills du projet inclus dans le ZIP restent disponibles. **Celui-ci prend la priorité sur leurs anciennes hypothèses contradictoires pour le périmètre de cette simulation.**


## Mise à jour : propriétaires de véhicules ≠ fournisseurs (nouveau Skill cumulatif)
**Lire impérativement** [erp-transport-partenaires-proprietaires](../erp-transport-partenaires-proprietaires/SKILL.md) avant de modifier le moteur partenaire : rémunération fixe (« salaire du propriétaire » métier), droit variable, avance ou cumul contractuel, retraits contrôlés, compte auxiliaire GA propriétaire séparé des fournisseurs, et preuve de chaque montant. Le mini-scénario autonome ne remplace ni ne corrige silencieusement les écritures du scénario septembre 2026 : intégrer le cas par nouvelles écritures équilibrées lors de la régénération de la simulation globale.
