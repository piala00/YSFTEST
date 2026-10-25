"""Transport interurbain de voyageurs : billetterie, colis et courrier, fret, flotte — liés à la comptabilité OHADA.

Schémas comptables (comptes réglables dans Paramètres transport, à valider par l'expert-comptable) :
  Billet vendu au comptant      D caisse de la gare          / C 70611 Transport de voyageurs (+ C taxe si réglée)
  Billet vendu en compte        D 411 client                  / C 70611
  Billet annulé (remboursement) D 70611 (prix − retenue)      / C caisse (ou 411)  — la retenue reste acquise
  Colis port payé               D caisse de la gare de départ / C 70612 Colis et courrier (70613 pour le fret)
  Colis port dû, à la livraison D caisse de la gare d'arrivée / C 70612
  Contre-remboursement encaissé D caisse                      / C 4718 Envois contre remboursement à reverser
  … reversé à l'expéditeur      D 4718                        / C caisse
  Dépense de véhicule           D 6xx (section du véhicule)   / C caisse
"""
import secrets
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _arrondi(valeur):
    return Decimal(valeur).quantize(Decimal("1"), rounding=ROUND_HALF_UP)       # FCFA : pas de centimes


class ParametresTransport(models.Model):
    """Comptes et taxes du transport (une seule fiche). Créés au premier usage ; modifiables ensuite."""

    compte_billets = models.ForeignKey("comptabilite.Compte", on_delete=models.PROTECT, related_name="+",
                                       verbose_name="Produits des billets")
    compte_colis = models.ForeignKey("comptabilite.Compte", on_delete=models.PROTECT, related_name="+",
                                     verbose_name="Produits des colis et courriers")
    compte_fret = models.ForeignKey("comptabilite.Compte", on_delete=models.PROTECT, related_name="+",
                                    verbose_name="Produits du fret")
    compte_contre_remboursement = models.ForeignKey(
        "comptabilite.Compte", on_delete=models.PROTECT, related_name="+", verbose_name="Fonds contre remboursement à reverser")
    taxe_billets = models.ForeignKey("comptabilite.Taxe", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                     verbose_name="Taxe sur les billets", help_text="Vide : aucune taxe (réglage par défaut)")
    taxe_colis = models.ForeignKey("comptabilite.Taxe", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                   verbose_name="Taxe sur les colis et le fret", help_text="Vide : aucune taxe (réglage par défaut)")
    retenue_annulation = models.DecimalField(
        "Retenue sur billet annulé (%)", max_digits=5, decimal_places=2, default=ZERO,
        help_text="Part du prix gardée par l'agence quand un voyageur annule (modifiable à chaque annulation)")

    class Meta:
        verbose_name = "Paramètres transport"

    COMPTES = {"compte_billets": ("70611", "Transport de voyageurs (billets)"),
               "compte_colis": ("70612", "Colis et courrier"),
               "compte_fret": ("70613", "Fret et logistique"),
               "compte_contre_remboursement": ("4718", "Envois contre remboursement à reverser")}

    @classmethod
    def get(cls):
        fiche = cls.objects.first()
        if fiche is None:
            from apps.comptabilite.models import Compte

            comptes = {champ: Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]
                       for champ, (numero, intitule) in cls.COMPTES.items()}
            fiche = cls.objects.create(**comptes)
        return fiche


def _ventiler(montant_ttc, compte_produit, taxe, sens_credit=True):
    """Lignes produit (+ taxe) d'un montant encaissé toutes taxes comprises."""
    if taxe is None or not taxe.taux:
        lignes = [{"compte": compte_produit, "montant": montant_ttc}]
    else:
        ht = _arrondi(montant_ttc * 100 / (100 + taxe.taux))
        lignes = [{"compte": compte_produit, "montant": ht}, {"compte": taxe.compte, "montant": montant_ttc - ht}]
    cle = "credit" if sens_credit else "debit"
    return [{"compte": l["compte"], cle: l["montant"]} for l in lignes]


def _caisse_par_defaut():
    from apps.comptabilite.models import Journal

    return Journal.objects.filter(code="CA").first()


