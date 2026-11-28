# Catalogue des 10 plans et des états consultables

## Plans retenus

| Code fonctionnel | Plan et périmètre | Sections exemples et rattachements | États particuliers |
|---|---|---|---|
| AGC | Agences / Gares | agence siège/établissement, ses gares de vente et d'exploitation | compte d'exploitation agence, détail des gares, ventilation services, comparaison des agences |
| VEH | Véhicules | code véhicule, flotte Classique/VIP à date | compte d'exploitation véhicule, relevé carburant, entretien, frais par voyage, balance/grand livre |
| PRT | Propriétaires de véhicules | propriétaire sous contrat; jamais fournisseur simplement « partenaire » | compte d'exploitation de ses véhicules, relevé financier des droits, fixe/variable, avances, retraits, solde |
| DEP | Services/départements | billetterie, courrier, garage, RH/paie, exploitation, direction | coûts de service, produits imputés, coûts salariaux, charges communes |
| ACT | Activités | transport voyageurs, courrier/colis, affrètement, autres | résultat par activité et marge segmentée |
| GAM | Gammes transport | Classique, VIP | rentabilité comparée, coûts, revenus par gamme, sans compter deux fois les colis |
| LIG | Lignes/itinéraires | Yaoundé–Bertoua, Douala–Bafoussam, etc. | compte par ligne, recettes par tronçon, comparatifs et saisonnalité |
| VOY | Voyages/départs | identifiant du départ exécuté | compte du voyage, dépenses et produits imputés, écarts par départ |
| CTR | Contrats d'exploitation | contrat de propriétaire et versions datées | résultat contractuel, rémunérations garanties et variables, suivi obligations |
| CAN | Canaux de vente | guichet, revendeur, web, mobile | chiffre d'affaires reconnu, coût de distribution, commissions et efficacité |

Codes indicatifs : mapper avec les identifiants du projet existant; ne pas renuméroter les sections déjà utilisées.

## États communs (disponibles à partir de n'importe quel plan)

1. **Compte d'exploitation analytique** : produits, charges directes, charges réparties, marge et résultat (période et état de validation).
2. **Balance analytique par sections** : colonnes section, débit analytique pertinent, crédit, charges, produits, solde; totals dans un seul plan, résiduel non ventilé montré.
3. **Grand livre analytique** : date, pièce, journal, compte général à sept chiffres, libellé, section, montant imputé, contrepartie explicative, source (lien vers écriture générale).
4. **Journal des imputations** : ventilation par date/pièce/règle/version/section, audit et auteur d'une éventuelle correction.
5. **Détail des produits** par rubrique comptable + filtres de service, destination, départ et autres dimensions.
6. **Détail des charges** par rubrique comptable, charges communes, allocations explicites et non affectées.
7. **Tableau des coûts directs/indirects** : méthode de répartition, clé, base et effet chiffré.
8. **Tableau mensuel / évolution** : mois successifs, valeurs cumulées, pourcentages et période de référence.
9. **Comparatif N / N-1** : périodes libres et comparables, écarts absolus et relatifs.
10. **Classement des sections** : par produits, coût, résultat, marge et activité (avec garde-fous si valeurs non comparables).
11. **État des imputations manquantes / anomalies** : montants et écritures à affecter, rejets, incohérences et écarts de rapprochement.
12. **Justificatifs et pièces sources** : détail jusqu'aux écritures et documents d'origine; pas de montant sans origine GL.

## États particuliers

**Véhicule** : nombre de départs, kilomètres, passagers, recettes billets, bagages, colis réellement transportés, carburant, péages, garage/maintenance, consommations pièces, salaires imputables, assurance/amortissement, marge par voyage et résultat cumulatif. Distinguer données financières des KPI non financiers.

**Propriétaire** : portefeuille historique de véhicules et contrats; résultat des véhicules pendant les périodes où le contrat était effectif; rémunération fixe garantie ou avance, variable, droits déjà comptabilisés, règlements, retraits autorisés, avances et solde à payer. Ne jamais appeler « salaire » au sens de bulletin de paie salarié sans vérification juridique et fiscale.

**Agence/Gare** : exploité vs vendu, caisse(s) et moyens de paiement en pièces de rapprochement de trésorerie; rapport quotidien imprimable simple; ventilation des charges de siège/communes; total établissement distinct du total par gare.

**VIP / Classique** : gamme à date du véhicule, revenus passagers et coûts; les frais et produits de colis conservent l'activité « Courrier » et peuvent faire l'objet d'une analyse croisée sans duplication.

## États budgétaires et bilans

Le « bilan d'un véhicule » est un **état de gestion** ou compte d'exploitation, pas un bilan SYSCOHADA légal autonome. Le vrai bilan normalisé est produit en comptabilité générale. Les états budget/écart n'apparaissent que si un budget existe avec une source vérifiable; ne pas inventer de prévisions.
