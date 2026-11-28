# 15 — Plans analytiques ERP Transport : référentiel métier validé

## Règle actualisée et prioritaire

**La flotte CLASSIQUE et la flotte VIP sont constituées de véhicules distincts et dédiés.** La gamme d'un voyage passagers doit être égale à la gamme du véhicule affecté (classification historisée par date). Le prix du billet dépend notamment de la gamme et du trajet. Les dépenses directement rattachées au véhicule suivent sa gamme historique, sans ventilation forcée vers l'autre gamme.

## Catalogue retenu

Dix plans cibles : (1) AGENCES, (2) VEHICULES, (3) PARTENAIRES/PROPRIETAIRES, (4) SERVICES/DEPARTEMENTS, (5) ACTIVITES COMMERCIALES, (6) GAMMES CLASSIQUE/VIP, (7) LIGNES/ITINERAIRES, (8) VOYAGES/DEPARTS, (9) CONTRATS D'EXPLOITATION, (10) CANAUX DE VENTE.

Attention aux **deux rôles agence** : agence vendeuse / caisse, et agence exploitante / résultat du transport ; chaque vue agrège les faits originaux sans double comptage. Le propriétaire juridique du véhicule, le partenaire contractuel et le solde auxiliaire sont distincts ; affectations datées.

## Principe d'automatisation

Tous les services (billetterie, colis, exploitation, garage, carburant, stocks, RH/paie, trésorerie, comptabilité) produisent un fait métier unique. Le système calcule les imputations analytiques en fonction du voyage, du véhicule, de l'agence, du contrat et des règles de répartition approuvées. Un même montant est analysé sur plusieurs axes, **jamais additionné comme plusieurs montants d'exploitation**.

Le chiffre d'affaires des colis transportés en VIP reste dans l'activité COLIS et contribue à la marge du véhicule VIP sans devenir une vente de billet VIP. Une avance de chauffeur n'est pas une charge tant que non justifiée. Un achat en stock n'est pas automatiquement une consommation garage. Les charges communes sont allouées suivant des clés versionnées et auditables.

## Implementation de référence

L'implémentation détaillée, les modèles de données, validations, tests et interfaces sont dans le skill complémentaire suivant (même archive, installé au même niveau) :

`../../erp-transport-plan-analytique/SKILL.md`

Références de ce skill : `references/01-catalogue-axes-sections.md` jusqu'à `references/08-sources-et-limites.md`.

**Invocation conseillée :** `/erp-transport-plan-analytique`, puis auditer le dépôt avant modification, concevoir des migrations non destructives et exécuter les tests. Aucun fichier de ce package ne prouve que la mise à jour fonctionnelle de l'ERP est déjà réalisée.
