from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class Societe(models.Model):
    """Fiche unique de l'entreprise utilisatrice de l'ERP."""

    # Configuration de la TVA choisie à la création de la société (rien n'est imposé)
    TVA_NON_PRECISEE = ""
    TVA_AUTOMATIQUE = "AUTOMATIQUE"
    TVA_MANUELLE = "MANUELLE"
    TVA_NON_ASSUJETTIE = "NON_ASSUJETTIE"
    TVA_ASSUJETTIE = TVA_AUTOMATIQUE          # ancien nom
    REGIMES_TVA = [
        (TVA_NON_PRECISEE, "Non précisée"),
        (TVA_AUTOMATIQUE, "Configuration automatique (TVA du Cameroun)"),
        (TVA_MANUELLE, "Configuration manuelle (aucune TVA paramétrée)"),
        (TVA_NON_ASSUJETTIE, "Société non assujettie à la TVA"),
    ]

    raison_sociale = models.CharField(max_length=150, default="Ma Société")
    sigle = models.CharField(max_length=30, blank=True)
    forme_juridique = models.CharField(max_length=30, blank=True, help_text="SARL, SA, SAS, ETS...")
    niu = models.CharField("N° contribuable (NIU)", max_length=30, blank=True)
    rccm = models.CharField("RCCM", max_length=50, blank=True)
    adresse = models.CharField(max_length=200, blank=True)
    ville = models.CharField(max_length=80, blank=True)
    pays = models.CharField(max_length=80, blank=True, default="Cameroun")
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    devise = models.CharField(max_length=10, default="XAF")
    FACTURATION_AUCUNE = "AUCUNE"
    FACTURATION_BROUILLON = "BROUILLON"
    FACTURATION_VALIDEE = "VALIDEE"
    FACTURATIONS_AUTO = [(FACTURATION_VALIDEE, "Facture créée et validée"), (FACTURATION_BROUILLON, "Facture créée en brouillon"),
                         (FACTURATION_AUCUNE, "Pas de facture automatique")]
    facturation_auto_livraison = models.CharField(
        "Facture à la livraison", max_length=10, choices=FACTURATIONS_AUTO, default=FACTURATION_VALIDEE,
        help_text="Quand le magasin valide le bon de livraison issu d'un bon de commande, la facture des quantités "
                  "livrées est établie le même jour (les avances versées sur la commande y sont imputées)")
    separation_gros_detail = models.BooleanField(
        "Vente au détail réservée aux dépôts désignés", default=False,
        help_text="Les magasins de gros ne vendent que par unités entières (pas de carton ouvert) ; la vente au détail "
                  "se fait uniquement dans les dépôts désignés (boutiques), approvisionnés par transfert")
    # Activité : commerce (achat-revente avec stocks), transport interurbain de voyageurs, ou les deux
    ACTIVITE_COMMERCE = "COMMERCE"
    ACTIVITE_TRANSPORT = "TRANSPORT"
    ACTIVITE_MIXTE = "MIXTE"
    ACTIVITES = [(ACTIVITE_COMMERCE, "Commerce (achat-revente, stocks)"),
                 (ACTIVITE_TRANSPORT, "Transport de voyageurs (billetterie, colis, logistique)"),
                 (ACTIVITE_MIXTE, "Commerce et transport")]
    uid = models.UUIDField("Identifiant de la société", null=True, blank=True, editable=False,
                           help_text="Le même dans tous les sites de la société (siège et agences)")
    activite = models.CharField("Activité", max_length=10, choices=ACTIVITES, default=ACTIVITE_COMMERCE,
                                help_text="Choisit les logiciels proposés dans le portail (la comptabilité est commune)")
    # Synchronisation avec le dossier de l'ancien logiciel (transition), puis bascule vers l'ERP
    SYNCHRO_AUCUNE = ""
    SYNCHRO_MIROIR = "MIROIR"
    SYNCHRO_BASCULE = "BASCULE"
    MODES_SYNCHRO = [(SYNCHRO_AUCUNE, "Aucune"), (SYNCHRO_MIROIR, "Copie synchronisée (saisie dans l'ancien logiciel)"),
                     (SYNCHRO_BASCULE, "Bascule effectuée (saisie dans l'ERP)")]
    assistant_termine = models.BooleanField(
        "Première configuration terminée", default=True,
        help_text="Faux à la création d'un dossier par le programme compilé : l'assistant s'ouvre au premier passage.")
    source_mode = models.CharField("Synchronisation", max_length=10, choices=MODES_SYNCHRO, blank=True, default=SYNCHRO_AUCUNE)
    source_dossier = models.CharField("Dossier d'origine synchronisé", max_length=200, blank=True)
    source_debut_exercice = models.DateField("Début d'exercice du dossier d'origine", null=True, blank=True)
    source_bascule_le = models.DateTimeField("Bascule effectuée le", null=True, blank=True)
    delai_pointage = models.PositiveIntegerField(
        "Délai de pointage des bons (jours)", default=1,
        help_text="Fiche de stock : un bon non pointé par le fichiste au-delà de ce délai est signalé en retard")
    regime_tva = models.CharField(
        "Configuration de la TVA", max_length=20, choices=REGIMES_TVA, blank=True, default=TVA_NON_PRECISEE,
        help_text="Automatique : taux du Cameroun créés (19,25 % ; 11 % ; 0 % export) et proposés sur les articles. "
                  "Manuelle : aucune TVA paramétrée, vous la saisissez vous-même si besoin (Structure › Taux de taxes, "
                  "fiche article). Non assujettie : ventes sans TVA, TVA des achats incluse dans le coût.")
    REGIMES_FISCAUX = [
        ("", "Non précisé"),
        ("REEL", "Régime du réel"),
        ("IGS", "Impôt général synthétique (IGS)"),
        ("OBNL", "Organisme à but non lucratif"),
        ("NON_PROFESSIONNEL", "Contribuable non professionnel"),
    ]
    regime_fiscal = models.CharField(
        "Régime d'imposition", max_length=20, choices=REGIMES_FISCAUX, blank=True,
        help_text="CGI 2026, art. 93 ter et quater. IGS : CA annuel HT < 50 M FCFA (30 M pour les professions libérales).")
    SYSTEME_NORMAL, SYSTEME_SMT = "NORMAL", "SMT"
    SYSTEMES_COMPTABLES = [(SYSTEME_NORMAL, "Système normal"), (SYSTEME_SMT, "Système minimal de trésorerie (SMT)")]
    systeme_comptable = models.CharField(
        "Système comptable (présentation des états financiers)", max_length=10, choices=SYSTEMES_COMPTABLES,
        default=SYSTEME_NORMAL,
        help_text="Acte uniforme OHADA relatif au droit comptable : système normal, ou système minimal de trésorerie "
                  "réservé aux très petites entités (seuils de l'Acte uniforme, à confirmer avec l'expert-comptable). "
                  "La saisie reste la même ; seuls le bilan et le compte de résultat changent de présentation.")
    longueur_comptes = models.PositiveSmallIntegerField(
        "Longueur des numéros de compte", default=0,
        help_text="7 : tous les comptes du plan ont 7 chiffres (4111 devient 4111000, complété par des zéros à droite). "
                  "0 : longueur libre, par exemple pour garder le plan d'un dossier repris d'un autre logiciel. "
                  "Pour changer la longueur d'un dossier existant : commande « longueur_comptes ».")
    taux_tva_defaut = models.DecimalField("Taux TVA par défaut (%)", max_digits=5, decimal_places=2, default=Decimal("0"),
                                          help_text="0 par défaut : pas de TVA tant que la société ne l'active pas")
    stock_negatif_autorise = models.BooleanField(
        "Autoriser le stock négatif", default=False,
        help_text="Si décoché, une sortie de stock supérieure au stock disponible du dépôt est refusée")
    pied_facture = models.TextField(blank=True, help_text="Mentions affichées en bas des factures")
    controle_mentions_facture = models.BooleanField(
        "Signaler les mentions légales manquantes des factures", default=False,
        help_text="Facultatif : avertit à la validation d'une facture s'il manque le NIU, le RCCM ou une adresse")

    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Société"

    def __str__(self):
        return self.raison_sociale

    @property
    def assujettie_tva(self):
        """Seule l'option « non assujettie » supprime la TVA : sinon les taux saisis sur les articles et lignes s'appliquent."""
        return self.regime_tva != self.TVA_NON_ASSUJETTIE

    @classmethod
    def get(cls):
        obj = cls.objects.order_by("pk").first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class Exercice(models.Model):
    code = models.CharField(max_length=20, unique=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    cloture = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_debut"]
        verbose_name = "Exercice comptable"
        verbose_name_plural = "Exercices comptables"

    def __str__(self):
        return self.code

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut > self.date_fin:
            raise ValidationError("La date de début doit précéder la date de fin.")

    @classmethod
    def pour_date(cls, date):
        exercice = cls.objects.filter(date_debut__lte=date, date_fin__gte=date).first()
        if exercice is None:
            raise ValidationError(f"Aucun exercice comptable ne couvre la date du {date:%d/%m/%Y}.")
        if exercice.cloture:
            raise ValidationError(f"L'exercice {exercice.code} est clôturé.")
        return exercice

    @classmethod
    def courant(cls):
        from django.utils import timezone

        today = timezone.localdate()
        return cls.objects.filter(date_debut__lte=today, date_fin__gte=today).first() or cls.objects.first()


class Sequence(models.Model):
    """Compteur de numérotation (factures, pièces comptables...) par code et par année."""

    code = models.CharField(max_length=20)
    annee = models.PositiveIntegerField()
    dernier_numero = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("code", "annee")

    def __str__(self):
        return f"{self.code}{self.annee} → {self.dernier_numero}"

    @classmethod
    def suivant(cls, code, annee, largeur=5):
        with transaction.atomic():
            seq, _ = cls.objects.select_for_update().get_or_create(code=code, annee=annee)
            seq.dernier_numero += 1
            seq.save(update_fields=["dernier_numero"])
        return f"{code}{annee}-{seq.dernier_numero:0{largeur}d}"

    @classmethod
    def piece(cls, code, annee, largeur=5):
        """Numéro d'une pièce qui circule entre agences : préfixé par le code de l'agence quand les échanges sont
        configurés (DLA-BIL2026-000001), pour que deux agences ne produisent jamais le même numéro."""
        from apps.echanges.publication import site_local

        local = site_local()
        numero = cls.suivant(code, annee, largeur)
        return f"{local.code}-{numero}" if local is not None else numero


class DroitAcces(models.Model):
    """Fichier › Autorisations d'accès : niveau d'un profil (groupe) sur une entrée de menu d'un logiciel."""

    from .droits import NIVEAUX as _NIVEAUX

    groupe = models.ForeignKey("auth.Group", on_delete=models.CASCADE, related_name="droits", verbose_name="Profil")
    module = models.CharField("Logiciel", max_length=20)
    code = models.CharField("Entrée de menu", max_length=100)
    niveau = models.CharField(max_length=20, choices=_NIVEAUX)

    class Meta:
        unique_together = ("groupe", "module", "code")
        verbose_name = "Autorisation d'accès"
        verbose_name_plural = "Autorisations d'accès"

    def __str__(self):
        return f"{self.groupe} · {self.module} · {self.code} : {self.get_niveau_display()}"


class AccesLogiciel(models.Model):
    """Accès d'un utilisateur à un logiciel lié : en tant qu'utilisateur, en tant qu'invité, ou aucun accès."""

    from .droits import ACCES as _ACCES

    utilisateur = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="acces_logiciels")
    module = models.CharField("Logiciel", max_length=20)
    acces = models.CharField("Accès", max_length=20, choices=_ACCES)

    class Meta:
        unique_together = ("utilisateur", "module")
        verbose_name = "Accès à un logiciel"
        verbose_name_plural = "Accès aux logiciels"

    def __str__(self):
        return f"{self.utilisateur} · {self.module} : {self.get_acces_display()}"


