# Ressources humaines — un mois complet, 300 salariés et paie

## Organisation
300 fiches fictives et postes par agence, 120 équipiers (60 chauffeurs/60 convoyeurs, rattachement à un véhicule pour simulation), 180 postes billetterie/courrier/garage/comptabilité/achats/RH/administration/technique. Effectifs AG01=65, AG02=64, AG03=34, AG04=32, AG05=26, AG06=30, AG07=27, AG08=22.

## Pipeline paie (obligatoire en ERP réel)
Contrats, affectations, présence, absences, congés, heures/suppléments approuvés, avances, variables, calcul brut, cotisations/impôts selon **barèmes réellement vérifiés**, bulletin, validation RH, validation comptable, OD de paie en comptabilité générale, règlement net en banque/caisse, rapprochement, remises déclaratives, clôture période et états comparatifs.

## Données pédagogiques sans valeur réglementaire
`retenue salarié = 5 % du brut`, `charge patronale = 10 % du brut` : choix FICTIFS pour tester comptes et reports. Ne représentent ni CNPS, ni IRPP, ni droit du travail camerounais ; ne JAMAIS les utiliser en production. Tous les bulletins de septembre sont payés par banque le 30/09 ; les dettes sociales, fictives, restent à régulariser dans le jeu.

## Analytique
Le brut et la charge patronale sont d'abord des lignes GA validées. L'équipe chauffeur/convoyeur est rattachée au véhicule en section analytique ; les autres salariés restent au service/agence « NON_AFFECTE véhicule » tant qu'une clé de répartition validée n'a pas été appliquée. Ne PAS soustraire deux fois les salaires dans le résultat véhicule.

## Contrôles
- Comptes 422 nets à payer clôturés lors du paiement ; comptes sociaux/impôts rapprochés séparément.
- Tout bulletin lié à une écriture OD et à un virement de règlement ; empêchez double règlement et paies multiples même mois sans motif explicite.
- Paie régionale multi-agences et accès RH sensibles, chiffrement, journal de consultation et masquage des identifiants privés.
