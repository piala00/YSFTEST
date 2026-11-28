# Modèles de définition des KPI / Sage BI

| KPI | Granularité | Faits source à tester | Piège |
|---|---|---|---|
| CA HT net | Document facturé validé / ligne | Factures - avoirs, période | Double comptage commande/BL/facture |
| Marge brute | Ligne facture ou article | Vente HT nette - coût valorisé | Coût de vente non fixé dans historique |
| Recouvrement | Paiement affecté | Règlements affectés par date | Encaissement non affecté et double compte |
| Créances échues | Échéance-client | Solde restant, date échéance | Date facture ≠ date d'échéance |
| Stock valorisé | Article-dépôt-date | Snapshot/mouvements + coût | Comparaison de valeurs à dates différentes |
| Rotation des stocks | Article-période | Sorties éligibles, stock moyen | Usage de stock fin comme moyenne |
| Balance comptable | Compte-exercice-période | À-nouveaux + écritures | Solde incorrect sans reports |

Pour chaque KPI : définir le périmètre d'entreprise, le mode de calcul, la fiscalité, le filtrage des annulations, le traitement des retours, le cas multi-devises, l'état standard de référence et le test d'égalité.