class Gare(models.Model):
    """Gare routière / point de vente de l'agence (une ville peut avoir plusieurs gares)."""

    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    ville = models.CharField(max_length=80)
    agence = models.ForeignKey("core.Agence", null=True, blank=True, on_delete=models.PROTECT, related_name="gares",
                               help_text="Agence (dossier) dont dépend la gare, si la société en a plusieurs")
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"},
                               help_text="Journal de caisse de la gare (vide : caisse principale CA)")
    section = models.ForeignKey("comptabilite.SectionAnalytique", null=True, blank=True, on_delete=models.PROTECT,
                                related_name="+", help_text="Section analytique de la gare (créée automatiquement)")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["ville", "nom"]

    def __str__(self):
        return f"{self.code} - {self.nom}"

    def save(self, *args, **kwargs):
        if not self.section_id:
            from apps.comptabilite.models import SectionAnalytique

            self.section = SectionAnalytique.objects.get_or_create(
                code=f"G-{self.code}"[:20], defaults={"plan": "Gares", "intitule": f"Gare {self.nom}"[:100]})[0]
        super().save(*args, **kwargs)

    def journal_caisse(self):
        return self.caisse or _caisse_par_defaut()


class Ligne(models.Model):
    """Ligne régulière (trajet) entre deux gares, avec ses tarifs."""

    code = models.CharField(max_length=20, unique=True)
    gare_depart = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="lignes_depart", verbose_name="Gare de départ")
    gare_arrivee = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="lignes_arrivee", verbose_name="Gare d'arrivée")
    distance_km = models.PositiveIntegerField("Distance (km)", null=True, blank=True)
    duree = models.CharField("Durée du trajet", max_length=20, blank=True, help_text="Ex. 4 h 30")
    prix_billet = models.DecimalField("Prix du billet", max_digits=12, decimal_places=0)
    colis_forfait = models.DecimalField("Colis : forfait", max_digits=12, decimal_places=0, default=ZERO,
                                        help_text="Prix minimum d'un colis sur cette ligne")
    colis_prix_kg = models.DecimalField("Colis : prix par kg", max_digits=12, decimal_places=0, default=ZERO)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.gare_depart.ville} → {self.gare_arrivee.ville})"

    def clean(self):
        if self.gare_depart_id and self.gare_depart_id == self.gare_arrivee_id:
            raise ValidationError("La gare d'arrivée doit être différente de la gare de départ.")

    def prix_colis(self, poids):
        return max(self.colis_forfait, _arrondi(Decimal(poids or 0) * self.colis_prix_kg))


class Vehicule(models.Model):
    CAR, MINIBUS, CAMION, AUTRE = "CAR", "MINIBUS", "CAMION", "AUTRE"
    TYPES = [(CAR, "Car / autocar"), (MINIBUS, "Minibus"), (CAMION, "Camion (fret)"), (AUTRE, "Autre")]

    immatriculation = models.CharField(max_length=20, unique=True)
    designation = models.CharField("Désignation", max_length=100, blank=True, help_text="Marque, modèle, n° de parc")
    type_vehicule = models.CharField("Type", max_length=10, choices=TYPES, default=CAR)
    nombre_places = models.PositiveIntegerField("Places voyageurs", default=0)
    section = models.ForeignKey("comptabilite.SectionAnalytique", null=True, blank=True, on_delete=models.PROTECT,
                                related_name="+", help_text="Section analytique du véhicule (créée automatiquement)")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["immatriculation"]
        verbose_name = "Véhicule"

    def __str__(self):
        return f"{self.immatriculation}{f' - {self.designation}' if self.designation else ''}"

    def save(self, *args, **kwargs):
        if not self.section_id:
            from apps.comptabilite.models import SectionAnalytique

            self.section = SectionAnalytique.objects.get_or_create(
                code=f"V-{self.immatriculation}"[:20], defaults={"plan": "Véhicules", "intitule": f"Véhicule {self}"[:100]})[0]
        super().save(*args, **kwargs)


