# Audit des écarts — skills « simulation complète » et « partenaires propriétaires »

Projet : ERP OHADA (Django 6.1, Python 3.13, SQLite / PostgreSQL / SQL Server), dépôt `YSFTEST`, branche
`ccr-5592a371-fusjt2`. États : **EXISTANT** (codé et testé), **PARTIEL**, **ABSENT**, **BLOQUANT**.

## 1. Rapport journalier RJ-AG-20261026 (anomalies relevées à la revue)

| Anomalie | État | Correctif (fichier) | Test |
|---|---|---|---|
| AN-RJ-001 caisse espèces −162 000 | EXISTANT (corrigé) | Bloquant de clôture et bandeau sur le rapport ; transfert refusé au-delà des espèces (`apps/transport/models_caisse.py`) | `AnomaliesRapportJournalierTests` |
| AN-RJ-002 départs futurs comptés à 00:05 | EXISTANT (corrigé) | Départ refusé avant son jour et trop tôt avant son heure (tolérance réglable) ; heure réelle de départ imprimée (`Depart.partir`) | idem |
| AN-RJ-003 730 000 = 730 000 sans rapprochement | EXISTANT (corrigé) | Tableau « billets transportés : payés ce jour / un jour précédent / par une autre agence » | idem |
| AN-RJ-004 courriers sans car | EXISTANT (corrigé) | Colonne « Car » (ou « pas encore chargé ») ; la recette d'un colis va au car au départ (déjà en place) | idem |
| AN-RJ-005 bagages non saisis | EXISTANT (corrigé) | Bagages payants à la vente du billet, tableau 2 | `BagagesTests` |
| AN-RJ-006 Mobile Money sur 551 | EXISTANT (corrigé) | Nouveaux dossiers : 552 = téléphone portable, 551 = carte carburant ; dossiers existants inchangés | tests comptabilité |
| Données de l'exemple RJ | — | Les chiffres du PDF venaient d'un jeu d'essai (transfert de 500 000 sans fonds) : le logiciel le refuse maintenant | — |

## 2. Exigences de la simulation

| Exigence | État | Preuve dans le code | Écart / suite |
|---|---|---|---|
| Agences multiples, chacune hors ligne, siège consolidant | EXISTANT | `apps/echanges` (lots signés, idempotence, relais, liaisons 185) ; scénario 4 bases | Essai à 8 agences non lancé (même mécanisme) |
| 300 salariés, paie mensuelle, OD de paie, règlement | EXISTANT | `apps/personnel` (rubriques sans taux imposé, bulletins, validation, paiement) | Pas de double validation RH → finance ; pas de présences/congés |
| Équipage rattaché au véhicule, ventilation | EXISTANT | `Employe.ventilation` (habituel, voyages, jours, agence) | — |
| 60 bus Classique/VIP exclusifs, historique | EXISTANT | `Vehicule.gamme`, `ChangementGamme`, contrôle au départ | — |
| 5 véhicules de fret courrier | PARTIEL | Type de véhicule CAMION ; colis chargés sur un départ | Pas de « tournée courrier » distincte d'une ligne voyageurs |
| 15 bus partenaires, contrats datés | EXISTANT | `apps/partenaires` | — |
| Billets : siège unique, agence vendeuse ≠ exploitante | EXISTANT | sièges par tronçon, `select_for_update`, `site_origine` | Quotas de sièges inter-agences : ABSENT |
| QR anti-réutilisation | ABSENT (choix) | Embarquement sur liste choisi par l'utilisateur | — |
| Colis : bordereau, car transporteur, statut | EXISTANT | `Colis` | — |
| Achats : demande → devis → BC → réception → facture | PARTIEL | Gestion commerciale : demande d'achat, commande, réception, facture fournisseur, avoirs, règlements | Pas de comparatif de devis fournisseurs ni de rapprochement 3 pièces bloquant |
| Stock = actif, consommation = charge | EXISTANT (garage) | Magasin du garage : achat pour le stock D 33x (pièces 338, bureau 334, emballages 335, consommables 331), sortie D charge / C stock au CMUP (`models_magasin.sortir`, `MagasinTests`) | La gestion commerciale (négoce) reste en inventaire intermittent |
| Pièce garage sortie du stock sur ordre de réparation | EXISTANT | Ligne « pièce du magasin » de l'ordre de réparation, sortie au CMUP à la clôture, charge sur le véhicule | — |
| Achat décidé « pour le stock » ou « pour un véhicule » | EXISTANT | Destination de chaque ligne d'achat : STOCK, VÉHICULE (charge directe sur le véhicule), IMMOBILISATION (classe 2) | — |
| Immobilisation d'un matériel durable | PARTIEL | Ligne d'achat « immobilisation » (D 244 par défaut, compte modifiable) | Pas de fichier des immobilisations ni d'amortissements automatiques |
| Transfert inter-dépôts neutre | EXISTANT | `STOCK_VIREMENT` | — |
| GA source unique, analytique sourcée | EXISTANT | Le véhicule est une colonne de la ligne d'écriture générale (aucune ventilation orpheline possible) | Répartition 60/40 d'une ligne sur plusieurs véhicules : ABSENT |
| Non affecté visible | EXISTANT | Rapprochement affecté / non affecté (Comptabilité analytique › Véhicules) | — |
| Reporting comparatif | EXISTANT | Reporting › Transport : comparaisons | Semaines, N/N−1 automatiques : PARTIEL (périodes libres) |
| Caisse unique / multiple | EXISTANT | Situation par caisse ; sessions par guichetier | Paramétrage « caisse commune » par agence : PARTIEL |
| Droits : guichetier sans paie, partenaire A sans B | PARTIEL | Droits par logiciel et par menu | Périmètre par agence (ABAC) et portail partenaire : ABSENT |
| Rejouer dix fois un lot | EXISTANT | Import idempotent, testé | — |
| Rapport provisoire / clôturé daté | EXISTANT | En-tête RJ (état, synchronisation, généré le) | — |

