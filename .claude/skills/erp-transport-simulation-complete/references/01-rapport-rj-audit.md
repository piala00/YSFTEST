# Rapport RJ-AG-20261026 (3 pages) — constat et exploitation

**Source incluse** `../examples/rapport_source/rj-1.pdf` ; société nommée « Ma Société » ; date d'activité 26/10/2026, rapport provisoire, synchronisation non configurée. Les véhicules sont libellés « fictifs ». Ne pas mélanger cet exemple avec la société fictive SEPTEMBRE 2026. Date de génération 00:05 alors que départs annoncés 06:00 à 17:00 : incohérence temporelle à corriger, et ne jamais considérer des départs futurs comme effectués.

## Reconstitution exacte de la page 1 — Billetterie

| Véhicule | Départ | Trajet | Places/Passagers du rapport | Prix FCFA | Produit FCFA |
|---|---|---|---:|---:|---:|
| LT 100 XX | DEP2026-00001 / 06:00 | Douala–Yaoundé |25|6000|150000|
| LT 102 XX | DEP2026-00003 / 07:00 | Douala–Bafoussam |20|5000|100000|
| LT 101 XX | DEP2026-00002 / 09:00 | Douala–Yaoundé |18|6000|108000|
| LT 103 XX | DEP2026-00004 / 13:00 | Douala–Yaoundé |30|6000|180000|
| LT 104 XX | DEP2026-00005 / 15:00 | Douala–Bafoussam |12|5000|60000|
| LT 105 XX | DEP2026-00006 / 17:00 | Douala–Yaoundé |22|6000|132000|
| **TOTAL** |||**127**||**730000**|

Note explicite du PDF : le prix est la part du billet revenant au car pour la correspondance/tronçon ; billets pouvant avoir été encaissés une autre date ou agence. **Ce tableau n'est PAS équivalent aux encaissements du jour.**

## Recettes et dépenses
- Bagages payants : 0 **mais saisie non disponible** => absence de données, pas la preuve d'absence de revenu.
- Courrier : 18 bordereaux `COL2026-000001` à `COL2026-000018`, chacun 2 500 FCFA, soit **45 000 FCFA** ; **aucune affectation de véhicule transporteur**.
- Sorties : six débits carburant de 45 000 = **270 000 FCFA**, six entretiens de 2 000 = **12 000 FCFA**, total **282 000 FCFA**, répartis à parts égales entre les six véhicules.
- Tableau 5 : billets encaissés 730 000, colis encaissés 45 000, total encaissé 775 000, dont espèces 620 000, monnaie électronique/banque 155 000 ; décaissements 282 000 ; net tous modes **493 000 FCFA**.
- Transferts déclarés −500 000 FCFA ; caisse espèces ouverture 0 => `0+620000-282000-500000 = -162000 FCFA` ; trésorerie globale comptabilisée fin affichée `-7 000 FCFA` en incluant 155 000 électroniques. **Anomalie bloquante pour clôture physique**. Faire rapprocher la destination et date du transfert de 500 000.
- Référence visuelle PDF p.3 : moyen de paiement électronique affiché sous **551 MM** ; code SYSCOHADA à vérifier : la monnaie électronique par téléphone est généralement **552**, le 551 étant notamment la carte carburant. Le compte 5711 du PDF ne doit pas être appliqué aveuglément à toutes les succursales.

## Reconstitution du résultat analytique PARTIEL (sans colis ni charges communes)
| Véhicule | Billetterie | Carburant | Entretien | Résultat partiel |
|---|---:|---:|---:|---:|
| LT 100 XX |150000|45000|2000|103000|
| LT 101 XX |108000|45000|2000|61000|
| LT 102 XX |100000|45000|2000|53000|
| LT 103 XX |180000|45000|2000|133000|
| LT 104 XX |60000|45000|2000|13000|
| LT 105 XX |132000|45000|2000|85000|
| **TOTAL** | **730000** | **270000** | **12000** | **448000** |

**493 000 n'est PAS le résultat analytique véhicule ; 448 000 est un résultat CONTRIBUTIF PARTIEL lié aux véhicules.** Les **45 000 colis** restent non ventilés par véhicule ; ne pas attribuer fictivement aux six véhicules. Les 155 000 de Mobile Money/banque ne sont pas une autre recette, mais une modalité de paiement.

## Deux exemples d'écritures à produire seulement APRÈS vérification des faits et dates
- Prestation de transport acquise : D compte de règlement/tiers approprié ; C `706* Services vendus` 730000 (fragmentation par pièces/clients/TVA/statuts réels).
- Carburant consommé : D compte de charge de carburant correctement validé ; C caisse/fournisseur pour 270000 selon justificatifs.
- Une opération déjà comptabilisée ne doit jamais être repassée à partir du PDF de synthèse.
- Pour les 45 000 de courrier : D créance ou trésorerie / C prestation de messagerie **au moment correct de reconnaissance du produit** ; l'affectation véhicule doit être recueillie séparément.

## Anomalies à livrer explicitement à la direction
1. Solde espèces négatif : bloquer clôture ou justifier par réconciliation documentée.
2. Somme 730000 voyageurs de départs = 730000 encaissés le jour par coïncidence numérique ; rapprocher billets un à un, y compris vente dans une autre agence.
3. Courriers sans véhicule transporteur.
4. Bagages payants non saisis, table vide non fiable.
5. Provisoire et date/heure de génération incompatibles avec départs futurs.
6. Ligne 155000 « Mobile Money / banque » trop agrégée ; ventiler comptes et caisses réels.
7. Le tableau 5 de trésorerie et le tableau 1 des départs ont des bases temporelles différentes : pas de fusion ni de comptabilisation directe du total RJ.
