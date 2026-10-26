# Schéma de la base (généré depuis les modèles Django, sans données)

## Paramètres (core)

### Societe — table `core_societe`
- `id` : BigAutoField
- `raison_sociale` : CharField
- `sigle` : CharField
- `forme_juridique` : CharField
- `niu` : CharField
- `rccm` : CharField
- `adresse` : CharField
- `ville` : CharField
- `pays` : CharField
- `telephone` : CharField
- `email` : CharField
- `devise` : CharField
- `facturation_auto_livraison` : CharField
- `separation_gros_detail` : BooleanField
- `uid` : UUIDField
- `activite` : CharField
- `source_mode` : CharField
- `source_dossier` : CharField
- `source_debut_exercice` : DateField
- `source_bascule_le` : DateTimeField
- `delai_pointage` : PositiveIntegerField
- `regime_tva` : CharField
- `regime_fiscal` : CharField
- `systeme_comptable` : CharField
- `taux_tva_defaut` : DecimalField
- `stock_negatif_autorise` : BooleanField
- `pied_facture` : TextField
- `controle_mentions_facture` : BooleanField

### Exercice — table `core_exercice`
- `id` : BigAutoField
- `code` : CharField
- `date_debut` : DateField
- `date_fin` : DateField
- `cloture` : BooleanField

### Sequence — table `core_sequence`
- `id` : BigAutoField
- `code` : CharField
- `annee` : PositiveIntegerField
- `dernier_numero` : PositiveIntegerField

### DroitAcces — table `core_droitacces`
- `id` : BigAutoField
- `groupe` : ForeignKey → Group
- `module` : CharField
- `code` : CharField
- `niveau` : CharField

### AccesLogiciel — table `core_acceslogiciel`
- `id` : BigAutoField
- `utilisateur` : ForeignKey → User
- `module` : CharField
- `acces` : CharField

### Agence — table `core_agence`
- `id` : BigAutoField
- `code` : CharField
- `nom` : CharField
- `ville` : CharField
- `locale` : BooleanField
- `compte_liaison` : ForeignKey → Compte
- `actif` : BooleanField
- `uid` : UUIDField
- `role` : CharField
- `rang` : PositiveIntegerField
- `cle_echange` : CharField
- `sequence_integree` : PositiveIntegerField
- `derniere_reception` : DateTimeField

### JournalEvenement — table `core_journalevenement`
- `id` : BigAutoField
- `date` : DateTimeField
- `utilisateur` : ForeignKey → User
- `logiciel` : CharField
- `action` : CharField
- `objet_type` : CharField
- `objet_id` : CharField
- `objet_libelle` : CharField
- `details` : JSONField

### LotSynchronisation — table `core_lotsynchronisation`
- `id` : BigAutoField
- `debut` : DateTimeField
- `fin` : DateTimeField
- `utilisateur` : ForeignKey → User
- `dossier` : CharField
- `date_bascule` : DateField
- `applique` : BooleanField
- `conforme` : BooleanField
- `volumes` : JSONField
- `rapport` : TextField

## Gestion commerciale (commercial)

### CategorieTarifaire — table `commercial_categorietarifaire`
- `id` : BigAutoField
- `code` : CharField
- `intitule` : CharField

### Tiers — table `commercial_tiers`
- `id` : BigAutoField
- `type_tiers` : CharField
- `code` : CharField
- `nom` : CharField
- `niu` : CharField
- `rccm` : CharField
- `adresse` : CharField
- `ville` : CharField
- `telephone` : CharField
- `email` : CharField
- `compte_collectif` : ForeignKey → Compte
- `delai_paiement` : PositiveIntegerField
- `plafond_credit` : DecimalField
- `vente_credit` : BooleanField
- `code_risque` : CharField
- `categorie_tarifaire` : ForeignKey → CategorieTarifaire
- `compte_bloque` : BooleanField
- `payeur` : ForeignKey → Tiers
- `assujetti_tva` : BooleanField
- `regime_fiscal` : CharField
- `actif` : BooleanField
- `cree_le` : DateTimeField

