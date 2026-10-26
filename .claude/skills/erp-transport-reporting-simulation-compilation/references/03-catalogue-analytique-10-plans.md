# 03 — Dix plans analytiques visibles et états détaillés

**Les dix plans apparaissent dans le module Comptabilité analytique**, avec rubrique, sections, choix d'état, date libre, filtres et exports. Véhicules et Propriétaires sont les favoris ; aucune autre rubrique ne doit être masquée.

| Code | Plan | Section exemple | Analyses spécialisées |
|---|---|---|---|
| 01 | Agences / Gares | Douala, Bertoua | Compte d'exploitation, résultat billetterie/courrier/garage, coûts structurels, caisses en lecture séparée |
| 02 | Véhicules | BUS-001 | Produits, charges, marge, entretien, carburant, km, voyages, total GL, coût/km |
| 03 | Propriétaires véhicules | PROP-001 | Résultat de chaque véhicule au contrat historique, fixe, variable, avances, retenues, retraits, dette réellement due |
| 04 | Services / Départements | Billetterie, Courrier, Garage, RH | Coût de service, produits éventuels, répartition des frais communs |
| 05 | Activités | Voyageurs, Colis, Affrètement | Rentabilité et progression par activité |
| 06 | Gammes de transport | Classique, VIP | Flottes dédiées, produits, coûts, charges moyennes, taux de remplissage opérationnel |
| 07 | Lignes / Itinéraires | Douala–Yaoundé | Marge par ligne, voyages, sièges et tronçons |
| 08 | Voyages / Départs | DEP2026-0001 | Compte d'exploitation voyage, billets, bagages, colis, frais route |
| 09 | Contrats d'exploitation | CTR-001 | Conditions tarifaires à dates d'effet, échéances, calculs de droits et charges autorisées |
| 10 | Canaux de vente | Guichet, Web, Revendeur | CA par canal, frais de distribution, encaissement/vente séparés |

## Bibliothèque commune d'états pour chaque plan
1. Synthèse et tableau de bord ; 2. Compte d'exploitation analytique ; 3. Balance analytique par section et compte ; 4. Grand livre analytique chronologique ; 5. Journal analytique des ventilations ; 6. Produits détaillés ; 7. Charges détaillées ; 8. Direct/indirect et clés de répartition ; 9. Comparatif de deux périodes ; 10. Évolution mensuelle / annuelle ; 11. Classement des sections ; 12. Non-affectés, écarts, anomalies ; 13. État des pièces justificatives et drill-down.

Chaque état porte le nom du plan, section, société, devise, début/fin, mode de comptabilisation, dernière synchro, total, statut et date d'édition.

## Propriétaires ≠ autres tiers
Un propriétaire de véhicule peut être aussi fournisseur mais ses comptes auxiliaires doivent rester distincts. **Résultat comptable d'un véhicule ≠ somme retirable par propriétaire**. Rémunération fixe (appelée parfois « salaire du propriétaire ») ne constitue pas automatiquement une paie de salarié. Retrait uniquement contre solde disponible/autorisation et écriture générale préalable. La méthode de part fixe/variable/avance dépend du contrat daté.

## Algorithme d'affectation
`GL_line` → `AnalyticalAllocation` avec `GL_line_id`, `plan_id`, `section_id`, montant, pourcentage, méthode, période d'effet, source opérationnelle et audit. Les axes restent indépendants ; la somme totale GL ne s'obtient **pas** en sommant les dix plans. Stocker ou dériver `non_affecté` par axe.