class Agence(models.Model):
    """Agence de la société. Chaque agence travaille sur son propre serveur ; ce dossier est celui de l'agence
    « locale ». Les autres agences servent aux opérations faites pour leur compte (versements hors recettes,
    sorties pour une autre agence), passées sur leur compte de liaison."""

    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    ville = models.CharField(max_length=80, blank=True)
    locale = models.BooleanField("Agence de ce dossier", default=False,
                                 help_text="L'agence qui travaille sur ce serveur (une seule)")
    compte_liaison = models.ForeignKey(
        "comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
        verbose_name="Compte de liaison", help_text="Compte de liaison de l'agence (classe 18). Vide : créé automatiquement.")
    actif = models.BooleanField(default=True)
    # Échanges entre sites (serveurs hors ligne) : lots signés transmis par WhatsApp, Telegram, clé USB…
    SIEGE, AGENCE = "SIEGE", "AGENCE"
    ROLES = [(SIEGE, "Siège (consolidation)"), (AGENCE, "Agence")]
    uid = models.UUIDField("Identifiant de site", null=True, blank=True, unique=True, editable=False)
    role = models.CharField("Rôle", max_length=10, choices=ROLES, default=AGENCE)
    rang = models.PositiveIntegerField("N° d'ordre", null=True, blank=True, unique=True,
                                       help_text="Attribué par le siège ; donne le compte de liaison 185NN, le même dans tous les dossiers")
    cle_echange = models.CharField("Clé d'échange", max_length=64, blank=True, editable=False,
                                   help_text="Secret partagé entre ce site et le siège (signature des lots)")
    sequence_integree = models.PositiveIntegerField("Dernier événement intégré", default=0, editable=False)
    derniere_reception = models.DateTimeField("Dernier lot reçu le", null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-locale", "nom"]
        verbose_name = "Agence"

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @classmethod
    def locale_ou_none(cls):
        return cls.objects.filter(locale=True).first()

    def save(self, *args, **kwargs):
        if self.locale:
            Agence.objects.exclude(pk=self.pk).filter(locale=True).update(locale=False)
        if not self.locale and not self.compte_liaison_id:
            self.compte_liaison = self._creer_compte_liaison()
        super().save(*args, **kwargs)

    def _creer_compte_liaison(self):
        """185 « Comptes permanents non bloqués des établissements et succursales » + numéro d'ordre (celui du siège
        s'il est connu, pour que le même compte désigne la même agence dans tous les dossiers)."""
        from apps.comptabilite.models import Compte

        if self.rang:
            return Compte.objects.get_or_create(numero=f"185{self.rang:02d}",
                                                defaults={"intitule": f"Liaison agence {self.nom}"[:200]})[0]
        rang = 1
        while Compte.objects.filter(numero=f"185{rang:02d}").exists():
            rang += 1
        return Compte.objects.create(numero=f"185{rang:02d}", intitule=f"Liaison agence {self.nom}"[:200])


class JournalEvenement(models.Model):
    """Journal des événements : trace de chaque création, modification, validation, suppression et connexion."""

    ACTIONS = [
        ("CREATION", "Création"), ("MODIFICATION", "Modification"), ("VALIDATION", "Validation"),
        ("ANNULATION", "Annulation"), ("SUPPRESSION", "Suppression"), ("CLOTURE", "Clôture"),
        ("CONNEXION", "Connexion"), ("ECHEC_CONNEXION", "Échec de connexion"),
        ("SAUVEGARDE", "Sauvegarde"), ("RESTAURATION", "Restauration"),
    ]

    date = models.DateTimeField(auto_now_add=True, db_index=True)
    utilisateur = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    logiciel = models.CharField(max_length=30, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS, db_index=True)
    objet_type = models.CharField("Type", max_length=60, blank=True, db_index=True)
    objet_id = models.CharField(max_length=40, blank=True)
    objet_libelle = models.CharField("Objet", max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Événement"
        verbose_name_plural = "Journal des événements"

    def __str__(self):
        return f"{self.date:%d/%m/%Y %H:%M} {self.get_action_display()} {self.objet_type} {self.objet_libelle}"


class LotSynchronisation(models.Model):
    """Un passage de synchronisation (ou de simulation) depuis le dossier de l'ancien logiciel : quand, quoi, résultat."""

    debut = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    utilisateur = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    dossier = models.CharField(max_length=200)
    date_bascule = models.DateField("Données jusqu'au")
    applique = models.BooleanField("Appliqué", default=False, help_text="Faux : simulation (rien n'a été enregistré)")
    conforme = models.BooleanField(default=False)
    volumes = models.JSONField(default=dict, blank=True, help_text="Par donnée : lues, créées, mises à jour, supprimées")
    rapport = models.TextField(blank=True)

    class Meta:
        ordering = ["-debut"]
        verbose_name = "Lot de synchronisation"

    def __str__(self):
        return f"{self.debut:%d/%m/%Y %H:%M} · {self.dossier} · {'appliqué' if self.applique else 'simulation'}"
