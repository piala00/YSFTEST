---
name: erp-ohada-agences-hors-ligne-rapport-stock
description: "Concevoir et développer avec Claude un ERP OHADA configurable pour petites, moyennes et grandes entreprises, utilisable hors ligne avec agences autonomes, synchronisation et reporting global. Utiliser pour le paramétrage société, gros et détail, conditionnements, rapport commercial journalier, encaissements hors-recettes, liaisons interagences, commandes payées avant livraison et fiche de stock magasin avec quantités saisies sans voir l’attendu."
---

# ERP OHADA : agences autonomes, rapport commercial et stock magasin

## Prendre connaissance du besoin

Lire [CONTEXTE_UTILISATEUR.md](references/CONTEXTE_UTILISATEUR.md), puis [EXIGENCES.csv](references/EXIGENCES.csv). Traiter les deux tâches comme un ensemble :

1. Configurer une plateforme pour plusieurs sociétés distinctes et, dans chaque société concernée, plusieurs agences autonomes hors ligne ; gérer gros, détail et conditionnements.
2. Automatiser le rapport commercial, les opérations pour compte d’autres agences, les commandes/avances/livraisons/factures et le contrôle indépendant des sorties au magasin.
3. Intégrer le complément U4 sur clients à crédit, plafond, échéance, rattachement obligatoire du reçu à une facture et auteur visible sur tous documents et opérations.

Distinguer toujours plusieurs sociétés clientes du logiciel et plusieurs agences d’une seule société. Dans le cas métier décrit, les agences sont autonomes localement mais appartiennent à une même société. Ne pas les convertir en sociétés juridiquement indépendantes.

## Respecter la provenance

- **CONFIRME_UTILISATEUR** : exigence explicitement formulée dans les échanges U1 à U4 ; la préserver dans toute conception.
- **PROPOSITION_CONCEPTION** : réponse architecturale ou contrôle proposé ; la présenter comme tel et l’adapter au code existant sans affaiblir le besoin.
- **A_PRECISER** : choix dont le détail n’est pas tranché ; consulter [DECISIONS_OUVERTES.csv](references/DECISIONS_OUVERTES.csv), avancer sur les parties indépendantes et poser uniquement les questions bloquantes.

Ne pas prétendre que ce dossier démontre un comportement Sage, une conformité fiscale acquise ou une fonctionnalité déjà implémentée. Il s’agit d’un cahier métier issu de l’utilisateur, complété par des propositions. Ne pas ajouter de comptes français ou de numéros de comptes de liaison non validés pour le dossier OHADA. Ne pas inclure d’identifiants de connexion dans les livrables.

## Collaborer avec le travail de Claude

Lire [COLLABORATION_CLAUDE.md](references/COLLABORATION_CLAUDE.md) avant de développer. Inspecter les instructions du dépôt et les modules déjà présents. Construire une correspondance exigence → code existant → écart → changement → preuve. Compléter l’existant ; conserver menus, options, calculs et historiques utiles. Ne pas réimplémenter une fonction sans vérifier son existence. Le Skill est le dossier de transmission ; ne pas prétendre disposer d’une conversation directe entre assistants.

## Appliquer les règles essentielles

1. Maintenir le fonctionnement local de chaque agence sans serveur central joignable. Ne pas assimiler une page web en cache à un ERP local autonome.
2. Rattacher chaque opération à sa société, son agence d’exécution et, si différente, son agence bénéficiaire. Contrôler ces périmètres côté serveur.
3. Séparer vente, encaissement, livraison et facturation. Conserver les liens BC → BL → facture et règlement → commande/facture. Ne jamais compter la commande puis sa facture comme deux ventes.
4. Inclure le hors-recettes dans la caisse qui a réellement reçu les espèces ; exclure cet encaissement des ventes propres de cette agence. Affecter une seule fois le règlement au client bénéficiaire via un rapprochement de liaison traçable.
5. Conserver les quatre parties exigées du rapport : ventes, encaissements, sorties/dépenses, solde de caisse. Ajouter les sous-rubriques nécessaires sans remplacer ces parties.
6. Charger les articles du BL pour le fichiste sans transmettre les quantités attendues à son interface. Enregistrer sa déclaration avant comparaison. Conserver une révision et un historique de correction.
7. Comparer registre de gestion et registre indépendant du magasin. Ne pas créer une deuxième sortie du stock de gestion à la validation du fichiste. Ne pas assimiler concordance des BL et comptage physique.
8. Synchroniser avec identifiants stables, reprises et intégration sans doublons. Afficher les dates de fraîcheur. Ne pas fusionner les données financières par simple règle « dernière modification gagnante ».
9. Conserver les conversions et unités utilisées sur chaque pièce. Ne pas convertir automatiquement kg et litres, ni changer rétroactivement les conditionnements historiques.
10. Exiger une facture cible pour valider un reçu de règlement de créance. Conserver l’avance sur commande comme circuit distinct avant facturation ; ne pas inventer de facture. Par défaut, un reçu de créance cible une facture ; ne pas activer le multi-factures sans arbitrage.
11. Afficher l’auteur d’origine et les informations de création sur chaque document/écriture/opération. Conserver séparément les auteurs des modifications, validations, annulations et synchronisations ; ne pas remplacer l’auteur d’origine par l’utilisateur qui importe les données.

Les contrôles techniques ci-dessus sont des propositions de conception destinées à rendre les exigences fiables ; ils ne prouvent pas un choix préalable de technologie.

## Lire les références du sujet traité

- [PARAMETRAGE_ET_HORS_LIGNE.md](references/PARAMETRAGE_ET_HORS_LIGNE.md) : sociétés, agences, unités, prix, droits, fonctionnement local et synchronisation.
- [RAPPORT_COMMERCIAL_ET_LIAISONS.md](references/RAPPORT_COMMERCIAL_ET_LIAISONS.md) : structure du rapport, formules, hors-recettes, dépenses pour autrui, commandes et cas chiffrés.
- [FICHE_STOCK_ET_RAPPROCHEMENT.md](references/FICHE_STOCK_ET_RAPPROCHEMENT.md) : rôle du fichiste, saisie sans attendu, registre indépendant, écarts et inventaire physique.
- [REGLEMENTS_CREDIT_ET_TRACABILITE.md](references/REGLEMENTS_CREDIT_ET_TRACABILITE.md) : reçu lié à une facture, plafond, échéance et identité des auteurs sur tous les documents et opérations.
- [MODELE_CONCEPTUEL.csv](references/MODELE_CONCEPTUEL.csv) : données et contraintes proposées ; ne pas imposer ces noms aux tables existantes.
- [RECETTE_METIER.csv](references/RECETTE_METIER.csv) : scénarios de réception et résultats attendus ; tous sont proposés, non exécutés dans l’ERP.
- [DECISIONS_OUVERTES.csv](references/DECISIONS_OUVERTES.csv) : ambiguïtés, choix techniques et arbitrages à conserver visibles.
- [SOURCES_ET_STATUT.md](references/SOURCES_ET_STATUT.md) : provenance et limites de la livraison.

## Livrer une modification vérifiable

Indiquer les exigences couvertes, les écrans et calculs modifiés, les migrations et les tests exécutés. Relier chaque résultat aux pièces sources. Vérifier en priorité paiements interagences, avances, livraisons partielles, absence de double sortie et reprise après interruption réseau. Ne pas annoncer « temps réel global » quand une agence est déconnectée, ni « livré » pour un scénario uniquement décrit. Livrer les changements par périmètre cohérent et conserver les décisions non tranchées.
