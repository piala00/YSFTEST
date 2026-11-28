# Benchmark ERP & feuille de route — viser le sommet du transport interurbain

Demandé par le propriétaire (2026-11-04) : situer notre ERP face aux meilleurs du marché
(généralistes et spécialisés transport), module par module, et dégager ce qui nous ferait passer
au niveau mondial pour le transport de voyageurs + messagerie (colis) multi-agences en Afrique
centrale (OHADA). Les affirmations issues de pages éditeurs sont du déclaratif marketing, pas une
vérité indépendante — à confirmer avant toute décision structurante.

## 1. Paysage du marché (repères)

- **ERP généralistes** : SAP S/4HANA, Oracle NetSuite, Microsoft Dynamics 365, Odoo, Sage X3.
  Pas de « meilleur » absolu : le bon ERP dépend de la taille, du secteur et du budget. Odoo est le
  repère « modulaire / coût maîtrisé » le plus proche de notre philosophie (modules activables).
- **TMS (gestion de transport/logistique)** : Trimble, Aptean, etc. Cœur de fonctions : suivi temps
  réel, optimisation de tournées, gestion transporteurs, planification des charges, facturation
  automatique, télématique, analytique. Tendances 2025 : planification par IA, ETA prédictifs,
  alertes de perturbation.
- **Gestion de flotte** : Geotab, Fleetio, Samsara. Cœur : GPS/tracking, carburant (coût au km,
  ralenti, cartes carburant), maintenance préventive, comportement conducteur, rapports de coûts.
- **Billetterie bus interurbain** : Betterez / Ratality (rachetés par Busbud), Zaui, Distribusion,
  et de nombreux éditeurs. Cœur : réservation en ligne + plan de salle, canaux agents/revendeurs,
  applis passager/conducteur, module colis séparé (enlèvement → suivi → livraison), passerelles de
  paiement, portail opérateur multi-dépôts.

Sources : voir §6.

## 2. Ce que NOUS avons déjà (nos forces — souvent absentes des généralistes pour ce métier)