class Chauffeur(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    permis = models.CharField("N° de permis", max_length=40, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Depart(models.Model):
    """Un voyage programmé : ligne, date et heure, véhicule, chauffeur. Porte les billets et les colis chargés."""

    PROGRAMME, PARTI, ARRIVE, ANNULE = "PROGRAMME", "PARTI", "ARRIVE", "ANNULE"
    STATUTS = [(PROGRAMME, "Programmé"), (PARTI, "Parti"), (ARRIVE, "Arrivé"), (ANNULE, "Annulé")]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    ligne = models.ForeignKey(Ligne, on_delete=models.PROTECT, related_name="departs")
    date = models.DateField(default=timezone.localdate)
    heure = models.TimeField()
    vehicule = models.ForeignKey(Vehicule, null=True, blank=True, on_delete=models.PROTECT, related_name="departs",
                                 verbose_name="Véhicule")
    chauffeur = models.ForeignKey(Chauffeur, null=True, blank=True, on_delete=models.PROTECT, related_name="departs")
    places = models.PositiveIntegerField("Places à vendre", default=0, help_text="0 : places du véhicule")
    statut = models.CharField(max_length=10, choices=STATUTS, default=PROGRAMME)
    parti_le = models.DateTimeField(null=True, blank=True)
    arrive_le = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-heure"]
        verbose_name = "Départ"

    def __str__(self):
        return f"{self.numero} {self.ligne.code} {self.date:%d/%m/%Y} {self.heure:%H:%M}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = Sequence.suivant("DEP", self.date.year)
        if not self.places and self.vehicule_id:
            self.places = self.vehicule.nombre_places
        super().save(*args, **kwargs)

    @property
    def billets_actifs(self):
        return self.billets.exclude(statut=Billet.ANNULE)

    @property
    def places_vendues(self):
        return self.billets_actifs.count()

    @property
    def places_libres(self):
        return max(self.places - self.places_vendues, 0)

    def sieges_occupes(self):
        return set(self.billets_actifs.exclude(siege=None).values_list("siege", flat=True))

    def recette_billets(self):
        return sum((b.prix for b in self.billets_actifs), ZERO)

    def recette_colis(self):
        return sum((c.prix for c in self.colis.exclude(statut=Colis.ANNULE)), ZERO)

    def depenses(self):
        return sum((d.montant for d in self.depenses_vehicule.all()), ZERO)

    def ouvert_a_la_vente(self):
        if self.statut != self.PROGRAMME:
            raise ValidationError(f"Le départ {self.numero} est {self.get_statut_display().lower()} : vente impossible.")

    @transaction.atomic
    def partir(self):
        if self.statut != self.PROGRAMME:
            raise ValidationError("Seul un départ programmé peut partir.")
        if not self.vehicule_id or not self.chauffeur_id:
            raise ValidationError("Indiquez le véhicule et le chauffeur avant le départ.")
        self.statut, self.parti_le = self.PARTI, timezone.now()
        self.save(update_fields=["statut", "parti_le"])
        self.billets.filter(statut=Billet.VENDU).update(statut=Billet.EMBARQUE)
        self.colis.filter(statut=Colis.CHARGE).update(statut=Colis.EN_ROUTE)

    @transaction.atomic
    def arriver(self):
        if self.statut != self.PARTI:
            raise ValidationError("Seul un départ parti peut arriver.")
        self.statut, self.arrive_le = self.ARRIVE, timezone.now()
        self.save(update_fields=["statut", "arrive_le"])
        self.colis.filter(statut=Colis.EN_ROUTE).update(statut=Colis.ARRIVE)

    @transaction.atomic
    def annuler(self):
        if self.statut != self.PROGRAMME:
            raise ValidationError("Seul un départ programmé peut être annulé.")
        if self.billets_actifs.exists():
            raise ValidationError("Des billets sont vendus sur ce départ : reportez-les ou annulez-les d'abord.")
        self.colis.filter(statut=Colis.CHARGE).update(statut=Colis.ENREGISTRE, depart=None)
        self.statut = self.ANNULE
        self.save(update_fields=["statut"])


class Billet(models.Model):
    VENDU, EMBARQUE, ANNULE = "VENDU", "EMBARQUE", "ANNULE"
    STATUTS = [(VENDU, "Vendu"), (EMBARQUE, "Embarqué"), (ANNULE, "Annulé")]
    ESPECES, MOBILE_MONEY, COMPTE = "ESPECES", "MOBILE_MONEY", "COMPTE"
    PAIEMENTS = [(ESPECES, "Espèces"), (MOBILE_MONEY, "Mobile Money"), (COMPTE, "En compte (client)")]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    date_vente = models.DateField(default=timezone.localdate)
    gare = models.ForeignKey(Gare, null=True, blank=True, on_delete=models.PROTECT, related_name="billets",
                             verbose_name="Gare de vente", help_text="Vide : gare de départ de la ligne")
    depart = models.ForeignKey(Depart, on_delete=models.PROTECT, related_name="billets", verbose_name="Départ")
    voyageur = models.CharField(max_length=120)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    piece_identite = models.CharField("Pièce d'identité", max_length=40, blank=True)
    siege = models.PositiveIntegerField("Siège", null=True, blank=True)
    prix = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                               help_text="Vide : prix de la ligne")
    paiement = models.CharField(max_length=15, choices=PAIEMENTS, default=ESPECES)
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    client = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="billets",
                               help_text="Entreprise ou organisme qui paie en compte")
    statut = models.CharField(max_length=10, choices=STATUTS, default=VENDU)
    retenue = models.DecimalField("Retenue d'annulation", max_digits=12, decimal_places=0, default=ZERO)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_annulation = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                               related_name="+")
    vendu_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)
    annule_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    annule_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_vente", "-numero"]

    def __str__(self):
        return f"{self.numero} {self.voyageur}"

    def _contrepartie(self):
        """Ligne de trésorerie ou de client du billet (montant à placer par l'appelant)."""
        if self.paiement == self.COMPTE:
            return {"compte": self.client.get_compte_collectif(), "tiers": self.client}
        return {"compte": self.caisse.compte_tresorerie}

    def _journal(self):
        from apps.comptabilite.models import Journal

        return Journal.objects.get(code="VT") if self.paiement == self.COMPTE else self.caisse

    @transaction.atomic
    def vendre(self, utilisateur=None):
        """Contrôle, numérote et comptabilise la vente."""
        from apps.comptabilite.services import creer_ecriture

        depart = Depart.objects.select_for_update().get(pk=self.depart_id)
        depart.ouvert_a_la_vente()
        if not self.gare_id:
            self.gare = depart.ligne.gare_depart
        if self.paiement == self.COMPTE and not self.client_id:
            raise ValidationError("Choisissez le client qui paie en compte.")
        if self.paiement == self.COMPTE and not self.client.vente_credit:
            raise ValidationError(f"Le client {self.client} est au comptant : vente en compte impossible.")
        if self.paiement != self.COMPTE:
            self.caisse = self.caisse or self.gare.journal_caisse()
            if not self.caisse or not self.caisse.compte_tresorerie_id:
                raise ValidationError("La caisse de la gare n'a pas de compte de trésorerie.")
        if self.prix is None:
            self.prix = depart.ligne.prix_billet
        if self.prix < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")
        if depart.places and depart.places_libres <= 0:
            raise ValidationError(f"Le départ {depart.numero} est complet ({depart.places} places).")
        if self.siege is not None:
            if depart.places and not 1 <= self.siege <= depart.places:
                raise ValidationError(f"Siège {self.siege} inexistant (1 à {depart.places}).")
            if self.siege in depart.sieges_occupes():
                raise ValidationError(f"Le siège {self.siege} est déjà vendu sur ce départ.")
        self.vendu_par = self.vendu_par or utilisateur
        self.numero = self.numero or Sequence.suivant("BIL", self.date_vente.year, largeur=6)
        self.save()
        if self.prix:
            parametres = ParametresTransport.get()
            libelle = f"Billet {self.numero} {depart.ligne.code} {depart.date:%d/%m} - {self.voyageur}"
            lignes = [{**self._contrepartie(), "debit": self.prix},
                      *[{**l, "section": self.gare.section} for l in _ventiler(self.prix, parametres.compte_billets, parametres.taxe_billets)]]
            self.ecriture = creer_ecriture(self._journal(), self.date_vente, libelle, lignes, reference=self.numero,
                                           origine=self.numero)
            self.save(update_fields=["ecriture"])
        return self

    @transaction.atomic
    def reporter(self, nouveau_depart, siege=None):
        """Change de départ (même ligne), sans écriture : le prix déjà payé reste acquis."""
        if self.statut != self.VENDU:
            raise ValidationError("Seul un billet vendu (non embarqué, non annulé) peut être reporté.")
        nouveau = Depart.objects.select_for_update().get(pk=nouveau_depart.pk)
        nouveau.ouvert_a_la_vente()
        if nouveau.ligne_id != self.depart.ligne_id:
            raise ValidationError("Le report se fait sur un départ de la même ligne.")
        if nouveau.places and nouveau.places_libres <= 0:
            raise ValidationError(f"Le départ {nouveau.numero} est complet.")
        if siege is not None and siege in nouveau.sieges_occupes():
            raise ValidationError(f"Le siège {siege} est déjà vendu sur ce départ.")
        self.depart, self.siege = nouveau, siege
        self.save(update_fields=["depart", "siege"])
        return self

    @transaction.atomic
    def annuler(self, retenue=None, utilisateur=None, date=None):
        """Annule le billet : rembourse le prix moins la retenue (qui reste un produit de l'agence)."""
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.VENDU:
            raise ValidationError("Seul un billet vendu (non embarqué) peut être annulé.")
        parametres = ParametresTransport.get()
        if retenue is None:
            retenue = _arrondi(self.prix * parametres.retenue_annulation / 100)
        retenue = Decimal(retenue)
        if not ZERO <= retenue <= self.prix:
            raise ValidationError("La retenue doit être comprise entre 0 et le prix du billet.")
        rembourse = self.prix - retenue
        date = date or timezone.localdate()
        if rembourse:
            libelle = f"Annulation billet {self.numero} - {self.voyageur} (retenue {retenue})"
            lignes = [*[{**l, "section": self.gare.section} for l in _ventiler(rembourse, parametres.compte_billets,
                                                                            parametres.taxe_billets, sens_credit=False)],
                      {**self._contrepartie(), "credit": rembourse}]
            self.ecriture_annulation = creer_ecriture(self._journal(), date, libelle, lignes, reference=self.numero,
                                                      origine=self.numero)
        self.statut, self.retenue, self.annule_par, self.annule_le = self.ANNULE, retenue, utilisateur, timezone.now()
        self.save(update_fields=["statut", "retenue", "annule_par", "annule_le", "ecriture_annulation"])
        return self

    @property
    def rembourse(self):
        return self.prix - self.retenue if self.statut == self.ANNULE else ZERO


