# Comptabilité générale = référentiel monétaire UNIQUE

## Ne pas comptabiliser à partir du PDF agrégé
Le rapport RJ est un **document calculé**. Les écritures proviennent des ventes individuelles ou lots vérifiés, bordereaux, sorties, réceptions/factures, bulletins, règlements et autres faits validés. Le même achat ou la même vente ne peut pas être re-posté à partir de son cumul dans le RJ.

## Modèle minimal des mouvements GA
- `gl_journal_entry(id, entity_id, agency_id, date, journal_code, source_type, source_id, document_id, state=POSTED, currency, created_by, posted_by, offline_origin, external_event_id)`.
- `gl_journal_line(id, entry_id, account_id, debit, credit, third_party_id, due_date, currency_amount, tax_id, agency_id, source_line_id)`.
- Contrainte technique : débit=crédit par écriture, non négatif, devise et arrondis entiers FCFA, pièces liées, idempotence `source_event_id`, aucune suppression silencieuse après publication, inversion par contrepassation.
- Les écritures d'ouverture et de virement ne sont PAS des produits ou charges analytiques. Les comptes bancaires sont distincts des espèces et de la monnaie électronique.

## Maquette de pièces (fichier démonstrateur CSV)
- Billet vendu et voyage achevé : Débit caisse/mobile (ou compte de tiers approprié) ; Crédit revenus de transport, après application des règles de reconnaissance et taxes.
- Courrier expédié et service accompli : Débit caisse/mobile/tiers ; Crédit revenus courrier. **Si livraison future : traiter acomptes/produits à recevoir/différés selon règle validée — la simulation suppose livraison le même jour**, ce qui ne constitue pas une règle générale.
- Carburant consommé : Débit charge carburant, Crédit caisse/tiers.
- Achats stockés : Débit stock, Crédit fournisseur ; lors de sortie Débit charge correspondante, Crédit stock.
- Matériel durable : Débit immobilisation, Crédit fournisseur, puis amortissement si dû.
- Paie : Débit rémunérations brutes et charges patronales, Crédit dette salariale + cotisations ; paiement banque = extinction dette salariale, pas nouvelle charge.
- Redevance partenaire : après validation contrat/droits réels, Débit charge de prestation/partenariat correctement qualifiée, Crédit dette partenaire ; règlement réduit cette dette. La simple simulation du droit du partenaire ne suffit pas pour créer une dette légale en production.

**Codes du jeu d'essai** : `706-V`, `706-C`, `605-F`, `63-PE`, `624-R`, `60-S`, `661-DEMO`, `664-DEMO`, `63-PART` et autres comptes **ne sont pas un plan officiel validé**. Les distinctions `706-V/706-C` sont des comptes techniques de démonstration ; ne PAS déclarer que `7061=voyageurs` et `7062=colis`, car les subdivisions réelles de 706 suivent notamment le critère géographique. Imposer un mapping de configuration comptable validé par un professionnel SYSCOHADA.

## Conformité & contrôles
- Paramétrage taxes et obligations Cameroun/SYSCOHADA conforme au contexte réel, à faire valider avant mise en production ; aucun taux fictif pris comme légal.
- Rapports comptables définitifs = seulement GL POSTED + périodes autorisées ; si les autres agences n'ont pas synchronisé, étiquette « consolidation provisoire ».
- Grande balance de la société et balances auxiliaires : calculées sur GL, jamais sur vues analytiques.
- Tous les journaux de la simulation sont équilibrés au centime de FCFA : le générateur vérifie cette propriété.
