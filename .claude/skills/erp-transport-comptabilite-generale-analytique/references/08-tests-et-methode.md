# 08 — Tests d'acceptation et protocole Claude Code

## Tests fonctionnels obligatoires (décrire fixtures et résultats)

1. **Menu** : Gestion comptable contient deux sous-modules ; analytique affiche seulement deux rubriques de restitution (`Véhicules`, `Propriétaires`), les 10 dimensions sont présentes en filtres/réglages.
2. **Billet VIP** sur véhicule VIP : vente une fois, recette véhicule à la date pertinente, agrégée au propriétaire en vigueur. Un billet VIP sur véhicule Classique est rejeté.
3. **Billet payé hier / départ aujourd'hui** : pas de nouveau mouvement de caisse aujourd'hui ; rapport exploitation et comptabilité selon les bonnes dates.
4. **Bagage voyageur** facturé : recette indépendante de la billetterie, affectée au bon véhicule.
5. **Colis multi-véhicules** : allocation répartie justifiée, total des parts = total éligible, pas deux fois le CA.
6. **Garage** : achat d'une pièce en stock et sortie de stock pour réparation ; charge attribuée au bus uniquement au fait de consommation applicable ; aucune double charge.
7. **Carburant et voyage** : coût voyage/véhicule, pas service de billetterie.
8. **Paie équipage** : part imputable au véhicule selon présence/affectation, et paiement des salaires n'ajoute pas une seconde charge.
9. **Deux véhicules d'un même propriétaire** : total propriétaire = somme des résultats des 2 bus sur la période, pièces et répartition visibles.
10. **Changement propriétaire** à une date T : historiques attribués aux bons propriétaires, contrat daté, aucun changement rétroactif.
11. **Compte courant partenaire** : bénéfice analytique ≠ dette payable ; avances, retenues et règlements affectent solde sans fausser résultat véhicule.
12. **Compagnie propriétaire** : véhicule analysé mais aucun solde partenaire artificiel.
13. **Charges non affectables aux véhicules** : elles figurent en générale, pas de répartition fictive, rapprochement explicite.
14. **Multi-caisses** : petite agence caisse unique et grande agence plusieurs caisses ; transferts internes exclus du CA ; ventes et paiements séparés.
15. **Offline + reprise** : rejouer deux fois le même événement et recevoir dans le désordre contrôlé ; 1 seule écriture GL et 1 seule imputation analytique, aucune perte, statut provisoire tant que non synchro.
16. **Annulation/avoir/retour** : correction de recette véhicule et propriétaire, préservation de trace historique et rapprochement.
17. **Sécurité** : partenaire A ne consulte ni ne télécharge les comptes du partenaire B, ni période hors contrat ; accès restreint par compagnie/agence.
18. **Rapports** : chiffres dans tableau véhicules = éléments agrégés propriétaire et pièces sources ; grand livre société inclut les non-affectés.
19. **Clôtures** : écritures validées immuables, correction par mouvement inverse, dates et responsabilités tracées.
20. **Exports** : rapport imprimé avec en-tête, période, devise, totaux, statut synchro et labels explicites de recettes vs mouvements de trésorerie.

## Méthode imposée à Claude Code

### Audit préalable

Repérer l'organisation actuelle des modules, navigation, modèles de données, tables partenaires, véhicules, voyages, achat/stock, vente, GL, droits, caisse et hors connexion. Noter `fichier/ligne`, états des migrations, dépendances et tests ; l'architecture doit se conformer à l'existant, pas générer une deuxième application autonome.

### Implémentation itérative

1. Valider navigation et dictionnaire métier.
2. Ajouter contraintes et relations d'ownership historique en migrations additives.
3. Réutiliser les moteurs d'écritures généraux et analytiques ; ajouter adaptation de sources et allocations manquantes.
4. Développer requêtes états véhicule + propriétaire et contrôle de rapprochements.
5. Mettre l'interface simple, navigation, sécurité et export.
6. Tester sur scénarios ci-dessus et jeu de données réaliste (agences mono/multi-caisses, bus VIP/Classique, au moins 2 propriétaires, changement, garage, paie, colis).
7. Fournir diff/références fichiers, migrations, tests réellement exécutés et leurs résultats ; si des dépendances empêchent le développement, signaler clairement les limites.

### Intégrité et reprise

Préserver les bases de production, sauvegarder avant modification, pas de suppression de comptes ni d'axes historiques, ne jamais faire de migration irréversible sans approbation spécifique. Prévoir redémarrage sûr des workers de synchronisation et de comptabilisation après panne.
