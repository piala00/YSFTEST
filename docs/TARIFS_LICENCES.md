# Tarifs des licences — valeurs de départ (validées 2026-11-04, modifiables)

Décisions du propriétaire :
- **Modèle** : les deux au choix — **abonnement** (mensuel/trimestriel/annuel) **ou**
  **licence définitive + maintenance annuelle**.
- **Base de calcul** : **par agence/société** + **par poste** + **par module activé**
  (+ forfait de base selon l'édition).
- **Prix affiché au client dans la version d'essai** (pas encore de site web) : écran
  « Tarifs / Acheter une licence », tarifs intégrés au build (visibles hors ligne).
- **Alignement marché** : valeurs de départ ci-dessous, **modifiables** par le propriétaire
  dans l'outil éditeur ; ce sont les **défauts** de la grille. Devise : **FCFA (XAF)**.
- **TVA / taxes** : non incluses et **non inventées** ; le propriétaire les fixe selon la
  réglementation (règle AGENTS.md).

## Grille par défaut (FCFA)

### Abonnement (récurrent)
| Élément | Mensuel | Annuel (≈ 2 mois offerts) |
|---|---|---|
| Base par agence/société | 35 000 | 350 000 |
| Par poste supplémentaire | 12 000 | 120 000 |
| Par module optionnel | 6 000 | 60 000 |

### Licence définitive (paiement unique) + maintenance
| Élément | Montant |
|---|---|
| Base par agence/société | 700 000 |
| Par poste | 150 000 |
| Par module | 120 000 |
| Maintenance annuelle | 18 % du total de la licence / an |

## Repères marché ayant servi à l'alignement (déclaratif, à titre indicatif)
- ERP par poste/mois : Odoo ≈ 25 $ (~15 000 FCFA), Dynamics 365 BC ≈ 80 $ (~48 000 FCFA),
  NetSuite ≈ 99 $/poste + socle.
- Logiciels bus/transport : ~50–300 $/véhicule/mois ; forfaits ~69–100 $/mois ; souvent sur devis.
- Afrique/FCFA : SaaS commerce (FiaVia) dès 8 900 FCFA/mois ; billettique urbaine Dakar
  ~200 000 FCFA/mois + par valideur ; TMS France 6 000–40 000 € à l'achat.
- Norme maintenance logicielle : ~15–20 % du prix de licence par an.

## Intégration prévue (feuille de route P1)
1. **Outil éditeur** (`deploy/licences/licences.py`) : grille tarifaire éditable (ces défauts),
   calcul automatique du montant à l'émission (agence + postes + modules, abonnement vs
   définitive+maintenance), **devis/facture**, montant enregistré au registre.
2. **Version d'essai (client)** : écran « Tarifs / Acheter une licence » affichant la grille +
   la marche à suivre (copier le code du poste → l'envoyer à l'éditeur → recevoir la licence).
   Tarifs intégrés au build (hors ligne), mis à jour à chaque version.
