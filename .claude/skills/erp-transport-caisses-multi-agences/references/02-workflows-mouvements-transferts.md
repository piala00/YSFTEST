# 02 — Chaînes interservices, mouvements et transferts

## Billetterie et courrier dans une petite agence, caisse unique

1. Service Billetterie émet la pièce `billet#B1` avec `service_id=BILLETTERIE` ; l'agent enregistre le paiement espèces sur `cashbox_id=PRINCIPALE`, source `billet#B1`.
2. Service Courrier émet `colis#C1` avec `service_id=COURRIER` ; encaissement espèces sur **la même** caisse PRINCIPALE, source `colis#C1`.
3. La caisse contient deux mouvements avec services sources distincts ; rapport **service** et rapport **caisse** exploitent le même registre, sans doublon.
4. Montant électronique Mobile Money peut être accepté par le même guichetier mais va au **portefeuille électronique**, non dans les espèces physiques de la caisse.

## Grande agence, plusieurs caisses

1. Billetterie émet ses pièces et encaisse en caisse BILLETTERIE.
2. Courrier émet ses pièces et encaisse en caisse COURRIER.
3. Garage saisit un bon de réparation et une demande de paiement : cela crée coût analytique selon règles de consommation et dettes éventuelles, **pas mouvement d'espèces immédiat**.
4. Caissier de la caisse CENTRALE règle la dépense approuvée : mouvement `cash_disbursement` lié à la pièce garage et au véhicule ; ne pas requalifier la dépense de l'entreprise une deuxième fois.

## Transfert interne entre deux caisses de même société/agence

Exemple : BILLETTERIE remet des fonds à CENTRALE.

1. Émettre `cash_transfer_requested` avec identifiant unique, caisse source, caisse destination, montant/devise, auteur, motif, justificatif et autorisations.
2. Dans une transaction locale, réserver/débiter la source **une seule fois** ; statut `PENDING_RECEIPT` / `IN_TRANSIT`. Les fonds restent propriété de l'entreprise.
3. La caisse destination confirme réception et décompte des fonds (peut être à un autre instant) ; inscrire la contrepartie une fois, statut `COMPLETED`.
4. Si écart, refus ou perte, enregistrer `DISPUTED` et acte d'ajustement séparé, pas simplement supprimer la sortie ; traçabilité complète de la chaîne de garde.
5. Si les caisses ne communiquent pas (autre site hors ligne), traiter le transfert comme **remise en transit**, conserver une autorité sur l'identifiant, ne pas autoriser deux confirmations. Réconciliation à la reconnexion.

**Invariant** : la somme de l'argent en source + destination + en transit demeure inchangée par un simple transfert hors frais/pertes explicitement constatés. La trésorerie consolidée inclut le transit avec une ligne séparée au besoin. Une mutation de deux sous-comptes d'espèces peut exiger deux lignes de mouvement, mais **zéro vente et zéro charge d'exploitation**.

## Remise à la banque / dépôt au siège

- Remise en banque : transfert de trésorerie, **pas charge** ; tenir en transit jusqu'au crédit bancaire rapproché.
- Remise à la caisse centrale au siège : mouvement source agence / transit / réception siège ; **pas nouvelle recette** du siège. L'origine est l'agence qui a encaissé la vente.
- Frais réels de transfert/dépôt : pièces de charges distinctes si applicables.

## Annulations, retours et remboursements

- Une annulation de billet ne supprime pas sa vente ancienne : elle génère avoir/annulation traçable et, le cas échéant, un **remboursement financier distinct** depuis la caisse ou le compte effectif.
- Un remboursement Mobile Money n'est pas un décaissement d'espèces.
- Écritures de régularisation et pièces inverses, signatures et raison obligatoires, références immuables.

## Dépenses à ne pas confondre avec mouvements de caisse

- Facture fournisseur / commande / pièce du garage / frais de personnel calculés : n'impliquent pas tous un décaissement à la même date.
- Paiement partiel : payer `amount_paid ≤ amount_due` selon statut, reste dû géré en auxiliaire ; jamais doubler la charge analytique.
- Avance au chauffeur : mouvement de trésorerie vers l'équipe, créance/avance à justifier, **pas automatiquement charge définitive** ; liquidation ultérieure sur justificatifs et reliquats.
- Carburant imputé au véhicule lorsque réellement attribué/consommé selon flux métier, indépendamment de la caisse ayant réglé le fournisseur.