- **Billetterie** (classes Classique/VIP, embarquement sur liste, remboursement, arrêts, bagages payants).
- **Colis / messagerie** inter-agences, recette attribuée au véhicule transporteur.
- **Exploitation** : voyages, clôture de voyage, km, convoyeur, papiers, avances de mission, imprévus.
- **Garage** (carburant, ordres de réparation) + **Magasin** (achats stock/véhicule/immobilisation, pièces).
- **Caisses multi-agences** (sessions, clôtures, reversements), **Mobile Money**.
- **Personnel & paie**, **Propriétaires de véhicules** (rémunération fixe/variable, avances, retraits, compte du camion).
- **Comptabilité OHADA 7 chiffres** : générale + **analytique 10 plans**, **source unique** (toute
  écriture analytique naît d'une écriture générale validée), budgets, reports à nouveau, clôtures.
- **Reporting** multidimensionnel (agence, véhicule, propriétaire, ligne, gamme…) avec graphiques.
- **Offline-first multi-agences** : chaque agence autonome, synchronisation direction ↔ agences par
  boîte aux lettres chiffrée. **C'est un différenciateur fort** : la plupart des ERP mondiaux
  supposent une connexion permanente, inadaptée au terrain africain.
- **Simulation** reproductible (données fictives), **licences/essai**, packaging Windows + service.

→ Pour notre niche, nous couvrons déjà plus que la plupart des suites généralistes. L'écart au
« sommet mondial » n'est pas sur la profondeur métier, mais sur **la distribution (vente en ligne),
la mobilité (applis), la télématique (GPS) et l'expérience/BI décisionnelle**.

## 3. Écarts / opportunités pour atteindre le sommet

### A. Distribution & expérience client (le plus gros levier commercial)
- **Réservation en ligne + plan de salle** (choix du siège) : portail public + canal agents/revendeurs.
- **E-billet / QR** et **embarquement par scan** (nous avons l'embarquement sur liste ; ajouter le QR).
- **Notifications SMS / WhatsApp** (confirmation, départ, retard) — essentiel en Afrique.
- **Suivi public du colis** (page de suivi par numéro, preuve de livraison, QR/code-barres).
- **Programme de fidélité**, **tarification dynamique** (remplissage, anticipation).
- **Applis mobiles** : passager (achat/suivi), conducteur (manifeste, embarquement), agent (POS hors ligne).

### B. Flotte & exploitation (le plus gros levier d'économies)
- **Intégration GPS/télématique** (position, ralenti, vitesse, géofencing) — via API d'un boîtier.
- **Optimisation des tournées / affectation** véhicules-lignes, ETA prédictifs.
- **Maintenance préventive** (par km/date, alertes) au-delà des ordres de réparation actuels.
- **Carburant** : cartes carburant, **coût au km par véhicule** (tableau de bord dédié), détection d'anomalies.
- **Comportement conducteur** (sécurité, lien consommation).

### C. Finance & conformité
- **Facture électronique / normée DGI Cameroun** (mentions, transmission) — à valider par l'expert-comptable.
- **BI / tableaux de bord décisionnels** (au-delà des états : KPIs temps réel, par agence/véhicule/ligne).

### D. Plateforme & intégration
- **API ouverte** (REST) pour s'interfacer (paiement, SMS, GPS, partenaires).
- **Multi-sociétés / multi-exercices** (en cours — voir REFONTE_MENUS_ET_MULTI_SOCIETES.md).
- **Journalisation/audit** (déjà présent) ; **sauvegarde par exercice** (en cours).

### E. IA / 2025 (différenciation)
- **Prévision de demande** (remplissage par ligne/jour) à partir de l'historique + de la simulation.
- **Détection d'anomalies** (caisse, carburant, recettes) — nous avons déjà le socle comptable fiable.
- **ETA prédictifs** une fois le GPS branché.

## 4. Nos différenciateurs à défendre (ne pas les perdre en copiant les autres)
1. **Offline-first multi-agences** fiable (terrain africain) — rare et décisif.
2. **Comptabilité OHADA source-unique** (traçabilité argent, pas de « dernière écriture gagne »).
3. **Véhicule et propriétaire comme comptes** (rentabilité par camion, partenaires) — très spécifique transport.
4. **Caisses par agence** avec reversements et rapport journalier simple.
5. **Un seul logiciel intégré** (billetterie + colis + compta + flotte + paie) vs suites séparées.

## 5. Feuille de route priorisée (après la refonte menus/multi-sociétés en cours)

**P0 — socle en cours** : multi-sociétés une-base-par-année, menus globaux dédupliqués, clôture →
nouvelle base, arrêt/reprise simulation (voir REFONTE_MENUS_ET_MULTI_SOCIETES.md).

**P1 — fort impact, effort raisonnable, sans dépendance matérielle**
- E-billet **QR** + embarquement par scan (navigateur/clé douchette).
- **Suivi public du colis** + preuve de livraison.
- **Notifications SMS/WhatsApp** (via API ; Mobile Money déjà là).
- **Tableaux de bord KPI** (remplissage, recette/km, coût/km, caisse) — on a déjà le moteur d'états.
- **Maintenance préventive** (alertes par km/date) — extension du Garage.
- **Coût au km par véhicule** (tableau dédié) — on a déjà véhicule-compte + carburant.

**P2 — fort impact, effort/infra plus lourds**
- **Réservation en ligne + plan de salle** (portail public) + canal revendeurs.
- **Applis mobiles** passager / conducteur / agent (POS hors ligne).
- **API ouverte** (paiement, SMS, GPS).
- **Facture électronique DGI** (à cadrer avec l'expert-comptable).

**P3 — différenciation IA / télématique**
- **GPS/télématique** (intégration boîtier) + ETA.
- **Prévision de demande** et **détection d'anomalies** (sur l'historique + simulation).

## 6. Sources (déclaratif éditeur à confirmer)
- ERP généralistes : erpresearch.com (listes/comparaisons 2026), crm.org (top ERP 2026).
- TMS : TechTarget (requirements TMS), Dreamix (guide TMS), Aptean (scope), SaigonTechnology, DevTechnoSys.
- Flotte : Geotab (11 features), Fleetio (G2), SoftwareAdvice (key features).
- Bus/colis : Betterez/Ratality via Busbud (Wikipedia), Zaui, CWTicketing (module colis), LiyuBus (Afrique).
