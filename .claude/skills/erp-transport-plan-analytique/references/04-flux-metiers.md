# 04 — Chaîne interservices : événements, imputations et contrôle

## Matrice de flux fonctionnels

| Service initiateur | Action | Fait source | Imputation analytique | Limite/condition |
|---|---|---|---|---|
| Billetterie | Vendre billet Classique | ticket + voyage + paiement | ACT-PAX, GAM-CLASSIQUE, VOY, VEH, LIG, AGC exploitation, CAN | reconnaissance ≠ encaissement ; caisse agence de vente |
| Billetterie | Vendre billet VIP | ticket + voyage VIP | ACT-PAX, GAM-VIP, VOY, VEH dédié, LIG, AGC, CAN | rejeter si véhicule Classique |
| Billetterie | Annuler/avoir | événement annulation + avoir autorisé | inversion/correction du même fait attribué initialement | ne pas réattribuer selon classification courante |
| Billetterie | Report de départ | changement voyage accepté | requalification avant exécution, avec historique | paiements restent associés à leur source ; traiter écart tarifaire |
| Messagerie | Enregistrer expédition | shipment + facture/règlement | ACT-COL, agence de vente/origine | pas de produit véhicule avant transport selon politique |
| Messagerie | Charger/retransporter | shipment_leg, manifeste, véhicule | VOY, VEH, LIG, AGC exploitation ; GAM pour vue transversale selon voiture | attribution de revenu par legs, total inchangé |
| Messagerie | Remettre colis | livraison et preuve | progression des états du service | pas de deuxième vente |
| Garage | Réparation | ordre de réparation, pièce sortie, main-d'œuvre | VEH, DEP-GAR, GAM de la date / contrat | achat d'une pièce en stock ≠ consommation du véhicule |
| Carburant | Ravitailler | fuel_issue, véhicule, litres, km, bon | VEH, VOY si affectable, GAM, LIG, AGC | dépense/consommation ≠ simple commande ou avance |
| Exploitation | Clôturer voyage | trip_close + km + incidents | consolide produits/coûts VOY, VEH | pas de nouveau produit comptable |
| RH / Paie | Approuver paie | rubrique validée, agent, affectation | DEP, AGC et VOY/VEH si direct ; sinon ventilation | paiement salarial distinct ; données privées cloisonnées |
| Partenaires | Calculer décompte | contrat daté + sources imputées | CTR, PRT, VEH ; droits contractuels | résultat analytique ≠ dette partenaire |
| Trésorerie | Encaisser ou payer | payment/cash_movement | caisse/agence, source économique reliée | pas de nouvelle recette de transport à l'encaissement |
| Comptabilité | Valider écriture | journal_line | affectation et rapprochement de la ligne | équilibre débit/crédit et paramétrage SYSCOHADA |

## Exemple de bout en bout — Billet VIP vendu hors agence exploitante

1. Guichet Douala réserve une place d'un départ VIP exploité par Yaoundé, affecté à véhicule VEH-V04 (gamme VIP à l'heure du départ).
2. La vente acquittée crée un billet, reçu, encaissement *à Douala* et événements outbox atomiques. Le traitement comptable du produit suit la politique de reconnaissance documentée.
3. Une seule source de chiffre d'affaires est ventilée sur ACT-PAX / GAM-VIP / VEH-V04 / VOY-... / LIG-... / AGC-exploitation-Yaoundé / CAN-guichet.
4. Les états de performance du guichet Douala présentent la vente selon son rôle de point de vente ; l'état exploitation Yaoundé la rattache au voyage. Pas d'addition de deux chiffres d'affaires.
5. En absence d'Internet, la transaction locale demeure durable ; le siège ne l'intègre qu'après synchronisation vérifiée et reporte l'état de fraîcheur.
6. Un scan QR confirme l'embarquement sans créer une nouvelle vente. Le voyage clôturé alimente les états de rentabilité.

## Exemple de bout en bout — Colis sur véhicule VIP

1. Agence Bertoua facture l'expédition `COL-78` pour 20 000 FCFA, activité `ACT-COL`.
2. Le colis est transporté par un véhicule VIP sur un tronçon (event `ParcelLoaded` puis `LegCompleted`).
3. Politique de répartition assigne 20 000 au seul tronçon s'il est unique, ou une part sur chaque tronçon si trajet multi-véhicules ; la somme reste 20 000.
4. Le compte de rentabilité du véhicule VIP inclut sa contribution de messagerie ; **le chiffre d'affaires « Billetterie VIP » exclut la messagerie**.
5. La réception/livraison n'est pas une seconde vente. Les litiges et remboursements ont leurs propres événements rectificatifs.

## Exemple de bout en bout — Garage / pièces

1. Magasin achète dix filtres : mouvement entrée de stock et dette/paiement selon facture. Pas d'affectation directe d'une charge filtre à dix véhicules.
2. Garage crée un ordre de réparation pour VEH-C03 Classique.
3. Magasin sort deux filtres au coût valorisé ; l'événement de consommation crée le coût du véhicule selon politique de valorisation retenue.
4. Mécanicien impute ses heures via bon validé ; attribution aux coûts VEH-C03 et service GAR (selon vue directe ou commune), sans deuxième salaire comptable.
5. La marge du véhicule et la performance de l'atelier deviennent consultables avec accès à toutes les pièces sources.

## Exemple de bout en bout — Personnel / chauffeur

1. RH gère le contrat salarié et valide la paie après contrôles réglementaires.
2. La paie génère les écritures de charge/dettes correspondantes ; les paiements éventuels apurent les dettes.
3. L'imputation analytique repose sur les feuilles d'affectation/chauffeur-voyage ou le service et les heures, pas uniquement sur la dernière affectation connue.
4. Une avance de mission au chauffeur reste un **compte d'avance** jusqu'à justification ; les dépenses acceptées alimentent alors le voyage/véhicule et apurent l'avance selon les règles retenues.

## Exigences anti-fraude transversales

- Enregistrer documents source/acteur/date pour chaque imputation.
- Interdire « édition libre » d'une ligne de résultat calculé sans écriture de correction et justification.
- Conserver une seule autorité de validation du billet par voyage/segment.
- Signaler les trajets impossibles (même véhicule sur deux départs incompatibles) et les gammes incompatibles.
- Assurer l'idempotence des événements `ticket`, `shipment_leg`, `fuel_issue`, `stock_issue`, `payroll_approval`, `partner_settlement`.