## 3. Exigences « partenaires propriétaires »

| Exigence | État | Preuve | Écart |
|---|---|---|---|
| Rôle propriétaire ≠ fournisseur, sous-comptes distincts | EXISTANT | Compte propriétaires 467 (paramétrable) distinct du 401, sans compensation | Fiche « identité unique » avec onglets par rôle : PARTIEL (même fiche tiers) |
| Contrats versionnés (fixe, variable, fixe + variable, avance, location) | EXISTANT | `ContratPartenaire` (avenants datés) | Clauses de suspension du fixe (sinistre) : à décrire |
| Fixe et variable en écritures distinctes | EXISTANT | `Decompte.approuver` : deux écritures | — |
| Avance imputée sur le variable, sans double charge | EXISTANT | Règlement « avance » D 467 / C caisse | Test exemple B |
| Compte du camion consultable, retrait si positif, compensation si négatif | EXISTANT | Relevé : compte en cours depuis le dernier arrêté, bouton « Arrêter le compte à aujourd'hui » (`CompteDuCamionTests`) | — |
| Retraits autorisés, contrôle du disponible | EXISTANT | `DemandeRetrait` | Autorisation par le siège via les échanges : PARTIEL (autorisation locale par une autre personne) |
| « Salaire du propriétaire » hors paie | EXISTANT | Le propriétaire n'est pas un employé ; aucun lien avec la paie | — |
| Relevé par nature avec écriture GL | EXISTANT | Relevé (FIXE, VARIABLE, AVANCE, RETRAIT, RÈGLEMENT) | — |
| Exemples A et B du skill | EXISTANT | `RemunerationsProprietairesTests` (330 000 / 270 000 / 80 000 ; 240 000 / 90 000) | — |

## 4. Points BLOQUANTS pour une mise en production

1. Plan comptable de la société non fourni : tous les comptes proposés restent à valider (liste dans `MAPPING_JOURNAUX_ET_ANALYTIQUE.md`).
2. Méthode de stock : inventaire permanent retenu pour le magasin du garage ; comptes de stock proposés à valider.
3. Barèmes sociaux et fiscaux de paie : à saisir par l'expert-comptable (aucun taux n'est imposé par le logiciel).