### Depot — table `commercial_depot`
- `id` : BigAutoField
- `code` : CharField
- `intitule` : CharField
- `adresse` : CharField
- `ville` : CharField
- `responsable` : CharField
- `principal` : BooleanField
- `vente_detail` : BooleanField
- `fiche_debut` : DateField
- `actif` : BooleanField

### FamilleArticle — table `commercial_famillearticle`
- `id` : BigAutoField
- `code` : CharField
- `libelle` : CharField
- `compte_vente` : ForeignKey → Compte
- `compte_achat` : ForeignKey → Compte

### Article — table `commercial_article`
- `id` : BigAutoField
- `reference` : CharField
- `designation` : CharField
- `nature` : CharField
- `famille` : ForeignKey → FamilleArticle
- `unite` : CharField
- `prix_achat` : DecimalField
- `prix_vente` : DecimalField
- `taux_tva` : DecimalField
- `suivi_stock` : BooleanField
- `stock` : DecimalField
- `cmup` : DecimalField
- `stock_minimum` : DecimalField
- `fournisseur_principal` : ForeignKey → Tiers
- `compte_vente` : ForeignKey → Compte
- `compte_achat` : ForeignKey → Compte
- `article_detail` : ForeignKey → Article
- `facteur_detail` : DecimalField
- `actif` : BooleanField

### Document — table `commercial_document`
- `id` : BigAutoField
- `type_document` : CharField
- `numero` : CharField
- `date` : DateField
- `date_echeance` : DateField
- `tiers` : ForeignKey → Tiers
- `payeur` : ForeignKey → Tiers
- `depot` : ForeignKey → Depot
- `depot_destination` : ForeignKey → Depot
- `reference_externe` : CharField
- `reprise_sage` : CharField
- `source_empreinte` : CharField
- `statut` : CharField
- `origine` : ForeignKey → Document
- `notes` : TextField
- `total_ht` : DecimalField
- `total_tva` : DecimalField
- `total_ttc` : DecimalField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField
- `valide_par` : ForeignKey → User
- `valide_le` : DateTimeField
- `annule_par` : ForeignKey → User
- `annule_le` : DateTimeField

### LigneDocument — table `commercial_lignedocument`
- `id` : BigAutoField
- `document` : ForeignKey → Document
- `article` : ForeignKey → Article
- `designation` : CharField
- `quantite` : DecimalField
- `prix_unitaire` : DecimalField
- `remise` : DecimalField
- `taux_tva` : DecimalField
- `montant_ht` : DecimalField
- `montant_tva` : DecimalField
- `ligne_origine` : ForeignKey → LigneDocument

### Reglement — table `commercial_reglement`
- `id` : BigAutoField
- `reprise_sage` : CharField
- `numero` : CharField
- `date` : DateField
- `tiers` : ForeignKey → Tiers
- `mode` : CharField
- `journal` : ForeignKey → Journal
- `montant` : DecimalField
- `reference` : CharField
- `libelle` : CharField
- `commande` : ForeignKey → Document
- `facture` : ForeignKey → Document
- `agence_encaissement` : ForeignKey → Agence
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### Imputation — table `commercial_imputation`
- `id` : BigAutoField
- `reglement` : ForeignKey → Reglement
- `document` : ForeignKey → Document
- `montant` : DecimalField
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### OperationCaisse — table `commercial_operationcaisse`
- `id` : BigAutoField
- `numero` : CharField
- `date` : DateField
- `nature` : CharField
- `journal` : ForeignKey → Journal
- `montant` : DecimalField
- `libelle` : CharField
- `agence` : ForeignKey → Agence
- `tiers_libre` : CharField
- `compte` : ForeignKey → Compte
- `reference` : CharField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### TarifCategorie — table `commercial_tarifcategorie`
- `id` : BigAutoField
- `article` : ForeignKey → Article
- `categorie` : ForeignKey → CategorieTarifaire
- `prix_vente` : DecimalField

