# Scénarios d'acceptation (obligatoires, avec preuves réelles)

## Jeux de données et validations exécutables
Exécuter `python .../scripts/validate_demo.py` et joindre la sortie. Ce contrôle analyse fichiers CSV produits par générateur (pas le projet ERP !). Puis faire les mêmes tests **sur la base et les API réelles de l'ERP** après import sécurisé.

1. Huit agences, trois cents employés, 60 bus voyageurs, 5 courrier, 15 bus partenaires, deux gammes exclusives, fiches datées, chaque partenaire possède au moins un véhicule.
2. Exactement **30 dates** et 8 agences dans les rapports journaliers ; 300 bulletins septembre, paie datée au 30/09.
3. Ventes : billets individuels avec voyage, siège valide unique, agence vendeuse et exploitante ; somme lots vente = somme billets.
4. Deux tentatives simultanées d'achat du même siège refusées ; anti-réutilisation QR sous autorité locale (pas deux validations simultanées).
5. Colis : bordereau, caisse/paiement, véhicule transporteur, statut livré/à livrer, comptabilité selon reconnaissance ; suivi même transport par véhicule courrier ou bus voyageurs.
6. Un devis transformé en commande ne poste PAS de charge ni de dette ; facture réceptionnée validée poste le passif fournisseur ; paiement ne crée pas une deuxième charge.
7. Réception stock = actif ; sortie = charge GA + analytique véhicule seulement si applicable ; pas de stock négatif ou double consommation ; transfert interne neutre en résultat.
8. Comptabilité GA : égalité débits/crédits par écriture et globalement ; soldes 401, 422, 431, 467, 521/552/57 rapprochables ; aucun mouvement final sans justificatif.
9. Toute ventilation analytique à lien `source_gl_line_id` existant et statut POSTED ; somme des ventilations par ligne = montant éligible de GL ; cas de charge répartie 60/40 sans double comptage.
10. Véhicules : somme des produits/charges liés au GL ; états des deux gammes et résultats par agence, période et propriétaire ; aucun 45 000 courrier RJ réparti sans trace du bus.
11. Paie 300 : net + retenues = brut ; charges patronales correctement ajoutées et déductibles du résultat de la bonne période ; paiement net sans second débit de charge.
12. Partenaires : droits datés du contrat, redevance GL POSTED, compte auxiliaire et reliquat, paiements distincts du résultat; empêcher doubles règlement.
13. Caisse physique négative (RJ exemple −162 000) : anomalie bloquante; l'écran affiche une piste d'explication, pas une conclusion comptable erronée.
14. Reporting : comparatifs sur journées/semaines/agences/vehicules, semaines sans activité ≠ absence de synchronisation; pas de mois N-1 inventé.
15. Synchronisation : rejouer dix fois même événement sans doubler vente/GL/stock; conflits mis en quarantaine; réconciliation locale/siège et statuts visibles.
16. Autorisations : guichetier ne peut pas voir paie globale; partenaire A n'accède pas aux véhicules de B; pièce justificative masquée si accès refusé.
17. RJ généré à 00:05 ne présente pas les trajets de 06:00 comme départs effectués ce jour; la date locale/coupure et date d'activité sont comparées.
18. Export de retour : pas de mots de passe, tokens, données de clients réels, PII, bases production, clés SSH ou dumps secrets.

## Définition de « terminé »
`implémenté dans code` + `test automatisé réussi` + `test métier visible` + `données vérifiées` + `documentation / procédure de reprise` + `retour de Claude`. Un pseudo-code dans ce Skill ne vaut pas réalisation dans le logiciel.
