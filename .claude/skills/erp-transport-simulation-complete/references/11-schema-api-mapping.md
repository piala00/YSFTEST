# Tables / attributs / endpoints cibles (adapter à l'existant)

Ce schéma est conceptuel, à mapper au projet réel, **pas une instruction de créer aveuglément toutes ces tables**.

| Domaine | Entités clés | Contraintes / liens |
|---|---|---|
| Société/agences | company, branch, department, cashier, cash_session | company_id / branch_id / caisse_id ; clôtures locales |
| Flotte | vehicle, vehicle_class_history, vehicle_ownership_period, vehicle_contract | type physique ≠ gamme ; propriété effective datée |
| Voyages | route, segment, departure, seat_allocation, boarding_validation | une place unique par tronçon/départ, anti-passback |
| Billetterie | booking, ticket, ticket_payment, refund | agence vente ≠ agence exploitation ; encaissement ≠ prestation |
| Colis | shipment, shipment_leg, dispatch_manifest, delivery_proof | véhicule fret/bus, statuts et dates livraison |
| Garage | work_order, vehicle_usage, spare_part_issue, maintenance_invoice | charge au véhicule seulement sur consommation/GA |
| Achats | purchase_request, supplier_quote, purchase_order, po_line | transitions autorisées et approbations |
| Stock | warehouse, stock_receipt, stock_movement, stock_transfer, stock_issue | dépôt, article, coût, inventaire et sérialisation |
| Comptabilité | gl_entry, gl_line, account, third_party, payment, reconciliation | écritures équilibrées, seules POSTED définitives |
| Analytique | analytic_axis, analytic_section, analytic_allocation | FK gl_line_id obligatoire, sum allocations = montant GL |
| RH/Paie | employee, attendance, payroll_period, payslip, payslip_payment | localité, statut, versement, barèmes à valider |
| Propriétaires | owner, contract, owner_royalty, owner_payment | droits contractuels ≠ solde comptable dû |
| Offline | outbox, inbox, sync_cursor, conflict_queue | idempotence clé composite source/revision |

APIs (illustration, conserver les routes effectives de l'ERP) : `GET /agences/{id}/rapport-journalier?date=...`, `GET /compta/general/entries`, `GET /analytique/vehicules/{id}/grand-livre`, `GET /analytique/proprietaires/{id}/situation`, `GET /reporting/comparatif`, `POST /achats/bons-commande`, `POST /stocks/sorties`, `POST /paie/periodes/{id}/cloturer`, `POST /sync/events`. Pour chaque API : RBAC, pagination, filtres date fuseau Afrique/Douala, clés sources, validation et audit.

## Index des CSV du jeu
- `agences, caisses, vehicules, partenaires, contrats, employes, voyages, billets, colis, depenses`
- `demandes_achat, devis_fournisseurs, bons_commande, lignes_achats, receptions, factures_fournisseurs, reglements_fournisseurs, articles, mouvements_stock, consommations_stock, stock_final`
- `bulletins_paie, situations_partenaires, ecritures_entetes, ecritures_lignes, ventilations_analytiques, etat_vehicules, synthese_agences, rj_agences_synthese, balance_generale_demo, comptes_demo`

Le générateur est un **fixture de tests**, pas une architecture logicielle de production. Après audit, adapter les importateurs pour passer par les validations métier et GA, jamais par injection brute de CSV en base réelle.
