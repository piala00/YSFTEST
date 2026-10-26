# Bilan de la simulation « septembre 2026 » (8 agences, 300 salariés)

## Ce qui a été fait
- Les fichiers CSV fictifs du skill (`examples/demo_2026_09`) ont été **validés** par leur script : 8 agences, 300 salariés,
  60 bus voyageurs dont 15 de partenaires, 5 courriers, 1 275 voyages, 35 883 billets, 2 523 colis, 32 bons de commande,
  300 bulletins, débit = crédit = 803 114 750 FCFA. Sortie complète dans `TESTS_EXECUTES.md`.
- Les règles que la simulation sert à vérifier sont couvertes par des **tests automatisés du logiciel** (voir
  `AUDIT_ECARTS.md`) : source unique, rapprochement affecté / non affecté, flottes Classique / VIP, contrats datés,
  propriétaires (exemples A et B), caisses, échanges hors ligne, rejeu idempotent.

## Ce qui n'a pas été fait
- L'**import** de ces CSV dans une base de l'ERP. Il demande un programme d'import dédié (agences, gares, lignes,
  véhicules, contrats, voyages, billets avec sièges, colis, achats, paie, écritures), qui doit **recréer les faits**
  par les fonctions du logiciel (vente, départ, paie…) plutôt que copier les écritures du CSV : sinon on comptabiliserait
  deux fois. Proposition : une commande `simulation_septembre` qui rejoue le mois dans une base de démonstration séparée,
  puis compare les totaux (billets, colis, paie, partenaires) avec ceux du CSV.
- Les écarts du module achats / stocks (inventaire permanent, magasin du garage) empêchent de rejouer à l'identique la
  partie « stock = actif, consommation = charge » : voir `AUDIT_ECARTS.md` § 2.

Aucun résultat chiffré de la simulation n'est présenté comme produit par l'ERP.
