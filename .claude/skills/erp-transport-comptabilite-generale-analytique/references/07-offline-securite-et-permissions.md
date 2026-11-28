# 07 — Synchronisation, sécurité, séparation des fonctions

## Offline-first

- L'opération source est enregistrée localement avec un UUID stable et outbox transactionnelle ; l'agent ne déclenche pas une seconde écriture en "réessayant" la synchro.
- Événements et écritures provisoires sont marqués par `origin_agency_id`, `source_event_id`, `effective_at`, `created_at`, `sync_status`.
- Le siège intègre via consommation idempotente, registre des événements traités et contraintes d'unicité ; états "partiellement synchronisés" en attendant les agences.
- La direction voit la dernière synchro de chaque agence, la couverture de la période et le nombre de pièces en attente ou rejetées.
- Interdire `last_write_wins` sur montants, contrat propriétaire, affectation véhicule, pièces comptables et clôtures. Les conflits passent par workflow d'anomalie et justificatif.
- Si une caisse est clôturée localement mais le siège non synchronisé, afficher statut de clôture locale et non état central définitif.

## Permissions

| Profil | Générale | Analytique véhicules | Analytique propriétaires | Règlement partenaire |
|---|---|---|---|---|
| Direction autorisée | Vue globale | Toutes données dans périmètre | Tous propriétaires du périmètre | Approbation selon rôle |
| Comptable général | Saisie/validation selon droits | Consultation/contrôle | Consultation + rapprochement | Saisie et validation séparées |
| Contrôleur analytique | Consultation ciblée | Détails/calculs | Détails/calculs | Prépare mais ne paye pas |
| Chef d'agence | Rapports de son agence | Véhicules/voyages dans périmètre | Restreint au besoin | Pas de paiement hors autorisation |
| Guichetier | Uniquement ses ventes/caisse autorisées | Aucun compte global | Aucun | Aucun |
| Garage | Bons, consommations autorisées | Véhicules de son périmètre | Aucun | Aucun |
| Partenaire | Aucun journal global | Ses véhicules/périodes contractuelles | Son compte uniquement | Lecture de ses règlements |

Les autorisations se vérifient **dans les APIs et les requêtes** (tenant, agences, owner_id, validité temporelle), pas seulement en masquant les boutons. Journaliser export de relevé et consultation des données sensibles. Empêcher un propriétaire d'ouvrir l'URL du relevé d'un autre.

## Clôtures

Journée caisse, jour exploitation, clôture voyage, période comptable et décompte partenaire = objets distincts, ordonnancés avec contraintes et permissions. Le décompte ne doit pas être irrévocablement validé lorsque les recettes/coûts requis n'ont pas été synchronisés, sauf procédure d'estimation et d'ajustement approuvée et traçable.
