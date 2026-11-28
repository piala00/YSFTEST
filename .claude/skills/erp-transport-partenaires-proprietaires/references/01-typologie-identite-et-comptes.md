# 01 — Typologie des tiers et identité unique

## Décision métier
Créer le rôle métier explicite `PROPRIETAIRE_VEHICULE` / `PARTENAIRE_PROPRIETAIRE` : il ne se confond pas avec `FOURNISSEUR`, `CLIENT`, `SALARIE`, `DEBITEUR_DIVERS` ou `CREDITEUR_DIVERS`. Le registre des tiers est commun, mais les relations, flux, permissions et sous-comptes auxiliaires sont séparés.

## Cas d'une même personne exerçant deux rôles
Un propriétaire peut vendre des pièces au garage : `party_id=PTY-001` possède `OWNER-001` + `SUP-003`. Sa dette de prestation fournisseur et sa créance de rémunération contractuelle propriétaire sont deux sous-ledgers **distincts**, avec journaux/pièces/échéances distincts. Affichage possible d'une fiche unifiée d'identité avec onglets séparés. Pas de compensation implicite ; toute compensation doit être expressément autorisée, justifiée et comptabilisée en GA.

## Données
- Personne/organisation : `party_id`, identité, nature, données légales, contacts et pièces d'identité avec permissions adaptées, dates et archivage.
- `party_role`: `party_id`, `role_type`, statut, date d'effet, références dans le domaine concerné.
- `owner_profile`: `owner_id`, `party_id`, conditions de versement, compte bancaire ou portefeuille vérifié, restrictions d'accès.
- `supplier_profile`: `supplier_id`, `party_id`, documents fournisseurs et comptes de dettes fournisseurs.
- `employee_profile`: `employee_id`, `party_id`, contrat de travail distinct et paie.
- `gl_third_party_account`: identité, type de rôle, sous-compte auxiliaire distinct, source réglementaire/plan de comptes paramétrable (sans imposer de numérotation OHADA fictive).

## Critères de validation
Impossible de comptabiliser une facture d'achat comme rémunération propriétaire ; impossible de présenter un solde fournisseur dans la rubrique `Propriétaires`. Le directeur habilité peut accéder aux deux sans fusionner les soldes. Historique et piste d'audit complets.
