# Audit (benchmark) du reporting : tous les états et statistiques possibles

Date : 26/10/2026. Cet audit confronte le catalogue de référence (75 états : comptabilité générale, analytique,
commerce, transport, direction) avec ce que le logiciel contient vraiment.

**Méthode.** Un état est noté « Existe » seulement s'il a :
- une page du logiciel (nom d'URL indiqué) ;
- un test automatique qui l'ouvre ;
- un affichage sur les données de la simulation de septembre 2026.

Le libellé d'un menu ne suffit pas.

**Statuts.**
- **Existe** : l'état est disponible.
- **Partiel** : une partie de l'état existe, avec ce qui manque indiqué.
- **Absent** : l'état reste à faire.
- **Volontairement absent** : il faudrait des formules ou des taux officiels non encore validés par l'expert-comptable ; rien n'est inventé.

Colonne « Gr. » : un graphique est dessiné juste sous le tableau (voir la fin du document).

## 1. Comptabilité générale

| État | Statut | Où dans le logiciel | Gr. |
|---|---|---|---|
| Balance générale | Existe | `comptabilite:balance` (période, comptes, export CSV) | — |
| Balance des comptes de tiers | Existe | `comptabilite:balance` comptes 4 à 4 | — |
| Grand-livre général | Existe | `comptabilite:grand_livre` | — |
| Grand-livre des tiers | Existe | `comptabilite:grand_livre` avec filtre tiers | — |
| Journal comptable | Existe | `comptabilite:journal` | — |
| Brouillard (écritures provisoires isolées) | Partiel | liste `comptabilite:ecritures` filtrée sur « provisoire » ; pas d'édition dédiée | — |
| Balance âgée clients / fournisseurs | Existe | `comptabilite:balance_agee`, `reporting:balance_agee` | oui |
| Échéancier clients / fournisseurs | Existe | `commercial:statistique` echeances_clients / echeances_fournisseurs | — |
| Justificatif de solde | Existe | `comptabilite:justificatif_solde` | — |
| Statistiques des tiers | Existe | `comptabilite:statistiques_tiers` | oui |
| Compte de résultat (et SIG) | Existe | `comptabilite:compte_resultat`, `?vue=sig` (selon le système du dossier) | — |
| Bilan | Existe | `comptabilite:bilan` (système normal ou SMT) ; maquette officielle à valider | — |
| Flux de trésorerie | Volontairement absent | formules SYSCOHADA à faire valider | — |
| Notes annexes | Volontairement absent | référentiel officiel à valider | — |
| Récapitulatif TVA | Existe | `comptabilite:tva` (TVA désactivée par défaut, aucun taux imposé) | — |
| Situation de caisse et banques | Existe | évolution (`reporting:evolution`, trésorerie fin de mois), balance des comptes 5 | oui |
| Rapprochement bancaire | Existe | `comptabilite:rapprochement` | — |
| Contrôles de clôture | Existe | `comptabilite:controles_cloture` : liste unique (brouillard, équilibre, caisses, 58, tiers, 471, liaisons, corrections, caisses, analytique), plus `cloture_exercice` | — |
| Variation mensuelle des comptes | Partiel | classes 6/7 et soldes 5, 411, 401, 467 mois par mois (`reporting:evolution`) ; pas compte par compte | oui |

## 2. Comptabilité analytique (pour chacun des plans, sans jamais additionner deux plans)

Plans Transport : agences, points de vente, villes, véhicules, propriétaires, services, activités, gammes, lignes,
voyages, contrats, et les plans de sections créés par l'utilisateur.

| État | Statut | Où | Gr. |
|---|---|---|---|
| Compte d'exploitation par élément | Existe | `analytique:element` état « exploitation » | — |
| Balance analytique | Existe | `analytique:axe` (chaque plan), `comptabilite:balance_analytique` (sections) | oui |
| Grand-livre analytique | Existe | `analytique:element` état « grand_livre » | — |
| Journal analytique | Existe | `analytique:element` état « journal » | — |
| Produits / charges par élément | Existe | `analytique:axe`, détail par compte (`analytique:element` « comptes ») | oui |
| Charges communes / ventilation | Partiel | `comptabilite:ventilation` (sections) ; le non-affecté des plans est montré, sans clé de répartition automatique | — |
| Résultat par élément | Existe | `analytique:axe`, `reporting:classement` | oui |
| Comparatif d'éléments | Existe | `reporting:comparaison`, `reporting:classement` | oui |
| Comparatif de périodes | Existe | `analytique:element` « comparaison », `reporting:comparaison` (précédente, N-1, libre) | oui |
| Évolution mensuelle | Existe | `analytique:element` « evolution », `reporting:matrice` | oui |
| Ventilation croisée (un plan par un autre) | Existe | `analytique:element` « croise » | oui |
| Budget vs réel | Existe | `analytique:budgets` → budget / réel (société ou un plan : par élément et par compte, hors budget, écarts favorables / défavorables) | oui |
| Écarts et anomalies d'imputation | Partiel | non-affecté et rapprochement sur chaque balance ; pas de liste des anomalies | — |
| Affecté / non affecté | Existe | `analytique:plan` (tous les plans) | oui |
| Classement de rentabilité | Existe | `reporting:classement` (résultat, produits, charges, marge) | oui |
| Rapprochement GL / analytique | Existe | sur chaque balance et comparaison (éléments + non affecté = générale) | — |

## 3. Commerce

| État | Statut | Où | Gr. |
|---|---|---|---|
| Chiffre d'affaires net des ventes | Existe | `reporting:ventes`, tableau de bord | oui |
| Achats par période | Existe | `commercial:etat_achats` | oui |
| Marges par famille et article | Existe | statistiques familles / articles, palmarès | oui |
| Ventes par article / par client | Existe | `reporting:ventes`, statistiques clients | oui |
| Ventes par commercial | Absent | pas de commercial (vendeur) sur les documents | — |
| Recouvrement et retards, créances échues | Existe | risque clients, balance âgée, échéances | oui |
| État du stock valorisé | Existe | `commercial:etat_inventaire`, `commercial:stock` | — |
| Rotation et ruptures | Existe | état « Rotation des stocks et ruptures » (`commercial:statistique` rotation_stocks) : stock début / fin, entrées, sorties, rotation, couverture en jours, alertes | — |
| Règlements et modes de paiement | Existe | état « Règlements par mode de paiement » (`commercial:statistique` reglements_modes), `commercial:reglements`, rapport commercial journalier | — |
| Performance agences et magasins | Partiel | rapport commercial par agence, échanges entre agences ; pas de comparatif multi-magasins | — |
| Avoirs et retours | Existe | état « Avoirs et retours clients » (`commercial:statistique` avoirs_retours) : pièce d'origine, montants, part du CA | — |

## 4. Transport

| État | Statut | Où | Gr. |
|---|---|---|---|
| Billetterie Classique / VIP | Existe | plan « gammes », `transport:recette_billetterie` | oui |
| Résultat par véhicule | Existe | `comptabilite:analytique_vehicules`, plan « véhicules » | oui |
| Résultat par propriétaire (économique) | Existe | `comptabilite:analytique_proprietaires` | oui |
| Solde dû au propriétaire (tiers) | Existe | `comptabilite:analytique_releves`, `partenaires:releves` | — |
| Compte d'exploitation par voyage | Existe | plan « voyages », `transport:rentabilite?axe=depart` | oui |
| Performance par agence / gare | Existe | plans « agences », « points de vente », « villes », `transport:recette` | oui |
| Rentabilité des lignes | Existe | plan « lignes », `transport:rentabilite` | oui |
| Activités et services | Existe | plans « activités » et « services » | oui |
| Rentabilité des contrats | Existe | plan « contrats » | oui |
| Ventes par canal | Partiel | plan « points de vente » (guichets) ; pas de canal en ligne / Mobile Money séparé | — |
| Occupation des sièges par gamme | Existe | `transport:rentabilite`, `reporting:comparaisons_transport` (remplissage) | oui |
| Recettes courrier et colis | Existe | `transport:recette_colis`, activité « colis et fret » | oui |
| Carburant par véhicule | Existe | `garage:consommation` | — |
| Garage / maintenance | Existe | `garage:reparations`, magasin (achats, sorties), charges du véhicule | — |
| Caisses par agence et par service | Existe | `transport:sessions_caisse`, `transport:rapport_journalier` | — |
| Règlements et transferts internes | Existe | `transport:transferts` | — |
| Décomptes des propriétaires | Existe | `partenaires:decomptes` | — |

## 5. Direction et scénarios

| État | Statut | Où | Gr. |
|---|---|---|---|
| Tableau de bord direction | Partiel | `reporting:dashboard` (orienté commerce) + `reporting:evolution` | oui |
| Top / bottom des éléments analytiques | Existe | `reporting:classement` | oui |
| Comparatif multisites | Existe | `reporting:comparaison` sur le plan agences ou villes | oui |
| Plusieurs mois, N et N-1 | Existe | `reporting:matrice`, `reporting:comparaison` (N-1) | oui |
| Trésorerie projetée | Existe | `comptabilite:tresorerie_projetee` : trésorerie réelle de départ, factures à échéance, prévisions uniques ou mensuelles, budget validé en option | oui |
| Écart scénario / réel | Absent | pas de scénario enregistré | — |
| Simulation par mois et cumulée | Existe | commande `simulation --nombre-mois N` (BILAN-SIMULATION.md, tableau mois par mois) ; tous les états sur le dossier de simulation | oui |
| Hypothèses et sensibilités | Absent | — | — |
| Anomalies et exceptions | Partiel | contrôles de la simulation, contrôle des liaisons, non-affecté | — |
| Couverture analytique par plan | Existe | `analytique:plan` | oui |
| Rapport mensuel de consolidation | Partiel | consolidation comptable au siège par les échanges ; pas d'édition mensuelle dédiée | — |

## 6. Bilan de l'audit

| Domaine | États | Existe | Partiel | Absent | Volontairement absent |
|---|---:|---:|---:|---:|---:|
| Comptabilité générale | 19 | 15 | 2 | 0 | 2 |
| Analytique | 16 | 14 | 2 | 0 | 0 |
| Commerce | 10 | 8 | 1 | 1 | 0 |
| Transport | 17 | 16 | 1 | 0 | 0 |
| Direction et scénarios | 11 | 6 | 3 | 2 | 0 |
| **Total** | **73** | **59** | **9** | **3** | **2** |

Ces totaux portent sur les lignes de ce document. Les deux balances âgées et les deux échéanciers du catalogue sont regroupés en une ligne chacun.

**Priorités proposées** (rien n'est commencé sans accord) :
1. ~~Budget, avec un état budget / réel par plan~~ — fait le 27/10/2026.
2. ~~Trésorerie projetée~~ — fait le 27/10/2026.
3. Vendeur sur les documents de vente, avec un état des ventes par commercial.
4. Canal de vente (guichet, Mobile Money, en ligne) comme plan analytique.
5. Liste unique des contrôles de clôture et des anomalies.
6. Export Excel (.xlsx).

À ce jour, les exports sont CSV et l'impression, PDF par le navigateur.

## 7. Statistiques disponibles

Chaque statistique est calculée sur les écritures générales validées. Les données d'exploitation (voyages, voyageurs, places) la complètent.
- **Société** : produits, charges, résultat, marge (%), trésorerie fin de mois, créances clients, dettes fournisseurs, dû aux propriétaires.
- **Par élément d'un plan** : produits, charges, résultat, marge, nombre de lignes, écart et variation entre deux périodes (%), rang.
- **Transport** :
  - départs, voyageurs, places offertes et remplissage (%) ;
  - billets, colis et fret, bagages ;
  - recettes, dépenses et marge par ligne, véhicule ou départ ;
  - part du propriétaire ;
  - net caisse par gare.
- **Commerce** :
  - CA HT, quantité, marge et taux de marge par article, famille et client ;
  - palmarès ;
  - encours et risque client ;
  - achats et reste à payer par fournisseur.
- **Tiers** : report, facturé, réglé, solde, taux de recouvrement, ancienneté des créances.

## 8. Tableaux simples et graphiques

Les tableaux gardent une ligne par élément, des montants alignés à droite, les négatifs en rouge et une ligne de total. Un graphique se dessine **juste en dessous** de chaque tableau marqué « oui » ci-dessus :
- courbes pour ce qui évolue dans le temps (mois) ;
- barres pour comparer des éléments ;
- barres horizontales pour les classements et les longues listes.

Le graphique relit les chiffres du tableau affiché, il montre donc exactement les mêmes montants. Le survol d'une barre ou d'un point donne la valeur. Au-delà de 15 lignes, seules les plus fortes sont tracées et le graphique le signale. Pour un tableau éléments × mois, 7 éléments au plus sont tracés, le reste est regroupé en « Autres ».

Mécanisme : `static/js/graphiques.js` (attribut `data-graphique` sur le tableau). La bibliothèque de graphiques fournie avec le logiciel n'est chargée que sur les pages qui ont un graphique.

Pages contrôlées dans un navigateur sur la simulation :
- évolution, comparaison, tableau mensuel, classements ;
- balance d'un plan, plan analytique ;
- comptes d'exploitation des véhicules, rentabilité, comparaisons du transport.

Chaque page affiche son graphique, sans erreur.
