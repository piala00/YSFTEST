# 04 — Clôture, synchronisation Offline-First, autorisations et UX

## Statuts du document

- **Brouillon / provisoire** : l'agence n'a pas encore clôturé toutes les caisses et les services essentiels ; chiffres susceptibles d'évoluer.
- **Clôturé localement** : caisses et services pertinents validés par rôles autorisés ; produire version immuable signée/hashée si déjà dans le projet.
- **En attente de synchronisation** : document local validé mais non reçu au siège. Il est imprimable avec statut et horodatage explicites.
- **Centralisé** : siège a reçu et intégré tous les événements de la période/du périmètre.
- **Rectificatif** : correction post-clôture avec numéro version, motifs, auteurs, pièces et rapprochement. Ne pas écraser l'édition initiale.

## Autorisations

- Guichetier : consulter uniquement les billets et sa propre caisse, pas les dépenses privées d'autres services sans permission.
- Agent bagages/messagerie : produire les pièces et sa caisse.
- Chef d'agence : voir le rapport consolidé de son agence, demander clôture, signer, selon habilitation ; pas les autres agences.
- Comptable / Direction : rapport des agences autorisées, contrôle des écarts, traçabilité, centralisation.
- Administrateur technique : pas de droit implicite pour approuver ou modifier des montants.

## UX et impression

- Dans menu `Rapports > Rapport journalier d'agence`, une seule page avec sélecteurs `Agence` (si plusieurs autorisées), `Date`, et boutons `Afficher`, `Imprimer`, `Exporter PDF` si disponibles.
- **Aucun graphique, aucun camembert, aucun graphique de tendance, aucune carte KPI, aucun onglet superflu sur ce rapport**. Les autres analyses conservent leur espace dans l'ERP.
- Tables fixes, fond blanc, texte noir, entête clair, montants à droite, totaux en gras, signatures en bas. Support A4 paysage si tableau A large ; options de répétition de l'en-tête imprimé.
- Valeur manquante : `—`; aucun mouvement : `Aucune opération`; chargement incomplet : bandeau texte `Rapport provisoire — données en attente de synchronisation` plutôt qu'une fausse valeur 0.
- Le PDF et l'impression doivent conserver les mêmes données que l'écran (numéro et version du rapport, total et date de génération).

## Synchronisation

- Le serveur local génère le rapport depuis ses propres écritures validées, même hors Internet, avec la date de la dernière synchro.
- Le siège ne marque pas « complet » tant que les agences/caisse/services attendus n'ont pas terminé la transmission ; ne pas additionner silencieusement les chiffres incomplets.
- Le transfert répété d'une clôture ne crée ni nouvelle vente ni nouvelle dépense. Déduplication par identifiants et version/état.
- Les ventes liées à un voyage d'autre agence sont visibles selon leurs rôles économiques, mais le paiement appartient à sa caisse d'origine ; deux rapports d'agence ne peuvent compter deux fois un même encaissement dans les recettes centralisées.
