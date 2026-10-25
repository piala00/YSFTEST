# 03 — Comptabilité, moyens de paiement et rapprochements

## Principe financier

- **Comptabilité générale** : enregistrement en partie double conformément au paramétrage OHADA validé ; flux de trésorerie distincts des produits/charges, journal selon schéma de comptabilisation.
- **Comptabilité analytique** : agence, service, voyage, véhicule, ligne, gamme Classique/VIP, partenaire ; une charge ne doit pas être imputée deux fois parce qu'elle apparaît dans deux rapports.
- **Caisse (espèces)** : encaissements / décaissements physiquement effectués, transferts, comptages, remises et solde de fin. Si plusieurs caisses, `cashbox_id` obligatoire pour opérations espèces et sessions.
- **Paiement électronique** : journal par portefeuille ou compte bancaire ; rattache aussi le service et l'agence du règlement. Ne pas lui attribuer un faux solde espèces.

## Formule de chaque caisse physique c et journée D

```
SOLDE_OUVERTURE(c,D) = solde de clôture accepté du dernier jour/session (hors fonds en transit non reçus)
RECETTES_ESPECES(c,D) = somme des encaissements espèces validés datés de D
SORTIES_ESPECES(c,D) = somme des décaissements espèces réels de D, y compris remboursements selon convention explicite
TRANSFERTS_ENTRANTS(c,D) = remises d'autres caisses effectivement reçues
TRANSFERTS_SORTANTS(c,D) = remises effectivement sorties de caisse (en transit ou reçues)
DEPOTS_ET_REMISES(c,D) = dépôts en banque ou siège physiquement remis
SOLDE_THEORIQUE(c,D) = OUVERTURE + RECETTES - SORTIES + TRANSFERTS_ENTRANTS - TRANSFERTS_SORTANTS - DEPOTS_ET_REMISES
ECART(c,D) = SOLDE_COMPTE_PHYSIQUE(c,D) - SOLDE_THEORIQUE(c,D)
```

Éviter les doubles soustractions : si un versement vers le siège est déjà classé `TRANSFERTS_SORTANTS`, **ne pas le compter une seconde fois** dans `DEPOTS_ET_REMISES`. Chaque mouvement financier comporte `movement_type` unique et un sens du point de vue de la caisse.

### Total agence

- `TOTAL_RECETTES_EXTERNES_ESPECES` = somme des encaissements espèces de la journée **hors transferts internes**.
- `TOTAL_SORTIES_EXTERNES_ESPECES` = somme des paiements espèces à des tiers, remboursements réels selon convention **hors transferts internes**.
- `SOLDE_ESPECES_CAISSES_FIN` = somme des soldes fin de toutes les caisses ; ajouter les **fonds en transit** si le rapport est de trésorerie totale (ligne distincte), mais pas pour les espèces physiquement sur place.
- `TOTAL_RECETTES_MULTI-MOYENS` = somme des paiements externes reçus dans l'agence, quelle que soit la caisse responsable, avec classification des moyens ; ne pas ajouter les recettes d'exploitation correspondant à des billets payés précédemment.
- `NET_FLUX_EXTERNE_JOUR` = recettes externes réellement encaissées − sorties externes réellement payées, tous moyens, sans inclure transferts internes.
- `MONTANT_A_REVERSER` : dépend des espèces réellement présentes, du fonds de caisse à conserver, des avances autorisées et des remises déjà effectuées. Ce n'est **ni** le total des ventes ni une marge ni le bénéfice analytique.

### Exemple fictif d'agence multi-caisses, XAF

| Caisse | Ouverture | Entrées espèces externes | Sorties externes | Solde fin théorique |
|---|---:|---:|---:|---:|
| Billetterie | 0 | 500 000 | 20 000 | 480 000 |
| Courrier | 0 | 250 000 | 10 000 | 240 000 |
| Garage | 100 000 | 0 | 80 000 | 20 000 |
| Centrale | 0 | 300 000 | 100 000 | 200 000 |
| **TOTAL** | **100 000** | **1 050 000** | **210 000** | **940 000** |

**Hypothèses** : zéro transfert, zéro remise, zéro remboursement distinct, espèces seulement. Chiffres illustratifs. Le total des fonds physiques n'est pas la « recette nette du jour » : net externe du jour = 840 000 XAF, et 100 000 XAF existaient déjà à l'ouverture.

### Exemple avec transfert interne

- Billetterie verse 300 000 à Centrale. L'agent source passe de 480 000 à 180 000 ; la centrale passe de 200 000 à 500 000 après réception ; total final toujours **940 000**. La direction voit 300 000 de transferts, **zéro recette nouvelle**.
- Si la réception est en attente : total des caisses physiques = 640 000 et espèces en transit = 300 000 ; trésorerie globale = 940 000, sous réserve de confirmation et rapprochement.

### Modes de paiement et établissement des états

Montants encaissés selon date d'encaissement réelle en Afrique/Douala pour les agences camerounaises, sans supposer que les départs du même jour égalent les encaissements. Les paiements en ligne peuvent être perçus centralement ; éviter de les attribuer à l'espèce d'agence où a lieu le départ. Impressions signées font état des sommes comptées et des écarts, ainsi que des paiements non-espèces à rapprocher.

## Contrôles

- Aucune caisse négative sans règle exceptionnelle explicite et autorisation, surtout en offline.
- Contrôle par solde/devise ; si ajustement, pièce documentée, validation indépendante des écritures originales.
- Comptes OHADA précis et traitement de la TVA à configurer après validation professionnelle selon contrats/réglementation, **pas de numéros/taux inventés**.
- Le contrôle comptable doit rapprocher sous-journaux caisses, banque et portefeuille électronique des journaux généraux sans additionner les agrégats opérationnels.
