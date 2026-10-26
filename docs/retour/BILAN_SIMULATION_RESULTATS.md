# Bilan de la simulation (données FICTIVES)

Mois simulé : 01/09/2026 au 30/09/2026 · échelle 1.0 · graine 2026

Produit par `python manage.py simulation --mois 2026-09` dans un dossier SQLite séparé (Linux, 55 minutes). Chaque
écriture vient d'une opération du logiciel (vente, départ, plein, achat, sortie, paie, décompte), aucune n'est copiée.

| Activité | Nombre |
|---|---:|
| voyages | 1392 |
| billets | 47653 |
| bagages | 7173 |
| colis | 2564 |
| pleins | 1392 |
| reparations | 15 |
| bulletins | 300 |
| ecritures | 53178 |

| Comptabilité générale | FCFA |
|---|---:|
| produits | 340 108 500 |
| charges | 192 074 288 |
| billets_70611 | 319 430 500 |
| bagages_70614 | 14 268 000 |
| colis_70612 | 6 410 000 |
| carburant | 125 302 800 |
| pieces_624 | 730 000 |
| paie_661 | 34 925 000 |
| paie_664 | 3 492 500 |
| net_bulletins | 33 178 750 |
| net_a_payer_422 | 0 |
| organismes_431 | 5 238 750 |
| fournisseurs_401 | 0 |
| proprietaires_467 | 10 036 075 |
| caisse_57 | 1 255 827 |
| banque_52 | 139 796 010 |
| mobile_money_55 | 65 631 000 |
| transit_585 | 0 |
| stock_33 | 6 376 200 |
| valeur_magasin | 6 376 200 |
| immobilisations_2 | 250 000 |
| Résultat (produits − charges) | 148 034 212 |
| Total débit = total crédit | 1 285 931 897 = 1 285 931 897 |

| Analytique véhicules | FCFA |
|---|---:|
| produits_gl | 340 108 500 |
| charges_gl | 192 074 288 |
| produits_affectes | 340 108 500 |
| charges_affectees | 168 912 988 |
| nb_non_affectees | 40 |
| produits_non_affectes | 0 |
| charges_non_affectees | 23 161 300 |
| Résultat des véhicules pour la société | 171 195 512 |

| Propriétaire | Véhicule | Contrat | Solde du propriétaire, tous ses véhicules (467) |
|---|---|---|---:|
| Propriétaire 1 (fictif) | SIM 046 CL | Compte du camion : recettes − charges (− commission éventuelle de la société) | 1 754 800 |
| Propriétaire 2 (fictif) | SIM 047 CL | Salaire mensuel fixe du propriétaire (forfait) | 705 798 |
| Propriétaire 3 (fictif) | SIM 048 CL | Fixe garanti + complément variable | 1 781 056 |
| Propriétaire 4 (fictif) | SIM 049 CL | Fixe versé en avance sur le variable | 800 010 |
| Propriétaire 5 (fictif) | SIM 050 CL | Compte du camion : recettes − charges (− commission éventuelle de la société) | 1 597 640 |
| Propriétaire 6 (fictif) | SIM 051 CL | Salaire mensuel fixe du propriétaire (forfait) | 160 000 |
| Propriétaire 7 (fictif) | SIM 052 CL | Fixe garanti + complément variable | 1 212 054 |
| Propriétaire 8 (fictif) | SIM 053 CL | Fixe versé en avance sur le variable | 486 941 |
| Propriétaire 9 (fictif) | SIM 054 CL | Compte du camion : recettes − charges (− commission éventuelle de la société) | 1 377 776 |
| Propriétaire 10 (fictif) | SIM 055 CL | Salaire mensuel fixe du propriétaire (forfait) | 160 000 |
| Propriétaire 1 (fictif) | SIM 056 CL | Fixe garanti + complément variable | 1 754 800 |
| Propriétaire 2 (fictif) | SIM 057 CL | Fixe versé en avance sur le variable | 705 798 |
| Propriétaire 3 (fictif) | SIM 058 CL | Compte du camion : recettes − charges (− commission éventuelle de la société) | 1 781 056 |
| Propriétaire 4 (fictif) | SIM 059 CL | Salaire mensuel fixe du propriétaire (forfait) | 800 010 |
| Propriétaire 5 (fictif) | SIM 060 CL | Fixe garanti + complément variable | 1 597 640 |

| Contrôle | Résultat |
|---|---|
| Débit = crédit de toutes les écritures | OK |
| Caisse espèces positive en fin de mois | OK |
| Fonds en transit soldés (versements reçus) | OK |
| Salaires nets payés (422 soldé) | OK |
| Stock comptable (33) = valeur du magasin | OK |
| Produits analytiques affectés + non affectés = comptabilité | OK |

Taux de paie de démonstration (5 % / 10 %), prix, salaires et contrats : fictifs, sans valeur réglementaire.
Non simulés (le résultat est donc optimiste) : assurances, amortissements, péages, impôts et taxes, imprévus de voyage, annulations et remboursements.