class Colis(models.Model):
    """Colis, courrier ou fret confié à l'agence entre deux gares."""

    COLIS, COURRIER, FRET = "COLIS", "COURRIER", "FRET"
    NATURES = [(COLIS, "Colis"), (COURRIER, "Courrier"), (FRET, "Fret / marchandises")]
    PAYE, DU = "PAYE", "DU"
    PORTS = [(PAYE, "Port payé (par l'expéditeur au départ)"), (DU, "Port dû (par le destinataire à l'arrivée)")]
    ENREGISTRE, CHARGE, EN_ROUTE, ARRIVE, LIVRE, ANNULE = "ENREGISTRE", "CHARGE", "EN_ROUTE", "ARRIVE", "LIVRE", "ANNULE"
    STATUTS = [(ENREGISTRE, "Enregistré"), (CHARGE, "Chargé"), (EN_ROUTE, "En route"), (ARRIVE, "Arrivé"),
               (LIVRE, "Livré"), (ANNULE, "Annulé")]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    nature = models.CharField(max_length=10, choices=NATURES, default=COLIS)
    date = models.DateField(default=timezone.localdate)
    gare_depart = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="colis_expedies", verbose_name="Gare de départ")
    gare_arrivee = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="colis_recus", verbose_name="Gare d'arrivée")
    expediteur = models.CharField("Expéditeur", max_length=120)
    tel_expediteur = models.CharField("Téléphone expéditeur", max_length=30, blank=True)
    destinataire = models.CharField(max_length=120)
    tel_destinataire = models.CharField("Téléphone destinataire", max_length=30, blank=True)
    description = models.CharField("Contenu", max_length=200, blank=True)
    nombre = models.PositiveIntegerField("Nombre de pièces", default=1)
    poids = models.DecimalField("Poids (kg)", max_digits=10, decimal_places=2, default=ZERO)
    valeur_declaree = models.DecimalField("Valeur déclarée", max_digits=14, decimal_places=0, default=ZERO)
    prix = models.DecimalField("Prix du transport", max_digits=12, decimal_places=0, null=True, blank=True,
                               help_text="Vide : tarif de la ligne (forfait ou prix au kg)")
    port = models.CharField(max_length=5, choices=PORTS, default=PAYE)
    contre_remboursement = models.DecimalField(
        "Contre-remboursement", max_digits=14, decimal_places=0, default=ZERO,
        help_text="Somme à encaisser auprès du destinataire pour le compte de l'expéditeur")
    client = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT, related_name="colis",
                               help_text="Expéditeur en compte (entreprise) : le port payé est porté sur son compte")
    depart = models.ForeignKey(Depart, null=True, blank=True, on_delete=models.PROTECT, related_name="colis",
                               verbose_name="Chargé sur le départ")
    statut = models.CharField(max_length=10, choices=STATUTS, default=ENREGISTRE)
    code_retrait = models.CharField("Code de retrait", max_length=6, blank=True)
    livre_le = models.DateTimeField(null=True, blank=True)
    retire_par = models.CharField("Retiré par (nom, pièce)", max_length=150, blank=True)
    cr_reverse_le = models.DateTimeField("Contre-remboursement reversé le", null=True, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_livraison = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                              related_name="+")
    ecriture_reversement = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                                related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_le = models.DateTimeField(auto_now_add=True)
    livre_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Colis / courrier"
        verbose_name_plural = "Colis et courriers"

    def __str__(self):
        return f"{self.numero} {self.expediteur} → {self.destinataire}"

    def compte_produit(self, parametres):
        return parametres.compte_fret if self.nature == self.FRET else parametres.compte_colis

    def ligne(self):
        return Ligne.objects.filter(gare_depart=self.gare_depart, gare_arrivee=self.gare_arrivee, actif=True).first()

    @transaction.atomic
    def enregistrer(self, utilisateur=None):
        """Numérote, donne le code de retrait et comptabilise le port payé au départ."""
        from apps.comptabilite.services import creer_ecriture

        if self.gare_depart_id == self.gare_arrivee_id:
            raise ValidationError("La gare d'arrivée doit être différente de la gare de départ.")
        if self.prix is None:
            ligne = self.ligne()
            if ligne is None:
                raise ValidationError("Aucune ligne entre ces gares : indiquez le prix du transport.")
            self.prix = ligne.prix_colis(self.poids)
        if self.prix < 0 or self.contre_remboursement < 0:
            raise ValidationError("Les montants ne peuvent pas être négatifs.")
        if self.port == self.DU and self.client_id:
            raise ValidationError("Un envoi en compte client est en port payé.")
        self.cree_par = self.cree_par or utilisateur
        self.numero = self.numero or Sequence.suivant("COL", self.date.year, largeur=6)
        self.code_retrait = self.code_retrait or f"{secrets.randbelow(1000000):06d}"
        self.save()
        if self.port == self.PAYE and self.prix:
            parametres = ParametresTransport.get()
            from apps.comptabilite.models import Journal

            if self.client_id:
                journal, contrepartie = Journal.objects.get(code="VT"), {"compte": self.client.get_compte_collectif(), "tiers": self.client}
            else:
                journal = self.gare_depart.journal_caisse()
                contrepartie = {"compte": journal.compte_tresorerie}
            lignes = [{**contrepartie, "debit": self.prix},
                      *[{**l, "section": self.gare_depart.section}
                        for l in _ventiler(self.prix, self.compte_produit(parametres), parametres.taxe_colis)]]
            self.ecriture = creer_ecriture(journal, self.date, f"{self.get_nature_display()} {self.numero} - {self.expediteur}",
                                           lignes, reference=self.numero, origine=self.numero)
            self.save(update_fields=["ecriture"])
        return self

    @transaction.atomic
    def charger(self, depart):
        if self.statut != self.ENREGISTRE:
            raise ValidationError(f"Le colis {self.numero} est {self.get_statut_display().lower()} : chargement impossible.")
        if depart.statut != Depart.PROGRAMME:
            raise ValidationError("On ne charge que sur un départ programmé.")
        if (depart.ligne.gare_depart_id, depart.ligne.gare_arrivee_id) != (self.gare_depart_id, self.gare_arrivee_id):
            raise ValidationError(f"Le départ {depart.numero} ne va pas de {self.gare_depart.ville} à {self.gare_arrivee.ville}.")
        self.depart, self.statut = depart, self.CHARGE
        self.save(update_fields=["depart", "statut"])

    @property
    def a_encaisser(self):
        """Ce que le destinataire paie au retrait : port dû et contre-remboursement."""
        return (self.prix if self.port == self.DU else ZERO) + self.contre_remboursement

    @transaction.atomic
    def livrer(self, code, retire_par, utilisateur=None, date=None):
        """Remise au destinataire contre le code de retrait ; encaisse le port dû et le contre-remboursement."""
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.ARRIVE:
            raise ValidationError(f"Le colis {self.numero} n'est pas arrivé en gare ({self.get_statut_display().lower()}).")
        if (code or "").strip() != self.code_retrait:
            raise ValidationError("Code de retrait incorrect.")
        if not (retire_par or "").strip():
            raise ValidationError("Indiquez qui retire le colis (nom et pièce d'identité).")
        date = date or timezone.localdate()
        if self.a_encaisser:
            parametres = ParametresTransport.get()
            caisse = self.gare_arrivee.journal_caisse()
            lignes = [{"compte": caisse.compte_tresorerie, "debit": self.a_encaisser}]
            if self.port == self.DU and self.prix:
                lignes += [{**l, "section": self.gare_arrivee.section}
                           for l in _ventiler(self.prix, self.compte_produit(parametres), parametres.taxe_colis)]
            if self.contre_remboursement:
                lignes.append({"compte": parametres.compte_contre_remboursement, "credit": self.contre_remboursement,
                               "libelle": f"Contre-remboursement {self.numero} pour {self.expediteur}"})
            self.ecriture_livraison = creer_ecriture(caisse, date, f"Livraison {self.numero} - {self.destinataire}", lignes,
                                                     reference=self.numero, origine=self.numero)
        self.statut, self.livre_le, self.retire_par, self.livre_par = self.LIVRE, timezone.now(), retire_par.strip(), utilisateur
        self.save(update_fields=["statut", "livre_le", "retire_par", "livre_par", "ecriture_livraison"])
        return self

    @transaction.atomic
    def reverser_contre_remboursement(self, utilisateur=None, date=None):
        """Remet à l'expéditeur la somme encaissée auprès du destinataire."""
        from apps.comptabilite.services import creer_ecriture

        if not self.contre_remboursement:
            raise ValidationError("Cet envoi n'a pas de contre-remboursement.")
        if self.statut != self.LIVRE:
            raise ValidationError("Le contre-remboursement n'est reversé qu'après la livraison (somme encaissée).")
        if self.cr_reverse_le:
            raise ValidationError("Contre-remboursement déjà reversé.")
        parametres = ParametresTransport.get()
        caisse = self.gare_depart.journal_caisse()
        self.ecriture_reversement = creer_ecriture(
            caisse, date or timezone.localdate(), f"Reversement contre-remboursement {self.numero} - {self.expediteur}",
            [{"compte": parametres.compte_contre_remboursement, "debit": self.contre_remboursement},
             {"compte": caisse.compte_tresorerie, "credit": self.contre_remboursement}],
            reference=self.numero, origine=self.numero)
        self.cr_reverse_le = timezone.now()
        self.save(update_fields=["ecriture_reversement", "cr_reverse_le"])
        return self

    @transaction.atomic
    def annuler(self, utilisateur=None, date=None):
        """Annule un envoi non chargé : rembourse le port payé (écriture inverse)."""
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.ENREGISTRE:
            raise ValidationError("Seul un envoi enregistré (non chargé) peut être annulé.")
        if self.ecriture_id:
            lignes = [{"compte": l.compte, "tiers": l.tiers, "section": l.section, "debit": l.credit, "credit": l.debit}
                      for l in self.ecriture.lignes.all()]
            creer_ecriture(self.ecriture.journal, date or timezone.localdate(), f"Annulation {self.numero}", lignes,
                           reference=self.numero, origine=self.numero)
        self.statut = self.ANNULE
        self.save(update_fields=["statut"])


