# 16 — Rapport journalier d’agence : modèle simple validé

Le rapport journalier d’agence est composé uniquement de tableaux en colonnes, imprimables en noir et blanc, sans graphiques : (A) billets par nom/code de véhicule, service Classique/VIP, trajet, voyage/départ, places, prix et montant ; (B) bagages payants des voyageurs par véhicule, désignation, destination, quantité et montant ; (C) colis/messagerie séparés lorsque présents ; (D) sorties de trésorerie effectivement payées par l’agence, pièces et affectation ; (E) caisse, total encaissé, moyens de paiement, sorties, espèces disponibles, fonds reversés, reste en caisse et écarts. Entête avec société, agence, date, statut, signatures de responsables.

**Contrôle cardinal** : les départs du jour et les encaissements du jour ne représentent pas le même ensemble ; un billet vendu hier ou dans une autre agence peut être utilisé aujourd’hui. Le montant à reverser doit être calculé depuis le journal des vrais encaissements/décaissements et la caisse, jamais par simple soustraction des totaux des voyageurs du jour.

Instruction complète : `../../erp-transport-rapport-journalier-agence/SKILL.md` et ses références. Les chiffres de sa maquette sont fictifs.

## Caisses par agence

Si plusieurs caisses sont configurées, ajouter un tableau de leurs soldes individuels, entrées/sorties espèces externes, transferts et total agence. Une caisse unique doit garder le rapport compact. La synthèse des flux de trésorerie ne doit pas comptabiliser deux fois les transferts caisse-caisse ni les remises au siège. Appliquer le skill complémentaire `/erp-transport-caisses-multi-agences`.

