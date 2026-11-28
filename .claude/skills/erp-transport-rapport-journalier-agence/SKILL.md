---
name: erp-transport-rapport-journalier-agence
description: Auditer, concevoir et implémenter les rapports journaliers d'agence en tableaux simples (billetterie par véhicule et trajet, bagages payants, expéditions distinctes, sorties, rapprochement caisse et reversement), PDF/impression, sécurité et synchronisation offline-first dans l'ERP Transport Afrique Centrale. Utiliser lorsqu'on demande un rapport de journée, une édition de caisse agence ou un état journalier facile à lire.
---

# Rapport journalier d'agence — Skill de mise à jour Claude Code

## Besoin utilisateur confirmé

Chaque agence doit éditer **un seul rapport journalier simple à lire, composé de tableaux** (sans graphiques, widgets ni surcharge visuelle), affichant :

1. **En-tête** : compagnie, agence, date, numéro/édition, responsable, état de clôture et état de synchronisation.
2. **Tableau 1 : voyageurs / billetterie** — nom du véhicule, code du véhicule, trajet, nombre de places vendues/occupées, prix unitaire, montant total et sous-total. Chaque départ de l'agence doit y figurer, y compris plusieurs rotations du même véhicule. Décomposer par tarif si un départ contient plusieurs prix.
3. **Tableau 2 : bagages payants des voyageurs** — véhicule, désignation des bagages (excédent de franchise), destination, quantité, montant et total. Chaque bagage est rattaché au voyage et, si applicable, au billet.
4. **Tableau 3 facultatif et distinct : expéditions de colis** — lorsqu'il existe des recettes messagerie encaissées dans l'agence ; ne jamais confondre « bagages voyageurs » et « colis expédiés ».
5. **Tableau 4 : sorties** — toutes les sorties de trésorerie *réellement payées* dans l'agence ce jour, avec libellé, montant, pièce, bénéficiaire/motif et affectation véhicule/agence. Les dépenses dues mais non payées sont dans un état de suivi séparé, pas retirées à la caisse.
6. **Tableau 5 : rapprochement et solde** — recettes réellement encaissées selon leur date et moyen de paiement, solde ouverture, sorties payées, fonds reversés, reste en caisse, écarts, justificatifs et signatures.

**Règle UX :** le rapport quotidien standard n'affiche que des tableaux linéaires sur fond blanc, bordures fines, libellés clairs, sous-totaux en gras. Pas de graphique, KPI visuel, cartes, diagramme ou tableau analytique compliqué. L'impression doit être lisible même en noir et blanc.

## Obligations de justesse — ne pas confondre recettes et caisse

- Les lignes du **tableau voyageurs** décrivent les **départs du jour dans l'agence** (date/heure réelles de départ, identifiant unique du voyage). Les billets peuvent avoir été payés la veille ou dans une autre agence. Donc le total « valeur des billets transportés aujourd'hui » **ne doit pas être automatiquement considéré comme l'encaissement du jour de cette agence**.
- Le **tableau de caisse** regroupe **uniquement les véritables encaissements effectués dans cette agence à la date de caisse** (billets pour voyages futurs ou passés si paiement tardif, bagages, expéditions, régularisations), distingués des paiements par carte, banque et Mobile Money. Ne pas additionner les deux vues comme s'il s'agissait de recettes différentes.
- Billet **annulé, remboursé, réémis, impayé**, bagage remis, colis annulé : représenter seulement l'effet réellement approuvé selon le journal d'événements et l'état de la période ; corriger par ajustements traçables.
- Recettes billetterie **CLASSIQUE et VIP** avec **véhicules dédiés différents** ; une ligne de vente mentionne la gamme applicable au voyage, sans mélanger les deux flottes.
- Les sorties enregistrées par garage/RH/achats ne deviennent **sorties caisse** qu'après décaissement effectif autorisé et attribué à une caisse / agence. La charge analytique peut être reconnue à une date différente du paiement.
- La remise physique ne porte que sur les **espèces** effectivement à reverser ; les paiements électroniques sont affichés à part, selon leur destination et statut de rapprochement. Si le siège demande une « recette nette reversée », calculer et afficher clairement **total net tous moyens** et **espèces physiquement reversées**, sans les confondre.
- Solde caisse espèces = solde d'ouverture espèces + encaissements espèces - sorties espèces - remboursements espèces - remises/transferts espèces. Écart = espèces comptées - solde théorique. Une pièce financière ne peut apparaître qu'une fois dans les agrégats correspondant à son effet.
- Agence de vente / d'encaissement et agence d'exploitation sont deux attributions distinctes, tout comme date de départ et date d'encaissement.

