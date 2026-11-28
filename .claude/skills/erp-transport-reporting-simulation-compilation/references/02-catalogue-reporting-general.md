# 02 — Catalogue des états de comptabilité générale destinés au Reporting

La comptabilité générale est source de vérité ; le Reporting lit des états GL et les présente avec mêmes règles de période, statut et permissions :

| Groupe | États à produire | Contrôle / drill-down |
|---|---|---|
| Journaux | Journal centralisateur, ventes, achats, banque, caisses, OD, paie | Date, pièce, journal, auteur, débit, crédit |
| Balance | Balance générale, balance à 6 colonnes, balance de vérification, comparative N/N-1 | Soldes et mouvements rapprochés par compte |
| Grand livre | Grand livre général, par compte, par tiers, éditions mensuelles | Ligne GL et justificatif |
| Tiers | Balances auxiliaires fournisseurs, propriétaires, autres débiteurs/créditeurs ; échéanciers | Type de tiers et compte séparés |
| Trésorerie | Caisses par agence/caissier, caisse centrale, banque, Mobile Money, rapprochement, transferts en transit | Ne jamais assimiler mouvement interne à recette |
| Résultat | Produits / charges, compte de résultat de gestion, marges par activité si imputées | Comparaison GL et analytique |
| États financiers | Bilan SYSCOHADA, compte de résultat SYSCOHADA, tableau des flux et notes selon périmètre | Clôture, exercice, justification et contrôles |
| Taxes/paie | TVA et obligations applicables, masse salariale, salaires/charges sociales à payer | Schémas juridiques et fiscaux configurés |
| Fournisseurs/achats | Engagements, commandes, réceptions, factures comptabilisées, stock, dettes, paiements | Engagement non comptable clairement séparé |
| Contrôle | Pièces non équilibrées, journaux non clôturés, comptes inactifs, non-lettrés, comptes non conformes 7 chiffres | Liste d'anomalies exportable |

**Interdit :** présenter des données provisoires de vente comme bilan officiel. Les états SYSCOHADA doivent être construits sur des comptes paramétrés et des clôtures validées par un comptable ; ne pas promettre bilan certifié à partir d'un simple rapport journalier.

**Interface** : Filtres Société, agence ou toutes agences, exercice, date, journal, compte, tiers, mode de paiement, statut. Impression simple pour rapport journalier ; analyses plus avancées dans le module Reporting.