### StockDepot — table `commercial_stockdepot`
- `id` : BigAutoField
- `article` : ForeignKey → Article
- `depot` : ForeignKey → Depot
- `quantite` : DecimalField
- `stock_mini` : DecimalField
- `stock_maxi` : DecimalField

### MouvementStock — table `commercial_mouvementstock`
- `id` : BigAutoField
- `article` : ForeignKey → Article
- `depot` : ForeignKey → Depot
- `date` : DateField
- `quantite` : DecimalField
- `cout_unitaire` : DecimalField
- `document` : ForeignKey → Document
- `libelle` : CharField
- `cree_le` : DateTimeField

### PointageFiche — table `commercial_pointagefiche`
- `id` : BigAutoField
- `numero` : CharField
- `document` : ForeignKey → Document
- `depot` : ForeignKey → Depot
- `date` : DateField
- `statut` : CharField
- `fichiste` : ForeignKey → User
- `observation` : CharField
- `revision` : PositiveIntegerField
- `historique` : JSONField
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### LignePointage — table `commercial_lignepointage`
- `id` : BigAutoField
- `pointage` : ForeignKey → PointageFiche
- `article` : ForeignKey → Article
- `quantite_saisie` : DecimalField
- `quantite_document` : DecimalField

### Inventaire — table `commercial_inventaire`
- `id` : BigAutoField
- `numero` : CharField
- `date` : DateField
- `depot` : ForeignKey → Depot
- `famille` : ForeignKey → FamilleArticle
- `statut` : CharField
- `notes` : TextField
- `cree_par` : ForeignKey → User
- `mouvement_entree` : ForeignKey → Document
- `mouvement_sortie` : ForeignKey → Document
- `cree_le` : DateTimeField

### LigneInventaire — table `commercial_ligneinventaire`
- `id` : BigAutoField
- `inventaire` : ForeignKey → Inventaire
- `article` : ForeignKey → Article
- `stock_theorique` : DecimalField
- `stock_reel` : DecimalField
- `cout_unitaire` : DecimalField

## Comptabilité OHADA (comptabilite)

### Compte — table `comptabilite_compte`
- `id` : BigAutoField
- `numero` : CharField
- `intitule` : CharField
- `lettrable` : BooleanField
- `actif` : BooleanField

### Journal — table `comptabilite_journal`
- `id` : BigAutoField
- `code` : CharField
- `intitule` : CharField
- `type_journal` : CharField
- `compte_tresorerie` : ForeignKey → Compte
- `cloture_au` : DateField

### Taxe — table `comptabilite_taxe`
- `id` : BigAutoField
- `code` : CharField
- `intitule` : CharField
- `sens` : CharField
- `taux` : DecimalField
- `compte` : ForeignKey → Compte

### Banque — table `comptabilite_banque`
- `id` : BigAutoField
- `code` : CharField
- `intitule` : CharField
- `domiciliation` : CharField
- `rib` : CharField
- `journal` : ForeignKey → Journal

### SectionAnalytique — table `comptabilite_sectionanalytique`
- `id` : BigAutoField
- `plan` : CharField
- `code` : CharField
- `intitule` : CharField
- `actif` : BooleanField

### Ecriture — table `comptabilite_ecriture`
- `id` : BigAutoField
- `journal` : ForeignKey → Journal
- `exercice` : ForeignKey → Exercice
- `numero` : CharField
- `date` : DateField
- `libelle` : CharField
- `reference` : CharField
- `statut` : CharField
- `origine` : CharField
- `source_cle` : CharField
- `source_empreinte` : CharField
- `uid` : UUIDField
- `site_origine` : CharField
- `cree_le` : DateTimeField
- `cree_par` : ForeignKey → User

### LigneEcriture — table `comptabilite_ligneecriture`
- `id` : BigAutoField
- `ecriture` : ForeignKey → Ecriture
- `compte` : ForeignKey → Compte
- `tiers` : ForeignKey → Tiers
- `libelle` : CharField
- `debit` : DecimalField
- `credit` : DecimalField
- `lettrage` : CharField
- `source_cle` : CharField
- `section` : ForeignKey → SectionAnalytique
- `vehicule` : ForeignKey → Vehicule
- `date_pointage` : DateField