## Documents à lire

1. [Modèle de rapport et maquette imprimable](references/01-maquette-rapport-tables.md)
2. [Origine des montants, règles et calculs](references/02-regles-metier-calculs.md)
3. [Modèle de données, API, requêtes et performances](references/03-donnees-api.md)
4. [Droits, clôture, synchronisation et impression](references/04-cloture-offline-ux.md)
5. [Plan de développement et tests d'acceptation](references/05-tests-acceptation.md)
6. [Maquette HTML autonome en tableaux](examples/rapport_journalier_agence_exemple.html)

## Exécution attendue dans le dépôt existant

1. **Auditer d'abord** routes, tables, caisses, ventes de billets, départs, bagages, messagerie, dépenses, rapprochements, droits, composant de rapport et états de synchronisation. Ne rien écraser ni supprimer.
2. Montrer la matrice : champ du rapport → service source → pièce justificative → critère date/agence → règle d'agrégation → état de validation. Vérifier les champs absents.
3. Implémenter le **rapport simple**, avec une vue écran tabulaire, une vue imprimable A4 paysage/portrait adapté, export PDF et CSV/XLSX si outillage disponible. Un seul bouton simple d'impression et un filtre agence/date pour l'utilisateur autorisé. Éviter les surcharges d'interface.
4. Rapprocher les valeurs d'exploitation des **mouvements réels de caisse**. Si les sommes diffèrent, afficher les deux chiffres et un rapprochement explicable, plutôt que de forcer l'égalité.
5. Préserver les dimensions analytiques `agency_id (encaissement/exploitation)`, `trip_id`, `vehicle_id`, `service_class`, `partner_id` historique si applicable, `cashbox_id`, `payment_method`, `source_event_id`.
6. Gérer les états de synchronisation **complet / provisoire / incomplet**. Un rapport imprimé hors ligne doit porter sa date de génération et son statut. Rejets ou retards de sync ne doivent pas doubler les lignes après reconnexion.
7. Tester avec des cas réels du dépôt, y compris anciens paiements, ventes dans autre agence, sorties non payées, encaissé Mobile Money, plusieurs départs, correction de clôture, erreurs de droits.
8. Livrer le détail des fichiers réellement modifiés, migrations, tests exécutés et limites. Le Skill est un cahier de réalisation, **pas une preuve d'implémentation**.

## Coexistence avec les autres skills

Complète `/erp-transport-afrique-centrale` et `/erp-transport-plan-analytique`. Les rapports analytiques approfondis, états légaux et états détaillés partenaires restent disponibles dans leurs modules respectifs. Le **rapport journalier d'agence** doit toutefois rester simple, imprimable, centré sur les recettes/dépenses et la situation de caisse.

## Commande à exécuter dans Claude Code

« Applique `/erp-transport-rapport-journalier-agence` à mon dépôt ERP Transport existant. Commence par auditer mes données et rapports, puis développe le rapport journalier imprimable en tableaux simples : billetterie par véhicule/trajet, bagages payants, expéditions de colis distinctes si présentes, sorties et état de caisse avec net à reverser. Ne confonds pas les départs du jour avec les encaissements du jour. Préserve le plan analytique, le fonctionnement hors ligne et les droits. Fais les tests et ne supprime aucune fonctionnalité. »

## Mise à jour des caisses (règle validée)

L'agence peut avoir **une caisse partagée** ou **plusieurs caisses spécialisées**. Il faut conserver les tableaux d'exploitation demandés et ajouter un récapitulatif de **chaque caisse active** lorsqu'il y en a plusieurs, suivi d'un total agence. Pour une caisse unique, maintenir la présentation compacte. Une sortie garage peut être payée depuis la caisse centrale ; les transferts internes apparaissent sans augmenter les recettes. Détails : `/erp-transport-caisses-multi-agences`.

