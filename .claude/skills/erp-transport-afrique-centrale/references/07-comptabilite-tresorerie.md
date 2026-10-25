# 07 — Comptabilité OHADA, trésorerie, caisses et analytique

## Distinctions incontournables

1. **Document commercial** : billet, facture de colis, facture atelier/achat.
2. **Fait générateur / reconnaissance comptable** : peut être différent du jour d'encaissement ou de réservation ; politique écrite et validée.
3. **Paiement** : mouvement de caisse, banque ou Mobile Money réel, avec référence et rapprochement.
4. **Comptabilité générale** : écriture équilibrée, validée, datée et non effaçable en silence.
5. **Comptabilité analytique** : distribution mesurable de produit/charge entre agences, services, lignes, voyages, véhicules et partenaires.
6. **Centralisation multi-agences** : une seule société peut avoir plusieurs établissements ; **consolidation légale** de plusieurs sociétés relève d'une autre procédure et d'autres exigences.

## Livres et référentiels

Plan comptable SYSCOHADA révisé approprié à l'activité et au pays, journaux (ventes, achats, caisse, banques, OD, paie, etc.), exercices/périodes, comptes de tiers, auxiliaires, centres analytiques, règles de taxation/TVA, balance d'ouverture, lettrage, échéancier, rapprochements bancaires, éditions grand livre/balance/bilan/compte de résultat/notes selon obligations applicables. Autorisations distinctes de saisie, validation, annulation, clôture.

**Ne pas inventer de numéros de comptes ni taux fiscal/sociaux.** Fournir des catégories symboliques de comptes dans les exemples et exiger leur mapping par expert-comptable/gestionnaire habilité : `CA_TRANSPORT`, `CA_MESSAGERIE`, `CA_GESTION_PARTENAIRE`, `CLIENT_A_RECEVOIR`, `ESPECES_AGENCE`, `BANQUE`, `MOBILE_MONEY_TRANSIT`, `FOURNISSEUR`, `SALAIRES_DUS`, `PARTENAIRE_DU`, `CHARGES_CARBURANT`, `STOCK_PIECES`, `TVA_COLLECTEE_APPLICABLE`, etc.

## Moteur de règles comptables

Table `posting_rule` versionnée par société, pays, nature de service, type de contrat, date d'effet, événement-source, clé de taxe et statut ; chaque règle crée lignes équilibrées dans une transaction. Exemple de correspondances **conceptuelles** :

| Événement | Impact métier | Effets financiers et comptables attendus |
|---|---|---|
| Billet réservé | capacité réservée | ni recette ni caisse tant que non facturé/encaissé |
| Billet émis/facturé | vente ou revenu différé selon politique | créance/revenu ou produit constaté d'avance (schéma à valider) |
| Encaissement billet | caisse augmente | contrepartie créance/compte approprié ; **pas deuxième vente** |
| Ticket remboursé | annulation autorisée | avoir/correction puis remboursement effectif si paiement |
| Colis facturé | vente de messagerie | créance/reconnaissance selon service rendu |
| Bon carburant sur facture fournisseur | coût/stock selon nature | dette fournisseur tant qu'impayée |
| Sortie pièce stock pour réparation | consommation | charge analytique véhicule et sortie d'inventaire, sans second achat |
| Avance chauffeur | remise temporaire de fonds | compte d'avance à justifier, pas une dépense consommée |
| Justificatifs chauffeur acceptés | frais de voyage | apurement de l'avance et charge pertinente |
| Paie approuvée | salaires et charges | dette salariale/sociale et charge ; règlement ensuite |
| Décompte partenaire approuvé | droit/dette ou commission | schéma déterminé par contrat, statut principal/agent |
| Paiement partenaire | trésorerie sort | apure la dette/avance concernée, sans charge doublée |

**Idempotence comptable** : la clé de liaison `source_event_id + posting_rule_version + journal_type` interdit deux écritures identiques lors d'une retransmission. Une rectification fait l'objet d'un nouvel événement. Enregistrer `journal_entry`, `journal_line`, total débit/crédit, provenance, dimensions, poste utilisateur, horodatage, période, devise, taux de conversion vérifié le cas échéant.

## Caisses et moyens de paiement

- Une caisse/guichet physique ou virtuelle rattachée à agence, devise et responsable ; session ouverte/fermée avec solde d'ouverture ; aucune collecte hors session sans procédure spéciale.
- Espèces, mobile money, carte, virement, chèque, règlement différé doivent avoir méthodes de rapprochement distinctes. Un paiement déclaré Mobile Money sans notification/confirmation ne doit pas être traité comme règlement irrévocable.
- Entrées/sorties : reçus, ordres autorisés, motifs, contreparties, moyens de paiement et justificatifs.
- Clôture : recettes attendues issues de documents payés, mouvements de caisse, remises, solde compté, écart, justification et approbation.
- Transfert d'argent agence A→siège ou A→B : deux étapes avec compte transitoire et preuve réception ; ne pas créer artificiellement une recette d'exploitation à B.
- Fournisseurs, salariés et partenaires : échéances et ordres de règlement séparés des paiements effectifs.

## Analytique et frais communs

Matrice d'imputation par transaction : coût **direct voyage** ; coût **direct véhicule mais non voyage** (entretien, assurance) ; coût **service/agence** (loyer, guichet) ; frais généraux siège ; coût **exclus du résultat partenaire** si contrat contraire. Les clés de répartition sont versionnées (kilométrage, places-km, nombre de trajets, heures, volumes, etc.). Tableau `cost_allocation` conserve source, méthode, base de ventilation, bénéficiaires et total égal à montant source éligible, avec règles d'arrondi.

Une charge de paie imputée analytiquement aux véhicules ne crée **pas une deuxième charge de comptabilité générale**. Les vues de résultat doivent afficher marge directe, marge après charges communes et éventuel résultat contractuel comme colonnes distinctes.

## Clôtures et contrôle

Journée opérationnelle par agence ≠ période comptable mensuelle ≠ exercice annuel. Les caisses se clôturent quotidiennement, les voyages à leur arrivée, la comptabilité selon période. Certaines pièces d'une agence déconnectée restent provisoires au siège. Périodes comptables verrouillées exigent une écriture dans une période ouverte autorisée, jamais réécriture silencieuse de journaux clos. Réconciliation : sous-livres billets/colis/paie/partenaires ≈ GL par compte, caisse ≈ fonds, stocks ≈ inventaires, totaux analytiques ≈ montants imputables.

## Conformité

Se référer à l'AUDCIF/SYSCOHADA révisé OHADA, expert-comptable local, fiscalité et paie nationale ; ne pas assimiler un rapport analytique à un bilan légal. Prévoir audit des mappings et version des règles.

## Mise à jour — caisses indépendantes par agence

Ajouter un sous-référentiel « Caisses d'agence » permettant 1..N caisses par agence, distinctes des services opérationnels et des comptes banque/Mobile Money. Une petite agence peut mutualiser les encaissements de la billetterie et du courrier. Une grande agence ou le siège peut avoir plusieurs caisses, y compris garage et centrale, si elles détiennent réellement de l'argent. Ne pas créer de faux décaissements sur simple saisie de charge.

Le transfert entre deux caisses (y compris la remise agence→siège) est un mouvement interne, **pas un chiffre d'affaires nouveau**. Historiser fonds en transit, réception, clôtures/contrôles par caisse et total consolidé agence. Voir `.claude/skills/erp-transport-caisses-multi-agences/SKILL.md`.