## Transport de voyageurs (transport)

### ParametresTransport — table `transport_parametrestransport`
- `id` : BigAutoField
- `compte_billets` : ForeignKey → Compte
- `compte_colis` : ForeignKey → Compte
- `compte_fret` : ForeignKey → Compte
- `compte_bagages` : ForeignKey → Compte
- `compte_contre_remboursement` : ForeignKey → Compte
- `compte_billets_a_voyager` : ForeignKey → Compte
- `compte_colis_a_transporter` : ForeignKey → Compte
- `taxe_billets` : ForeignKey → Taxe
- `taxe_colis` : ForeignKey → Taxe
- `compte_remboursements` : ForeignKey → Compte
- `compte_proprietaires` : ForeignKey → Compte
- `compte_carburant` : ForeignKey → Compte
- `compte_pieces` : ForeignKey → Compte
- `compte_main_oeuvre` : ForeignKey → Compte
- `bloquer_papiers_expires` : BooleanField
- `sessions_caisse_obligatoires` : BooleanField
- `avance_depart_toleree` : PositiveIntegerField
- `plafond_depense_sans_autorisation` : DecimalField
- `retenue_annulation` : DecimalField

### Gare — table `transport_gare`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `code` : CharField
- `nom` : CharField
- `ville` : CharField
- `agence` : ForeignKey → Agence
- `caisse` : ForeignKey → Journal
- `mobile_money` : ForeignKey → Journal
- `section` : ForeignKey → SectionAnalytique
- `actif` : BooleanField

### Ligne — table `transport_ligne`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `code` : CharField
- `gare_depart` : ForeignKey → Gare
- `gare_arrivee` : ForeignKey → Gare
- `distance_km` : PositiveIntegerField
- `duree` : CharField
- `prix_billet` : DecimalField
- `colis_forfait` : DecimalField
- `colis_prix_kg` : DecimalField
- `gamme` : CharField
- `actif` : BooleanField

### ChangementGamme — table `transport_changementgamme`
- `id` : BigAutoField
- `vehicule` : ForeignKey → Vehicule
- `gamme` : CharField
- `debut` : DateField
- `enregistre_le` : DateTimeField

### ArretLigne — table `transport_arretligne`
- `id` : BigAutoField
- `ligne` : ForeignKey → Ligne
- `ordre` : PositiveSmallIntegerField
- `gare` : ForeignKey → Gare

### Vehicule — table `transport_vehicule`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `immatriculation` : CharField
- `designation` : CharField
- `type_vehicule` : CharField
- `nombre_places` : PositiveIntegerField
- `gamme` : CharField
- `proprietaire` : ForeignKey → Tiers
- `carte_grise` : CharField
- `mise_en_service` : DateField
- `assurance_echeance` : DateField
- `visite_technique_echeance` : DateField
- `section` : ForeignKey → SectionAnalytique
- `actif` : BooleanField

### Chauffeur — table `transport_chauffeur`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `nom` : CharField
- `telephone` : CharField
- `permis` : CharField
- `actif` : BooleanField

### Depart — table `transport_depart`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `ligne` : ForeignKey → Ligne
- `date` : DateField
- `heure` : TimeField
- `vehicule` : ForeignKey → Vehicule
- `chauffeur` : ForeignKey → Chauffeur
- `convoyeur` : ForeignKey → Employe
- `places` : PositiveIntegerField
- `km_depart` : PositiveIntegerField
- `km_arrivee` : PositiveIntegerField
- `observations` : CharField
- `cloture_le` : DateTimeField
- `cloture_par` : ForeignKey → User
- `vehicule_remplacement` : BooleanField
- `motif_remplacement` : CharField
- `embarquement_valide_le` : DateTimeField
- `embarquement_valide_par` : ForeignKey → User
- `statut` : CharField
- `parti_le` : DateTimeField
- `arrive_le` : DateTimeField
- `ecriture_recettes` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User