class DepenseVehicule(models.Model):
    """Dépense de la flotte payée en caisse : carburant, entretien, réparation, péage, frais de route…"""

    CARBURANT, ENTRETIEN, REPARATION, PEAGE, FRAIS_ROUTE, ASSURANCE, AUTRE = (
        "CARBURANT", "ENTRETIEN", "REPARATION", "PEAGE", "FRAIS_ROUTE", "ASSURANCE", "AUTRE")
    NATURES = [(CARBURANT, "Carburant"), (ENTRETIEN, "Entretien"), (REPARATION, "Réparation / pièces"),
               (PEAGE, "Péage, pesage"), (FRAIS_ROUTE, "Frais de route (chauffeur)"), (ASSURANCE, "Assurance, visite technique"),
               (AUTRE, "Autre")]
    # Compte proposé par nature (SYSCOHADA ; modifiable à la saisie)
    COMPTES = {CARBURANT: "6053", ENTRETIEN: "624", REPARATION: "624", ASSURANCE: "625"}

    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    vehicule = models.ForeignKey(Vehicule, on_delete=models.PROTECT, related_name="depenses", verbose_name="Véhicule")
    depart = models.ForeignKey(Depart, null=True, blank=True, on_delete=models.PROTECT, related_name="depenses_vehicule",
                               help_text="Voyage concerné (frais de route), pour la rentabilité par départ")
    nature = models.CharField(max_length=15, choices=NATURES, default=CARBURANT)
    libelle = models.CharField("Libellé", max_length=200, blank=True)
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    caisse = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    compte = models.ForeignKey("comptabilite.Compte", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               verbose_name="Compte de charge", help_text="Vide : compte proposé pour la nature")
    reference = models.CharField("Pièce justificative", max_length=60, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Dépense de véhicule"

    def __str__(self):
        return f"{self.numero} {self.vehicule.immatriculation} {self.get_nature_display()}"

    @transaction.atomic
    def enregistrer(self, utilisateur=None):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        if self.depart_id and self.depart.vehicule_id and self.depart.vehicule_id != self.vehicule_id:
            raise ValidationError("Ce départ a été fait avec un autre véhicule.")
        if not self.compte_id:
            numero = self.COMPTES.get(self.nature)
            self.compte = Compte.objects.filter(numero=numero).first() if numero else None
            if self.compte is None:
                raise ValidationError("Choisissez le compte de charge.")
        if not self.caisse.compte_tresorerie_id:
            raise ValidationError(f"Le journal {self.caisse.code} n'a pas de compte de trésorerie.")
        self.cree_par = self.cree_par or utilisateur
        self.numero = self.numero or Sequence.suivant("DV", self.date.year)
        self.save()
        libelle = self.libelle or f"{self.get_nature_display()} {self.vehicule.immatriculation}"
        self.ecriture = creer_ecriture(self.caisse, self.date, libelle,
                                       [{"compte": self.compte, "section": self.vehicule.section, "debit": self.montant},
                                        {"compte": self.caisse.compte_tresorerie, "credit": self.montant}],
                                       reference=self.reference or self.numero, origine=self.numero)
        self.save(update_fields=["ecriture"])
        return self
