# 06 — Écrans, navigation, autorisations et rapports

## Arborescence fonctionnelle souhaitée

`Gestion comptable → Comptabilité analytique`

Onglets :
1. **Tableau de bord analytique** : résultats, marges, statut des synchronisations.
2. **Plans analytiques** : créer/éditer/désactiver/consulter axes, dates d'effet.
3. **Sections analytiques** : gérer sections reliées aux agences/véhicules/partenaires/voyages, import contrôlé.
4. **Règles d'imputation** : prévisualisation, versions, dates d'effet, approbation, publication.
5. **Clés de répartition** : base mesurée, méthode d'arrondi, périodes, simulation et signatures.
6. **Ventilations** : écritures et lots, statut, justification, documents sources.
7. **Anomalies/rapprochement** : non affectés, conflits gammes, événements incomplets, écarts comptables.
8. **Rapports analytiques** : véhicule, voyage, agence vente/exploitation, gamme Classique/VIP, activité, ligne, service, propriétaire, contrat et global.
9. **Budgets/prévisions** (phase ultérieure) : budgété vs réalisé selon mêmes axes.

Dans le module `Flotte → Fiche véhicule` ajouter : gamme d'exploitation Classique/VIP, historique des changements de catégorie, propriétaire/contrat daté, centre analytique, rapports associés. `Voyages → Nouveau voyage` affiche les véhicules disponibles **filtrés par gamme compatible** et la politique tarifaire correspondante.

## Permissions minimales

| Rôle | Sections / règles | Données analytiques | Validation/rapport |
|---|---|---|---|
| Administrateur métier | gérer catalogues et sections selon autorisations | consultation globale autorisée | ne valide pas seul toutes opérations financières |
| Comptable analytique | proposer règles, contrôler imputations | accès détail selon société | rapprocher/valider avec séparation des tâches |
| Contrôleur de gestion | proposer clés, simulation | analyses et tableaux de bord | approuver clés selon délégation |
| Directeur d'agence | lecture seule de sa portée | son agence, véhicules et voyages autorisés | visualiser son arrêté quotidien |
| Billetterie | aucun accès de paramétrage | voir chiffre d'affaires de son guichet | émettre billets, non modifier les imputations |
| Garage | aucun accès règles comptables | coûts des ordres relevant de son périmètre | valider travaux selon droits, non modifier bilan |
| RH | pas d'accès aux comptes des partenaires | coûts salariaux agrégés nécessaires | paie accessible uniquement au rôle RH comptable |
| Partenaire | aucun paramétrage | son périmètre uniquement, chiffres filtrés | relever son compte sans données d'autrui |

**Tout filtrage est imposé côté API/DB** : restreindre `tenant_id`, société, agence et véhicules explicitement autorisés. La simple dissimulation des menus n'est pas un contrôle de sécurité. Toute approbation de rétroactivité doit laisser une trace.

## Rapports indispensables avec filtres et drill-down

- **Résultat par gamme** CLASSIQUE vs VIP, avec produits passagers séparés des colis, coûts directs, frais communs et résultat ; comparer taux de remplissage, recette moyenne par siège et kilomètre.
- **Résultat par véhicule** : coûts et produits par date, voyage, gamme, partenaire ; totaux calculables et lien à chaque document.
- **Résultat par voyage** : produits billetterie, contribution colis, carburant, péages, RH, incident, marge.
- **Résultat par agence** : ventes effectuées vs exploitation économique, différence explicitée ; caisse distincte.
- **Résultat par partenaire** : marges analytiques et solde financier présentés séparément.
- **Rapport de service** : billetterie, messagerie, garage, RH, etc. → rapport global agence après clôture.
- **Tableau de rapprochement** : GL vs analytique, allocable vs non affecté, écarts, doublons, anomalies.

Filtres : société, exercice, période/date/jour, agence de vente, agence d'exploitation, ligne/tronçon, gamme, activité, véhicule, partenaire, contrat, voyage, département, état de validation/synchro. Prévoir exports PDF/XLSX selon outils existants, et ancrage dans la navigation préexistante.

## UX requise

Les agents métier n'ont PAS à saisir manuellement les dix axes à chaque vente, ordre atelier ou facture. La majorité des sections est déduite du document source. Seuls les cas spéciaux ouvrent une fenêtre de correction avec droits, motif, aperçu d'impact et historique.

Afficher toujours la définition des KPI : par exemple « produit net imputé après avoir » et « revenu encaissé » sont deux indicateurs distincts. Couleur/statut `COMPLET`, `PROVISOIRE`, `A_CONTROLER`, `NON_SYNCHRONISE`; ne pas masquer les dates de rafraîchissement.
