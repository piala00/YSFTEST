# 03 — Données, filtres, vues, API (noms indicatifs)

**Ne pas supposer que ces tables existent**. Faire le mapping depuis le schéma réel, adapter aux ORM, modèles et migrations du dépôt.

## Sources de données nécessaires

| Source métier | Clés indispensables | Informations affichées |
|---|---|---|
| Société/agence | company_id / legal_entity_id / agency_id | entête, périmètre |
| Véhicule / catégorie historisée | vehicle_id + validity dates | code, nom, Classique/VIP |
| Voyage effectif | trip_id, vehicle_id, depart_agency_id, actual_departure_at, status | trajet, date, véhicule |
| Billet / lignes tarifaires | ticket_id, trip_id, segment, unit_price, amount, boarding_status, cancellation, revision | places, prix, total exploitation |
| Bagage voyageur | luggage_charge_id, trip_id, vehicle_id, destination, description, quantity, amount, ticket_id | liste et total bagages |
| Messagerie | parcel_id, consignment_id, receiving/payment_agency_id, description, destination | option colis |
| Transactions de caisse | cash_movement_id, cashbox_id, agency_id, business_date, type, payment_method, amount, status | caisse + sorties |
| Remises et comptage | remittance_id, agency_id, cashbox_id, actual_amount, posted_at, status; count_id | sommes reversées, écart |
| Clôtures / synchro | closure_id, service_status, source_cursor, sync_at, version | statut rapport |

Tous les faits financiers ont identifiant stable, document source et anti-doublon `(tenant, source_event_id, effect_type)`. Type monétaire exact `DECIMAL`/entier d'unité sans flottants ; fuseau horaire métier du pays et date de caisse distincte de la date serveur.

## Signature d'API indicative

`GET /companies/{company_id}/agencies/{agency_id}/daily-reports/{YYYY-MM-DD}?version=latest&format=json`

`GET /companies/{company_id}/agencies/{agency_id}/daily-reports/{YYYY-MM-DD}/print`

`GET /companies/{company_id}/agencies/{agency_id}/daily-reports/{YYYY-MM-DD}/export?format=pdf`

`POST /companies/{company_id}/agencies/{agency_id}/daily-reports/{YYYY-MM-DD}/close` — soumis à RBAC, validation de tous les services requis et idem-potence.

Vérifier que le `tenant` réel du compte autorise l'agence demandée, même si l'utilisateur modifie l'URL. La structure JSON devrait exposer : `header, passenger_rows, passenger_total, luggage_rows, luggage_total, parcel_rows, parcel_total, expense_rows, expense_total, cash_summary, quality_flags, source_refs, approvals`.

## Agrégations : précautions

- Pas de `JOIN` direct billets × bagages × paiements × dépenses dans une unique requête, sous peine de multiplication cartésienne. Agréger chaque source séparément par identifiant de fait, puis réunir les **totaux** dans la réponse.
- Grouper billetterie par `(trip_id, segment, fare_price, vehicle_id, service_class)` : pas par seul véhicule/date, puisqu'il peut partir plusieurs fois.
- Pour chiffres encaissés, agréger par **date et agence de réception du paiement** depuis les mouvements de caisse, pas depuis la table des billets.
- Réutiliser en génération HTML/PDF/export **un même objet de rapport** pour garantir identité des totaux ; versionner les éditions clôturées.
- Pagination, affichage lignes nombreuses et calcul de totaux côté serveur / DB indexée.
- Index possibles selon schéma : `(tenant_id, agency_id, business_date, status)` sur caisse, `(tenant_id, depart_agency_id, actual_departure_at)` sur voyages, `(tenant_id, trip_id, status)` sur billets/bagages ; éviter des index doublons non mesurés.

## Référentiel sortie imprimable

Voir `examples/rapport_journalier_agence_exemple.html`. Le HTML est une **maquette statique** de présentation, pas une implémentation de la logique API ou du moteur comptable.