### Billet — table `transport_billet`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `date_vente` : DateField
- `gare` : ForeignKey → Gare
- `depart` : ForeignKey → Depart
- `gare_montee` : ForeignKey → Gare
- `gare_arrivee` : ForeignKey → Gare
- `voyageur` : CharField
- `telephone` : CharField
- `piece_identite` : CharField
- `siege` : PositiveIntegerField
- `prix` : DecimalField
- `bagages` : CharField
- `bagages_nombre` : PositiveIntegerField
- `bagages_poids` : DecimalField
- `prix_bagages` : DecimalField
- `paiement` : CharField
- `caisse` : ForeignKey → Journal
- `client` : ForeignKey → Tiers
- `statut` : CharField
- `retenue` : DecimalField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_annulation` : OneToOneField → Ecriture
- `vendu_par` : ForeignKey → User
- `session` : ForeignKey → SessionCaisse
- `session_annulation` : ForeignKey → SessionCaisse
- `cree_le` : DateTimeField
- `annule_par` : ForeignKey → User
- `annule_le` : DateTimeField
- `remboursement` : CharField
- `rembourse_par` : ForeignKey → User
- `rembourse_le` : DateTimeField
- `session_remboursement` : ForeignKey → SessionCaisse
- `ecriture_remboursement` : OneToOneField → Ecriture

### HistoriqueBillet — table `transport_historiquebillet`
- `id` : BigAutoField
- `billet` : ForeignKey → Billet
- `quand` : DateTimeField
- `evenement` : CharField
- `libelle` : CharField
- `utilisateur` : ForeignKey → User

### Troncon — table `transport_troncon`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `billet` : ForeignKey → Billet
- `ordre` : PositiveSmallIntegerField
- `gare_depart` : ForeignKey → Gare
- `gare_arrivee` : ForeignKey → Gare
- `depart` : ForeignKey → Depart
- `siege` : PositiveIntegerField
- `part` : DecimalField
- `part_bagages` : DecimalField
- `statut` : CharField
- `vehicule` : ForeignKey → Vehicule
- `effectue_le` : DateTimeField
- `site_effectue` : CharField
- `embarque` : BooleanField
- `embarque_le` : DateTimeField
- `embarque_par` : ForeignKey → User
- `depart_manque` : ForeignKey → Depart

### Colis — table `transport_colis`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `nature` : CharField
- `date` : DateField
- `gare_depart` : ForeignKey → Gare
- `gare_arrivee` : ForeignKey → Gare
- `expediteur` : CharField
- `tel_expediteur` : CharField
- `destinataire` : CharField
- `tel_destinataire` : CharField
- `description` : CharField
- `nombre` : PositiveIntegerField
- `poids` : DecimalField
- `valeur_declaree` : DecimalField
- `prix` : DecimalField
- `port` : CharField
- `contre_remboursement` : DecimalField
- `client` : ForeignKey → Tiers
- `depart` : ForeignKey → Depart
- `statut` : CharField
- `code_retrait` : CharField
- `livre_le` : DateTimeField
- `retire_par` : CharField
- `recette_constatee` : BooleanField
- `livre_site` : CharField
- `cr_reverse_le` : DateTimeField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_livraison` : OneToOneField → Ecriture
- `ecriture_reversement` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField
- `livre_par` : ForeignKey → User
- `session` : ForeignKey → SessionCaisse
- `session_livraison` : ForeignKey → SessionCaisse
- `session_reversement` : ForeignKey → SessionCaisse

### DepenseVehicule — table `transport_depensevehicule`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `date` : DateField
- `vehicule` : ForeignKey → Vehicule
- `depart` : ForeignKey → Depart
- `nature` : CharField
- `libelle` : CharField
- `montant` : DecimalField
- `caisse` : ForeignKey → Journal
- `compte` : ForeignKey → Compte
- `reference` : CharField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User

