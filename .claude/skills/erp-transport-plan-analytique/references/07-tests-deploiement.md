# 07 — Matrice de tests d'acceptation et déploiement

## Scénarios d'acceptation minimum (automatisables)

1. **Vente Classique** : voyage Classique / véhicule Classique → billet admissible, sections GAM-CLASSIQUE / ACT-PAX / VEH / VOY ; une seule recette reconnue.
2. **Vente VIP** : voyage VIP / véhicule VIP → tarif et imputation GAM-VIP corrects, produit unique.
3. **Incompatibilité** : assigner BUS-CLASSIQUE à un voyage VIP → rejet transactionnel côté backend, même en appel API direct.
4. **Changement de gamme daté** : passages successifs compatibles/non-chevauchants ; les périodes antérieures conservent leur affectation ; collision refusée.
5. **Deux agences** : vente à Douala et exploitation à Yaoundé → encaissement Douala, performance commerciale Douala, résultat d'exploitation Yaoundé, aucune vente comptabilisée deux fois.
6. **Colis sur véhicule VIP** : revenu dans ACT-COL et marge du bus VIP, pas dans CA billets VIP ; total compagnie inchangé.
7. **Colis multi-véhicules** : 20 000 FCFA d'expédition sur deux tronçons → allocations dont somme = 20 000 FCFA, avec justificatifs de legs.
8. **Achat vs consommation pièce** : stock acheté puis pièce sortie au garage ; coût véhicule enregistré à la consommation appropriée, pas deux fois.
9. **Charge commune** : 200 000 répartis 60 % Classique / 40 % VIP → 120 000 + 80 000 ; source générale 200 000, analytique total par vue 200 000.
10. **Paie** : salaire approuvé affecté à 2 missions ; coût total une seule fois, paiement ultérieur apure dette sans autre charge ; confidentialité du salaire des personnes.
11. **Partenaire multi-véhicules** : véhicules VIP et Classique même propriétaire → détail et total du propriétaire, sans mélange des droits contractuels et marge.
12. **Propriétaire change en milieu de période** : coûts/voyages antérieurs rattachés à l'ancien contrat, postérieurs au nouveau.
13. **Remboursement** : avoir d'un billet VIP renverse la vente d'origine, véhicule/partenaire historiques conservés.
14. **Offline replay** : même `source_event_id` transmis 3 fois après reconnexion → exactement une imputation dans chaque vue.
15. **Conflit offline** : deux sites transmettent classification véhicule incompatible / tarifs contradictoires → rejet et dossier de résolution, pas « dernière écriture gagne ».
16. **Rapprochement GL** : cas avec montants ventilables, non-affectés et frais non liés au transport → montant source = montant alloué + reliquat de la même vue ; anomalie visible.
17. **Clôture agence non synchronisée** : le siège présente des tableaux provisoires avec agence/date manquante et interdit fausse clôture globale définitive.
18. **Sécurité** : un agent de billet ne peut modifier axes/règles, un partenaire ne peut voir véhicule/contrat d'autrui, même via l'API.
19. **Centimes/arrondis** : répartir valeur non divisible en pourcentages → total exact en centimes ou unité de monnaie retenue ; aucun flottant.
20. **Relecture des rapports** : le drill-down d'un total véhicule doit ouvrir les pièces, y compris les corrections et périodes validées.

## Données de recette synthétiques

- Agences : A-YDE, A-DLA, A-BTA ; avec `agency_selling_id` et `agency_operating_id` distincts.
- Véhicules : C01 et C02 affectés Classique ; V01 et V02 affectés VIP.
- Partenaires : P1 détient C01 et V01 ; C02/V02 appartiennent à la compagnie.
- Voyages : J-C01 sur ligne YDE–BTA, J-V01 sur même ligne, tarifs illustratifs distincts.
- Services : billet, messagerie, garage, carburant, RH, comptabilité.
- Référence : un événement source par vente, paquet de charges et lot de ventilation ; identifier clairement quelle vue et quelle règle ont produit chaque chiffre.

## Tests techniques à ajouter selon dépôt

- Unitaires : validation de gamme, dates d'effet, import des sections, clés d'arrondi, non affectés, droits partenaires.
- Intégration DB : contraintes exclusivité, FK/tenant, transactions et versionnement, reconstructions idempotentes.
- API : authentification/autorisation, filtres, erreurs de conflits, simulation vs validation.
- E2E : agent billetterie → véhicule/voyage → écriture → analytique → rapport agence/siège ; garage et colis analogues.
- Résilience : sync deux fois, pertes réseau, interruptions entre événement et accusé, retard d'horloge, reprise sauvegarde.
- Performance : indicateurs sur volume production simulée, indexation, éventuelles vues matérialisées réconciliées.

## Ordre pratique de livraison

- **Étape A : AUDIT** code, migrations, UI, reporting, droits, synchro, contrats (aucune modification destructive).
- **Étape B : RÉFÉRENTIEL** plans/sections/relations historiques ; fiches véhicules VIP/Classique, contrôle voyages.
- **Étape C : IMPUTATION** version des règles, produits Classique/VIP, coûts garage/carburant, activité colis.
- **Étape D : PARTENAIRES/RH** contrats datés, feuilles de paie affectées, charges communes, décomptes.
- **Étape E : REPORTS** résultats voyage/véhicule/agence/partenaire/gamme, rapprochements, anomalies.
- **Étape F : RÉSILIENCE** offline-first, sync idempotente, backfill, cohérence sièges, reprise.

Pour chaque étape, Claude Code doit publier : fichiers réellement modifiés, migrations produites, jeux de tests exécutés et résultats, écarts restant à résoudre et instructions de retour arrière. Ne jamais prétendre avoir exécuté un test non exécuté.

## Conformité et exploitation

Le plan analytique est un dispositif interne de gestion et doit être raccordé à la comptabilité générale SYSCOHADA appropriée. Les règles pays/contrats/paie/taxes/recettes différées doivent être validées par l'expert habilité. L'architecture offline fonctionne seulement si le serveur local et l'équipement demeurent alimentés ; sécuriser sauvegardes chiffrées, restauration de test, journaux et contrôles d'accès.
