# 02 — Menu Fichier [DOC-V12]

**Source principale : S1, pages 1 à 6.** Les niveaux ci-dessous sont des regroupements fonctionnels de Sage, et ne sont pas tous des sous-menus déroulants autonomes.

## Commandes de premier niveau

- Nouveau ; Ouvrir ; Favoris ; Fermer.
- Paramètres société.
- Lire les informations : documents, structure.
- Configuration système et partage : système, utilisateurs (sur site selon édition).
- Autorisations d'accès : mot de passe, utilisateurs, paramètres de sécurité.
- Importer : format Sage, catalogue fournisseur, catalogue fournisseur + article, format paramétrable.
- Exporter : format Sage/HTML, format paramétrable.
- Format import/export paramétrable.
- Communication site à site : communication, planifiée (selon déploiement).
- Paiement en ligne (selon déploiement).
- Mise en page ; Format d'impression ; Impression différée.
- Outils.

## Paramètres société — cartographie des sections

### Identification
- Identification générale, coordonnées, télécommunication et immatriculation.
- Monnaie de tenue, formats quantité/prix, préférences de saisie et du dossier.
- Options fiscales/IFRS, informations liées et sécurité/traçabilité.

### Articles
- Général : règles de création, références fournisseurs, poids, production, suivi série/lot si option.
- Codification : références, codes-barres, gammes et conditionnements selon licence.
- Catalogue articles, unités d'achat/vente, conditionnements, gammes.
- Grilles de remise, arrondis, statistiques, informations libres.

### Comptes et tiers
- Comptes généraux : paramètres et informations libres.
- Tiers : codification, catégories tarifaires, modes de règlement, périodicité de livraison, codes risques, statistiques et comptes collectifs.

### Ressources, analytique et fiscalité
- Ressources / informations libres (module optionnel).
- Analytique : général, axes/plans analytiques affaire, article, IFRS, niveaux d'analyse.
- TVA et taxes : informations fiscales, mentions d'exonération.

### Contacts, international et banques
- Contacts : services et types.
- International : devises, pays.
- Banques : structure des banques.

### Documents
- Calcul des marges, remises, échéances, stocks en saisie, droits de création pendant la saisie.
- Numérotation et souches des documents ventes/achats/internes, circuits de validation.
- Bouton Actions ; conditions générales de vente ; mentions de paiement et pénalités.
- Informations libres sur en-têtes, lignes et éventuels lots/séries ; motifs des devis perdus.

### Logistique
- Stock : règles d'indisponibilité, stocks négatifs, alertes.
- Contremarque et emplacement multi-dépôts (option/édition).
- Livraisons : calendrier, encours, non-livrés, préparations, expéditions et conditions de livraison.
- Impression d'étiquettes de réception/colisage selon option.

### Comptabilisation
- Général : réglages de transfert, écarts, TVA, gestion devises.
- Catégories comptables ventes/achats/stock.
- Factures, règlements, engagements et ventes comptoir ; analytique et IFRS selon édition.

### Échanges et applications externes
- Services Sage, import, échanges entre sites, facturation et paiement connectés.
- Connexions Microsoft 365, stockage/partage et autres services selon déploiement.

### Agenda, factures électroniques, colonnage, modèles
- Agenda : alertes, types d'événements.
- Factures électroniques : émission/réception, identification et règles d'intégration, sous réserve du périmètre fiscal.
- Colonnage des ventes, achats, stocks, inventaires, règlements, tiers et autres objets.
- Libellés d'interface, modèles de documents, modèles d'impression et personnalisation en saisie.

## Fichier > Outils

Opérations mentionnées dans S1 : mise à jour des tarifs, références/codes-barres et prévisions ; modification du suivi de stock ; fusion, recalcul d'informations libres ; réajustement de cumuls ; historiques des modifications/suppressions ; purge ; maintenance ; réorganisation de la base ; sauvegarde/restauration de société ; journaux de maintenance, événements légaux et audit ; import/export de préférences ; réinitialisation de paramètres ou authentification.

**DANGER :** une bonne partie de ces commandes modifie massivement les données. Lors d'un audit UI, les **identifier sans les exécuter**. Une simulation ou une maquette doit rendre explicites confirmation, permissions et portée des changements.
