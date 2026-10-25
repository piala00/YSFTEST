# 11 — Rapport journalier d'agence, résultat des véhicules et centralisation siège

**Priorité UX pour le rapport journalier imprimable d’agence :** respecter le modèle **simple en tableaux** du skill `/erp-transport-rapport-journalier-agence`. La liste A–J ci-dessous constitue l’inventaire global des données de contrôle et des états détaillés disponibles dans l’ERP, **pas des blocs obligatoires de la feuille quotidienne imprimée**.

## Rapports à produire

### Rapport quotidien du service billetterie

Billets réservés/émis/embarqués/annulés/remboursés, caisse et moyens de paiement, distinction date d'émission/date de voyage, recette par ligne, agent, véhicule, voyages, écarts de justificatifs.

### Rapport quotidien de messagerie

Expéditions créées/encaissées, colis en chargement, transportés par voyage/véhicule, arrivés, remis, exceptions et indemnisations, encours à recevoir, COD en attente et colis non identifiés.

### Rapport garage et flotte

OR ouverts/fermés, pièces consommées, achats et réception, véhicules immobilisés, dépenses réparations (payées/non payées), carburant, km, coût/km, suivi d'entretien et alerte documents.

### Rapport du personnel

Présences/absences, effectifs par service/agence, voyages et équipes, salaires dus par période, paiements effectués, avances, charges ventilées (vue direction/RH seulement). Ne pas exposer données individuelles dans rapport grand public.

### Rapport caisse et trésorerie

Ouverture, ventes encaissées, créances non encaissées, dépenses réelles, remboursements, remises et transferts, encours Mobile Money, solde théorique, solde physique, écart, justification et approbation ; balances par caisse puis agence.

### Rapport comptable

Écritures validées, non validées/rejetées, équilibre, journaux, tiers, provisions selon règles, rapprochement, période close/non close, balance et états réglementaires. Rapport analytique distinct des états légaux.

### Rapport partenaires

Pour chaque propriétaire : véhicules, voyages, recettes éligibles, coûts refacturables selon contrat, droits calculés, avances/retentions, dettes, paiements effectués, solde comptable, pièces justificatives et litiges.

## Vues directionnelles

1. **Rapport agence** : tous les services de l'agence agrégés, mais chaque ligne demeure traçable vers sa source, avec état et taux de complétude.
2. **Rapport véhicule** : voyages et équipes, billets, colis par étape, kilomètres, carburant, péages, garage, paie imputée, autres coûts, marge directe, frais répartis, résultat complet, statut contrat partenaire.
3. **Rapport voyage** : étapes réelles, effectifs transportés, capacité/taux de remplissage, encaissements au guichet vs recettes allouées, colis, dépenses, écarts.
4. **Rapport ligne** : revenu par tronçon, fréquence, remplissage, rentabilité et incidents.
5. **Rapport compagnie** : centralisation de toutes agences de la société, comparaison et suivi dans le temps, état des dettes et créances, ventilation espèces/banques.
6. **Rapport multi-sociétés** : préconsolidation de gestion lorsque plusieurs entités, et consolidation légale seulement via procédures OHADA applicables avec éliminations/conversion et contrôles.

## Exemple structure type d'un rapport journalier agence

```text
COMPAGNIE / SOCIÉTÉ / AGENCE / DATE D'ACTIVITÉ
Statut : PROVISOIRE / CLÔTURÉ / PARTIELLEMENT SYNCHRONISÉ
Dernière remontée : timestamp par service

A. Billetterie : ventes, annulations, remises, remboursements, encaissé/non encaissé
B. Colis : ventes, remises, non remis, chargements, montants reçus
C. Voyages : programmés, partis, arrivés, différés/annulés
D. Flotte : véhicule, kilométrage, carburant, réparations, immobilisations
E. Personnel : présence, équipe voyages, charges RH admissibles, avances
F. Caisses : solde initial, espèces, autres paiements, sorties, solde réel, écarts
G. Comptabilité : pièces validées, en attente, comptes de régularisation
H. Partenaires : droits provisoires, décomptes validés, règlements
I. Anomalies : conflits sync, doublons, pièces absentes, exceptions métiers
J. Signature/approbation : responsables et horodatages
```

## Types de clôture

- `service_daily_close` : responsable de service confirme tâches, pièces et écarts ; les opérations interservices peuvent rester en cours.
- `cash_session_close` : fermeture de caisse avec comptage, justificatifs et approbation.
- `trip_close` : exploitation confirme les opérations du voyage ; late fees/corrections restent possibles via ajustement post-clôture.
- `agency_daily_close` : consolidateur rassemble services, mais signale non-synchronisés/attentes ; ne pas « déclarer complet » si un service essentiel n'a pas terminé.
- `fiscal_period_close` : comptable verrouille journaux selon procédure ; gère ajustements sur période ouverte.
- `head_office_snapshot` : vue globale, version/source/heure de dernière synchronisation par agence.

## Formule du résultat analytique véhicule

`Produits attribués au véhicule` moins `charges directes véhicule et voyages` = `marge directe`. Puis `moins frais communs ventilés` = `résultat analytique complet`, si le périmètre et les clés sont définis. Afficher sous-totaux : billets, colis, autres ; carburant, péages, réparations, pneus, frais d'équipe, charges fixes, amortissement si applicable et frais répartis. Un résultat contractuel partenaire se calcule séparément. Chaque poste doit disposer de drill-down (document source, propriétaire du chiffre, date, véhicule/voyage/partenaire, règle de ventilation).

## Visualisations / UX

Filtres combinables par société, agence, période flexible jour/mois/année, véhicule, voyage, ligne, service, partenaire. Comparaisons période N/N-1, graphiques, analyses par axe, export PDF/Excel, vues imprimables A4/A3, tableaux de bord rôles. KPI indicatif : chiffre d'affaires réel (définition explicite), encaissement, taux remplissage, colis livrés dans délais, coût/km, résultats des véhicules, marge par ligne, montants partenaires à payer, écarts de caisse, backlog de sync.

Ne pas appeler « temps réel » une information remontée avec décalage ; marquer fraîcheur et possibilité de retraitement après réception tardive des données.
