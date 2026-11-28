# 05 — Gestion du personnel, équipages, RH et paie intégrée

## Périmètre fonctionnel

Le personnel comprend guichetiers, agents colis, comptables, administratifs, mécaniciens, agents de sécurité, chauffeurs, convoyeurs, contrôleurs et responsables. Le logiciel doit pouvoir gérer le salarié affecté à une agence, à plusieurs agences, à un véhicule ou à un voyage, sans confondre son emploi légal avec une affectation ponctuelle.

## Sous-modules RH

| Sous-module | Fonctionnalités |
|---|---|
| Dossiers personnels | Matricule unique, identité minimale nécessaire, coordonnées, contrat, entrée/sortie, agence, poste, qualifications, pièces protégées |
| Contrats | Nature, durée, catégorie, rémunération de base, avenants, dates d'effet, historique, signatures |
| Affectations | Poste, agence, service, véhicule/voyage, remplacement, parcours professionnel |
| Présences | Pointage, présence, absence, retards, heures supplémentaires validées, missions |
| Congés | Demande, approbation, solde, calendriers, remplacements |
| Équipages | Affectation chauffeur/convoyeur, conformité habilitations, indemnités et primes de route |
| Discipline & incidents | Signalement encadré, accès restreint, procédure de contestation |
| Paie | Rubriques de gains/retenues, calcul, validation, bulletins, ordre de paiement, journaux |
| Avances/prêts | Décaissement, échéancier, retenues autorisées, compte de tiers salarié |
| Départs | Solde de tout compte contrôlé, restitutions, restrictions d'accès |

## Moteur de paie : étapes obligatoires

1. Importer ou valider les données RH pour une **période de paie** et une **société juridique**.
2. Calculer le brut à partir des rubriques applicables : fixe, primes, indemnités, heures, absences, congés ; les méthodes de calcul et définitions dépendent des lois, accords et contrats en vigueur.
3. Appliquer les cotisations, impôts/retenues autorisées et plafonds **via paramètres versionnés par pays et date d'effet**. Ne jamais coder en dur des taux non vérifiés (ex. CNPS, impôt sur salaires, contribution employeur).
4. Distinguer **brut**, **retenues salariales**, **charges patronales**, **net à payer** et **décaissement réel**.
5. Soumettre la paie à approbation RH puis finance selon seuils/contrôles ; geler un lot validé.
6. Générer bulletins sécurisés et écritures comptables équilibrées à partir de mapping SYSCOHADA approuvé.
7. Effectuer les paiements par caisse/banque/mobile money selon procédure, générer confirmations et rapprochements ; garder les salaires non réglés comme dettes et non comme paiements fictifs.
8. Gérer corrections par régularisations avec piste d'audit, et déclarations sociales/fiscales dont les formulaires sont validés pays par pays.

## Analytique des frais de personnel

- Mécanicien ayant réparé V1 : valorisation de main d'œuvre interne **selon politique de coûts** et feuille de temps, sans double charge en comptabilité générale.
- Chauffeur affecté à un voyage : salaire fixe/variable, primes et indemnités séparés. Allocation salariale possible par heure, jour, kilomètre ou voyage selon règle écrite ; période de paie clôturée peut différer de période de voyage.
- Guichetier/agent colis : coût direct du service ou frais indirects de l'agence ; ne pas les répartir systématiquement sur tous les véhicules sans justification.
- Double attribution interdit : coût analytique alloué à plusieurs véhicules doit totaliser le coût éligible et expliquer le reliquat non ventilé.

## Comptes d'équipes embarquées

Le chauffeur ou convoyeur peut recevoir une avance temporaire de caisse. Il remet pièces de péages, carburant et frais de route ; un responsable valide ; la caisse encaisse le reliquat ou constate la dette résiduelle. Le rapprochement de l'avance est distinct des avances sur salaire et des primes de route.

## Confidentialité et autorisations

Bulletins, contrats, rémunérations, maladies et sanctions ont une visibilité minimale ; le chef d'exploitation peut voir les disponibilités et habilitations sans accéder à tous les détails RH. Segmentation par établissement ; chiffrement des documents sensibles ; historique des accès ; conservation limitée selon règle nationale vérifiée.

## Tests obligatoires

Salarié multi-agences, rétroactivité d'un contrat, avance salariale et avance de mission distinctes, paie validée non modifiable, salaire dû mais non payé, ventilation d'un mécanicien sur V1/V2, retenue non autorisée bloquée, fuite de bulletins entre employés, droit de lecture limité du chef de gare.