### SessionCaisse — table `transport_sessioncaisse`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `agent` : ForeignKey → User
- `service` : CharField
- `gare` : ForeignKey → Gare
- `caisse` : ForeignKey → Journal
- `fonds_initial` : DecimalField
- `ouverte_le` : DateTimeField
- `fermee_le` : DateTimeField
- `montant_compte` : DecimalField
- `attendu` : DecimalField
- `ecart` : DecimalField
- `justification` : CharField
- `remis_a` : CharField
- `statut` : CharField
- `approuvee_par` : ForeignKey → User
- `approuvee_le` : DateTimeField
- `imputation_ecart` : CharField
- `ecriture_ecart` : OneToOneField → Ecriture

### TransfertFonds — table `transport_transfertfonds`
- `id` : BigAutoField
- `uid` : UUIDField
- `numero` : CharField
- `date_envoi` : DateField
- `origine` : ForeignKey → Journal
- `destination` : ForeignKey → Journal
- `montant` : DecimalField
- `porteur` : CharField
- `statut` : CharField
- `date_reception` : DateField
- `ecriture_envoi` : OneToOneField → Ecriture
- `ecriture_reception` : OneToOneField → Ecriture
- `envoye_par` : ForeignKey → User
- `recu_par` : ForeignKey → User

### ClotureJournee — table `transport_cloturejournee`
- `id` : BigAutoField
- `date` : DateField
- `perimetre` : CharField
- `cloture_par` : ForeignKey → User
- `cloture_le` : DateTimeField
- `commentaire` : CharField
- `anomalies` : JSONField

### AvanceMission — table `transport_avancemission`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `depart` : ForeignKey → Depart
- `beneficiaire` : CharField
- `date` : DateField
- `montant` : DecimalField
- `caisse` : ForeignKey → Journal
- `statut` : CharField
- `restitue` : DecimalField
- `complement` : DecimalField
- `justifiee_le` : DateField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_justification` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User

### JustificatifMission — table `transport_justificatifmission`
- `id` : BigAutoField
- `avance` : ForeignKey → AvanceMission
- `nature` : CharField
- `libelle` : CharField
- `montant` : DecimalField
- `compte` : ForeignKey → Compte

### DemandeDepense — table `transport_demandedepense`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `date` : DateField
- `agence` : CharField
- `nature` : CharField
- `compte` : ForeignKey → Compte
- `libelle` : CharField
- `beneficiaire` : CharField
- `montant` : DecimalField
- `vehicule` : ForeignKey → Vehicule
- `statut` : CharField
- `demande_par` : CharField
- `decision_par` : CharField
- `decision_le` : DateTimeField
- `motif` : CharField
- `caisse` : ForeignKey → Journal
- `payeur` : CharField
- `paye_le` : DateField
- `paye_par` : CharField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_regularisation` : OneToOneField → Ecriture

### Incident — table `transport_incident`
- `id` : BigAutoField
- `uid` : UUIDField
- `numero` : CharField
- `depart` : ForeignKey → Depart
- `type_incident` : CharField
- `date` : DateField
- `lieu` : CharField
- `description` : CharField
- `vehicule_secours` : ForeignKey → Vehicule
- `part_restante` : DecimalField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### FraisIncident — table `transport_fraisincident`
- `id` : BigAutoField
- `incident` : ForeignKey → Incident
- `nature` : CharField
- `libelle` : CharField
- `montant` : DecimalField
- `compte` : ForeignKey → Compte
- `vehicule` : ForeignKey → Vehicule
- `paiement` : CharField
- `caisse` : ForeignKey → Journal
- `fournisseur` : ForeignKey → Tiers
- `ecriture` : OneToOneField → Ecriture

## Garage (garage)

### PleinCarburant — table `garage_pleincarburant`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `date` : DateField
- `vehicule` : ForeignKey → Vehicule
- `depart` : ForeignKey → Depart
- `litres` : DecimalField
- `prix_litre` : DecimalField
- `montant` : DecimalField
- `kilometrage` : PositiveIntegerField
- `station` : CharField
- `paiement` : CharField
- `caisse` : ForeignKey → Journal
- `fournisseur` : ForeignKey → Tiers
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User
- `cree_le` : DateTimeField

