# Provenance et statut

Date de constitution : 24 octobre 2026. Auteur du besoin : utilisateur de la conversation ; destinataire opérationnel : Claude, qui a reçu les deux mêmes tâches.

U1 : message exposant plusieurs sociétés, utilisation en ligne/hors ligne, agences, reporting par agence/global, grandes/PME/petites structures, gros/détail et conditionnements dès le paramétrage puis après démarrage.

U2 : message précisant une seule société et agences autonomes Sage sur serveurs locaux, rapport commercial en quatre parties, versements hors-recettes, comptes de liaison, sorties pour autrui, commandes/avances/livraisons/factures et module de fichiste avec quantités attendues invisibles.

U3 : demande de création d’un Skill pour Claude puis précision de collaboration sur les deux mêmes tâches. Les formulations des exigences sont des restitutions structurées, pas des citations verbatim complètes.

U4 : complément sur clients comptant et crédit, compte client, plafond accordé, délai par facture, reçu obligatoirement rattaché à une facture et auteur identifiable/visible sur tous documents, écritures et opérations. Ce complément fait partie de cette livraison, pas d’une étape reportée.

A1–A2 : réponses de conception proposées par l’assistant dans le même fil, complétées ici par des invariants et cas limites nécessaires à une implémentation vérifiable. Ces propositions n’ont pas toutes été explicitement arbitrées par l’utilisateur. Elles sont marquées PROPOSITION_CONCEPTION ; les choix non tranchés sont dans DECISIONS_OUVERTES.csv.

Ce dossier ne prétend pas documenter l’interface native Sage, ni certifier des écritures ou obligations fiscales. Les recherches Sage/OHADA antérieures restent des références distinctes ; elles ne prouvent pas que ces nouvelles fonctions existent dans l’ERP. Aucun accès au code de Claude ni exécution des scénarios métier de ce dossier dans l’ERP n’a été effectué pour cette livraison.

Le Skill fournit un cahier de transmission et des scénarios de recette proposés. Les validations de format du paquet ne constituent pas une validation fonctionnelle du logiciel. Aucun mot de passe, identifiant secret ou donnée client réelle n’est nécessaire dans le paquet.

U5 (prioritaire pour le parcours règlement) : observation utilisateur de la facture qui disparaît lors de l’ouverture du règlement ; exigence de fenêtres indépendantes et navigables ; menu de saisie, client d’abord, factures non soldées proposées automatiquement, sélection d’une ou plusieurs factures et règlement en attente si aucune facture n’est disponible. En-tête ERP différent annoncé ; feuille non encore reçue.

Version 2 du cahier : U4 reste une provenance historique pour la règle ancienne ; U5 remplace son caractère obligatoire/unique du rattachement et les tests associés. Cette mise à jour du Skill ne corrige pas le code et ne revalide pas la version du site de test. Les anomalies historiques de la revue précédente restent à traiter selon leur portée ; les attentes sur le refus sans facture doivent être remplacées par celles de U5.


U6 : deux captures utilisateur jointes sous assets/captures ; relevé visuel, sources complémentaires et limites dans FONCTIONNEMENT_FENETRES_U6.md. Version de transmission 3 : documentation complétée, aucun code applicatif modifié et aucune recette interactive Sage/ERP exécutée dans cette mise à jour.


U7 — Reprise complète Sage demandée. Version de transmission 4 : cahier de migration et sources officielles ajoutés ; aucun importeur complet développé ni migration exécutée.


Clarification U7 intégrée avant livraison v4 : synchronisation initiale puis incrémentale et bascule autonome ; architecture proposée, aucun connecteur intégral ni synchronisation réelle exécutés.
