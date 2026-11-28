# Tests d'acceptation et retour collaboratif Claude Code

## Cas de test impératifs

1. Les 10 plans apparaissent en Comptabilité analytique sans perdre Véhicules/Propriétaires.
2. Plan AGC : section « Bertoua » donne compte d'exploitation, balance, grand livre, charges et détails des écritures sur la période.
3. Plan VEH : BUS-001 → résultat, coûts, grand livre avec liens aux pièces de GL; garde gamme CLASSIQUE/VIP à date.
4. Plan PRT : partenaire à trois véhicules, changement de contrat en cours de mois; chiffres antérieurs attribués à l'ancien propriétaire.
5. Une ligne GL de 100 000 imputée AGC+Bertoua et VEH+BUS-001 **compte 100 000, pas 200 000** dans le résultat société.
6. Ventilation d'une ligne 100 000 sur 2 véhicules dans le même plan : 60 000 + 40 000; une ventilation 100 000 + 100 000 dans le même plan est refusée.
7. Écriture BROUILLARD visible uniquement en vue provisoire contrôlée; pas dans les états certifiés. Contrepassation présente, pas de suppression historique.
8. Le grand livre d'une section contient date, compte général à 7 chiffres, n° pièce, montant et lien vers écriture validée.
9. Pour un plan ayant des sections mais aucune imputation source, l'écran affiche « Aucune imputation validée »; ne pas afficher un faux résultat 0 définitif.
10. Sélection « juin 2025 », mois précédent, période libre, comparaison N/N-1, page suivant/précédent: filtres cohérents; `Du > Au` refuse.
11. Reporting du même plan et même période = résultat de l'état analytique, centime pour centime; différence documentée lorsque périmètres différents.
12. Une agence hors connexion apparaît « informations partielles » avec dernière synchronisation; consolidation après reconnexion sans double compte.
13. Un propriétaire-fournisseur conserve ses comptes de tiers distincts et sa rémunération mensuelle propriétaire fixe/variable sans transformation automatique en paie salarié.
14. Interdiction pour un agent de gare A de lire les dossiers réservés gare B ou un autre propriétaire; audit des accès.
15. Export CSV/Excel/PDF (si réellement disponible) reproduit chiffres et filtres de l'écran; périodes conservées.
16. Tous les tests fonctionnent sur la flotte de démonstration (8 agences, 300 employés, 60 véhicules voyageurs dont 15 partenaires, 5 véhicules courrier) après import contrôlé; aucune fausse preuve si jeu non chargé.

## Livrable attendu de Claude

- `AUDIT_ANALYTIQUE.md` : carte de l'existant et fichiers/références précis.
- `ARCHITECTURE_ANALYTIQUE.md` : modèle, flux, migrations et règles comptables.
- `MATRICE_ETATS_PLAN.xlsx` ou CSV : 10 plans × états, statuts réalisé/partiel/absent, tests.
- `RESULTATS_TESTS.md` : commandes exécutées, résultats, tests non exécutés et causes.
- `ECARTS_A_CORRIGER.md` : écritures sans plan, écart GL, affectations incertaines, droits et sync.
- Archive complète `RETOUR_CLAUDE_CODE_ERP_TRANSPORT.zip`, **sans** `.env`, mots de passe, clés privées, tokens, `.venv`, bases de production ni informations personnelles non anonymisées. Ne pas faire remonter les données réelles non autorisées.

L'utilisateur veut pouvoir transmettre ce retour à ChatGPT pour une nouvelle lecture croisée. Différencier clairement « fait et testé » de « spécifié seulement ».