### OrdreReparation — table `garage_ordrereparation`
- `id` : BigAutoField
- `uid` : UUIDField
- `site_origine` : CharField
- `numero` : CharField
- `vehicule` : ForeignKey → Vehicule
- `date_entree` : DateField
- `date_sortie` : DateField
- `kilometrage` : PositiveIntegerField
- `panne` : CharField
- `intervenant` : CharField
- `statut` : CharField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User

### LigneReparation — table `garage_lignereparation`
- `id` : BigAutoField
- `ordre` : ForeignKey → OrdreReparation
- `nature` : CharField
- `designation` : CharField
- `quantite` : DecimalField
- `prix_unitaire` : DecimalField
- `paiement` : CharField
- `fournisseur` : ForeignKey → Tiers

## Personnel et paie (personnel)

### Employe — table `personnel_employe`
- `id` : BigAutoField
- `matricule` : CharField
- `nom` : CharField
- `telephone` : CharField
- `poste` : CharField
- `service` : CharField
- `agence` : ForeignKey → Agence
- `vehicule` : ForeignKey → Vehicule
- `chauffeur` : OneToOneField → Chauffeur
- `salaire_base` : DecimalField
- `date_embauche` : DateField
- `ventilation` : CharField
- `numero_cnps` : CharField
- `mode_paiement` : CharField
- `actif` : BooleanField

### RubriquePaie — table `personnel_rubriquepaie`
- `id` : BigAutoField
- `code` : CharField
- `libelle` : CharField
- `nature` : CharField
- `calcul` : CharField
- `valeur` : DecimalField
- `plafond` : DecimalField
- `compte` : ForeignKey → Compte
- `compte_contrepartie` : ForeignKey → Compte
- `automatique` : BooleanField
- `actif` : BooleanField

### Avance — table `personnel_avance`
- `id` : BigAutoField
- `employe` : ForeignKey → Employe
- `date` : DateField
- `montant` : DecimalField
- `caisse` : ForeignKey → Journal
- `motif` : CharField
- `ecriture` : OneToOneField → Ecriture
- `bulletin` : ForeignKey → Bulletin

### PeriodePaie — table `personnel_periodepaie`
- `id` : BigAutoField
- `annee` : PositiveIntegerField
- `mois` : PositiveSmallIntegerField
- `statut` : CharField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_paiement` : OneToOneField → Ecriture

### Bulletin — table `personnel_bulletin`
- `id` : BigAutoField
- `periode` : ForeignKey → PeriodePaie
- `employe` : ForeignKey → Employe
- `salaire_base` : DecimalField
- `brut` : DecimalField
- `retenues` : DecimalField
- `avances` : DecimalField
- `net` : DecimalField
- `patronales` : DecimalField

### LigneBulletin — table `personnel_lignebulletin`
- `id` : BigAutoField
- `bulletin` : ForeignKey → Bulletin
- `rubrique` : ForeignKey → RubriquePaie
- `montant_saisi` : DecimalField
- `montant` : DecimalField

## Partenaires propriétaires (partenaires)

### ContratPartenaire — table `partenaires_contratpartenaire`
- `id` : BigAutoField
- `uid` : UUIDField
- `numero` : CharField
- `version` : PositiveIntegerField
- `partenaire` : ForeignKey → Tiers
- `vehicule` : ForeignKey → Vehicule
- `modele` : CharField
- `debut` : DateField
- `fin` : DateField
- `taux_commission` : DecimalField
- `montant_location` : DecimalField
- `periodicite` : CharField
- `taux_proprietaire` : DecimalField
- `plancher_zero` : BooleanField
- `charge_carburant` : BooleanField
- `charge_reparations` : BooleanField
- `charge_equipage` : BooleanField
- `charge_route` : BooleanField
- `charge_autres` : BooleanField
- `statut` : CharField
- `approuve_par` : ForeignKey → User
- `notes` : CharField

### Decompte — table `partenaires_decompte`
- `id` : BigAutoField
- `uid` : UUIDField
- `numero` : CharField
- `contrat` : ForeignKey → ContratPartenaire
- `debut` : DateField
- `fin` : DateField
- `recettes` : DecimalField
- `commission` : DecimalField
- `depenses` : DecimalField
- `location` : DecimalField
- `fixe` : DecimalField
- `variable` : DecimalField
- `montant_du` : DecimalField
- `detail` : JSONField
- `statut` : CharField
- `ecriture` : OneToOneField → Ecriture
- `ecriture_fixe` : OneToOneField → Ecriture
- `approuve_par` : ForeignKey → User
- `approuve_le` : DateTimeField

### ReglementPartenaire — table `partenaires_reglementpartenaire`
- `id` : BigAutoField
- `uid` : UUIDField
- `nature` : CharField
- `numero` : CharField
- `partenaire` : ForeignKey → Tiers
- `decompte` : ForeignKey → Decompte
- `date` : DateField
- `montant` : DecimalField
- `caisse` : ForeignKey → Journal
- `reference` : CharField
- `ecriture` : OneToOneField → Ecriture
- `cree_par` : ForeignKey → User

### DemandeRetrait — table `partenaires_demanderetrait`
- `id` : BigAutoField
- `uid` : UUIDField
- `numero` : CharField
- `partenaire` : ForeignKey → Tiers
- `date` : DateField
- `montant` : DecimalField
- `motif` : CharField
- `statut` : CharField
- `demande_par` : ForeignKey → User
- `decision_par` : ForeignKey → User
- `reglement` : OneToOneField → ReglementPartenaire

## Échanges entre sites (echanges)

### Evenement — table `echanges_evenement`
- `id` : BigAutoField
- `sequence` : PositiveBigIntegerField
- `uid` : UUIDField
- `type` : CharField
- `objet_uid` : UUIDField
- `revision` : PositiveIntegerField
- `operation` : CharField
- `date_metier` : DateField
- `auteur` : CharField
- `payload` : JSONField
- `cree_le` : DateTimeField

### LotEmis — table `echanges_lotemis`
- `id` : BigAutoField
- `uid` : UUIDField
- `destination` : ForeignKey → Agence
- `sequence_de` : PositiveBigIntegerField
- `sequence_a` : PositiveBigIntegerField
- `nombre` : PositiveIntegerField
- `relayes` : PositiveIntegerField
- `nom_fichier` : CharField
- `empreinte` : CharField
- `taille` : PositiveIntegerField
- `cree_le` : DateTimeField
- `cree_par` : ForeignKey → User

### LotRecu — table `echanges_lotrecu`
- `id` : BigAutoField
- `uid` : UUIDField
- `source` : ForeignKey → Agence
- `empreinte` : CharField
- `nom_fichier` : CharField
- `nombre` : PositiveIntegerField
- `recu_le` : DateTimeField
- `recu_par` : ForeignKey → User
- `rapport` : TextField

### EvenementRecu — table `echanges_evenementrecu`
- `id` : BigAutoField
- `site_origine` : ForeignKey → Agence
- `uid` : UUIDField
- `sequence` : PositiveBigIntegerField
- `type` : CharField
- `objet_uid` : UUIDField
- `revision` : PositiveIntegerField
- `operation` : CharField
- `date_metier` : DateField
- `auteur` : CharField
- `payload` : JSONField
- `empreinte` : CharField
- `relaye` : BooleanField
- `statut` : CharField
- `message` : CharField
- `lot` : ForeignKey → LotRecu
- `integre_le` : DateTimeField

### Relais — table `echanges_relais`
- `id` : BigAutoField
- `evenement` : ForeignKey → EvenementRecu
- `destination` : ForeignKey → Agence
- `lot` : ForeignKey → LotEmis

## Reporting (reporting)
