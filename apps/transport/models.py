"""Transport interurbain de voyageurs : billetterie, colis et courrier, fret, flotte — liés à la comptabilité OHADA.

Schémas comptables (comptes réglables dans Paramètres transport, à valider par l'expert-comptable) :
  Billet vendu                  D caisse de la gare (ou 411)  / C 41911 Billets vendus, voyage à effectuer
  Départ du véhicule            D 41911 (part de chaque voyageur) / C 70611 Transport de voyageurs, sur le VÉHICULE
                                (+ C taxe si réglée) ; correspondance : chaque véhicule reçoit sa part du prix
  Tronçon fait par le véhicule d'une autre agence : chez elle D 185 agence vendeuse / C 70611 véhicule ;
                                chez l'agence vendeuse D 41911 / C 185 agence du véhicule
  Billet annulé avant le voyage D 41911 (prix)                / C caisse (remboursé) / C 70611 (retenue)
  Colis port payé               D caisse de la gare de départ / C 70612 Colis et courrier (70613 pour le fret)
  Colis port dû, à la livraison D caisse de la gare d'arrivée / C 70612
  Contre-remboursement encaissé D caisse                      / C 4718 Envois contre remboursement à reverser
  … reversé à l'expéditeur      D 4718                        / C caisse
  Dépense de véhicule           D 6xx (sur le véhicule)       / C caisse
"""
import secrets
import uuid
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
    compte_billets_a_voyager = models.ForeignKey(
        "comptabilite.Compte", null=True, on_delete=models.PROTECT, related_name="+",
        verbose_name="Billets vendus, voyage à effectuer",
        help_text="Encaissement d'avance du voyageur ; soldé au départ de chaque véhicule, qui reçoit sa part")
    compte_colis_a_transporter = models.ForeignKey(
        "comptabilite.Compte", null=True, on_delete=models.PROTECT, related_name="+",
        verbose_name="Envois encaissés, transport à effectuer",
        help_text="Port payé à l'expédition ; passé en recette du véhicule qui transporte l'envoi, à son départ")
    taxe_billets = models.ForeignKey("comptabilite.Taxe", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                     verbose_name="Taxe sur les billets", help_text="Vide : aucune taxe (réglage par défaut)")
    taxe_colis = models.ForeignKey("comptabilite.Taxe", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                   verbose_name="Taxe sur les colis et le fret", help_text="Vide : aucune taxe (réglage par défaut)")
    compte_carburant = models.ForeignKey("comptabilite.Compte", null=True, on_delete=models.PROTECT, related_name="+",
                                         verbose_name="Garage : carburant")
    compte_pieces = models.ForeignKey("comptabilite.Compte", null=True, on_delete=models.PROTECT, related_name="+",
                                      verbose_name="Garage : pièces et fournitures")
    compte_main_oeuvre = models.ForeignKey("comptabilite.Compte", null=True, on_delete=models.PROTECT, related_name="+",
                                           verbose_name="Garage : main d'œuvre extérieure")
    retenue_annulation = models.DecimalField(
        "Retenue sur billet annulé (%)", max_digits=5, decimal_places=2, default=ZERO,
        help_text="Part du prix gardée par l'agence quand un voyageur annule (modifiable à chaque annulation)")

    class Meta:
        verbose_name = "Paramètres transport"

    COMPTES = {"compte_billets": ("70611", "Transport de voyageurs (billets)"),
               "compte_colis": ("70612", "Colis et courrier"),
               "compte_fret": ("70613", "Fret et logistique"),
               "compte_contre_remboursement": ("4718", "Envois contre remboursement à reverser"),
               "compte_billets_a_voyager": ("41911", "Billets vendus, voyage à effectuer"),
               "compte_colis_a_transporter": ("41912", "Envois encaissés, transport à effectuer"),
               "compte_carburant": ("6053", "Fournitures non stockables - Autres énergies"),
               "compte_pieces": ("624", "Entretien, réparations et maintenance"),
               "compte_main_oeuvre": ("624", "Entretien, réparations et maintenance")}

    @classmethod
    def get(cls):
        from apps.comptabilite.models import Compte

        def compte(champ):
            numero, intitule = cls.COMPTES[champ]
            return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]

        fiche = cls.objects.first()
        if fiche is None:
            fiche = cls.objects.create(**{champ: compte(champ) for champ in cls.COMPTES})
        else:                                                # fiche antérieure : comptes ajoutés depuis
            manquants = [champ for champ in cls.COMPTES if not getattr(fiche, f"{champ}_id")]
            for champ in manquants:
                setattr(fiche, champ, compte(champ))
            if manquants:
                fiche.save(update_fields=manquants)
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


def _site_local():
    from apps.echanges.publication import site_local

    return site_local()


def _proprietaire(objet, quoi):
    """Une copie reçue d'un autre site ne se modifie que dans son site d'origine."""
    if objet.site_origine:
        raise ValidationError(f"{quoi} appartient à l'agence {objet.site_origine} : seule cette agence peut le modifier.")


def _gare_ici(gare):
    """La gare est-elle tenue par ce dossier ? (sans échanges entre sites : toutes les gares le sont)"""
    local = _site_local()
    return local is None or gare.agence_id is None or gare.agence_id == local.pk


def _compte_liaison(code_site):
    from apps.core.models import Agence

    agence = Agence.objects.filter(code=code_site).first()
    if agence is None or not agence.compte_liaison_id:
        raise ValidationError(f"Agence {code_site} inconnue ou sans compte de liaison : recevez d'abord les lots du siège.")
    return agence.compte_liaison


def _caisse_par_defaut():
    from apps.comptabilite.models import Journal

    return Journal.objects.filter(code="CA").first()


class Gare(models.Model):
    """Gare routière / point de vente de l'agence (une ville peut avoir plusieurs gares)."""

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    ville = models.CharField(max_length=80)
    agence = models.ForeignKey("core.Agence", null=True, blank=True, on_delete=models.PROTECT, related_name="gares",
                               help_text="Agence (dossier) dont dépend la gare, si la société en a plusieurs")
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"},
                               help_text="Journal de caisse de la gare (vide : caisse principale CA)")
    mobile_money = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                     limit_choices_to={"type_journal": "TRESORERIE"}, verbose_name="Journal Mobile Money",
                                     help_text="Encaissements Mobile Money de la gare (vide : journal MM)")
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

    def journal_mobile_money(self):
        from apps.comptabilite.models import Journal

        return self.mobile_money or Journal.objects.filter(code="MM").first() or self.journal_caisse()


class Ligne(models.Model):
    """Ligne régulière (trajet) entre deux gares, avec ses tarifs."""

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
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
    """Fiche du véhicule : c'est aussi un compte (recettes et dépenses portées sur les lignes d'écriture)."""

    CAR, MINIBUS, CAMION, AUTRE = "CAR", "MINIBUS", "CAMION", "AUTRE"
    TYPES = [(CAR, "Car / autocar"), (MINIBUS, "Minibus"), (CAMION, "Camion (fret)"), (AUTRE, "Autre")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
    immatriculation = models.CharField(max_length=20, unique=True)
    designation = models.CharField("Désignation", max_length=100, blank=True, help_text="Marque, modèle, n° de parc")
    type_vehicule = models.CharField("Type", max_length=10, choices=TYPES, default=CAR)
    nombre_places = models.PositiveIntegerField("Places voyageurs", default=0)
    proprietaire = models.ForeignKey("commercial.Tiers", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="vehicules", verbose_name="Propriétaire",
                                     help_text="Vide : véhicule de la société ; sinon le partenaire qui le met à disposition")
    carte_grise = models.CharField("N° de carte grise", max_length=40, blank=True)
    mise_en_service = models.DateField("Mise en service", null=True, blank=True)
    assurance_echeance = models.DateField("Assurance valable jusqu'au", null=True, blank=True)
    visite_technique_echeance = models.DateField("Visite technique valable jusqu'au", null=True, blank=True)
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

    def alertes(self, jour=None):
        """Papiers expirés ou à renouveler dans les 30 jours."""
        import datetime

        jour = jour or timezone.localdate()
        resultat = []
        for libelle, echeance in (("Assurance", self.assurance_echeance), ("Visite technique", self.visite_technique_echeance)):
            if echeance and echeance < jour:
                resultat.append(f"{libelle} expirée depuis le {echeance:%d/%m/%Y}")
            elif echeance and echeance <= jour + datetime.timedelta(days=30):
                resultat.append(f"{libelle} à renouveler avant le {echeance:%d/%m/%Y}")
        return resultat


class Chauffeur(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
    nom = models.CharField(max_length=100)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    permis = models.CharField("N° de permis", max_length=40, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Depart(models.Model):
    """Un voyage programmé : ligne, date et heure, véhicule, chauffeur. Porte les tronçons de billets et les colis."""

    PROGRAMME, PARTI, ARRIVE, ANNULE = "PROGRAMME", "PARTI", "ARRIVE", "ANNULE"
    STATUTS = [(PROGRAMME, "Programmé"), (PARTI, "Parti"), (ARRIVE, "Arrivé"), (ANNULE, "Annulé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
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
    ecriture_recettes = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                             related_name="+", help_text="Recettes constatées au départ, sur le véhicule")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-heure"]
        verbose_name = "Départ"

    def __str__(self):
        return f"{self.numero} {self.ligne.code} {self.date:%d/%m/%Y} {self.heure:%H:%M}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = Sequence.piece("DEP", self.date.year)
        if not self.places and self.vehicule_id:
            self.places = self.vehicule.nombre_places
        super().save(*args, **kwargs)

    @property
    def voyageurs(self):
        """Tronçons de billets voyageant sur ce départ (billets directs et correspondances)."""
        return self.troncons.exclude(statut=Troncon.ANNULE)

    @property
    def billets_actifs(self):
        return self.voyageurs

    @property
    def places_vendues(self):
        return self.voyageurs.count()

    @property
    def places_libres(self):
        return max(self.places - self.places_vendues, 0)

    def sieges_occupes(self):
        return set(self.voyageurs.exclude(siege=None).values_list("siege", flat=True))

    def recette_billets(self):
        """Part des billets qui revient à ce départ (donc à son véhicule)."""
        return sum((t.part for t in self.voyageurs), ZERO)

    def recette_colis(self):
        return sum((c.prix for c in self.colis.exclude(statut=Colis.ANNULE)), ZERO)

    def depenses(self):
        return sum((d.montant for d in self.depenses_vehicule.all()), ZERO)

    def correspondances_a_affecter(self):
        """Voyageurs en correspondance qui attendent un véhicule pour ce trajet."""
        return Troncon.objects.filter(depart__isnull=True, statut=Troncon.A_VOYAGER, gare_depart=self.ligne.gare_depart,
                                      gare_arrivee=self.ligne.gare_arrivee).select_related("billet")

    def ouvert_a_la_vente(self):
        _proprietaire(self, f"Le départ {self.numero}")
        if self.statut != self.PROGRAMME:
            raise ValidationError(f"Le départ {self.numero} est {self.get_statut_display().lower()} : vente impossible.")

    @transaction.atomic
    def partir(self):
        """Le car part : la part de chaque voyageur devient une recette de CE véhicule (D billets à voyager / C produit)."""
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        _proprietaire(self, f"Le départ {self.numero}")
        if self.statut != self.PROGRAMME:
            raise ValidationError("Seul un départ programmé peut partir.")
        if not self.vehicule_id or not self.chauffeur_id:
            raise ValidationError("Indiquez le véhicule et le chauffeur avant le départ.")
        self.statut, self.parti_le = self.PARTI, timezone.now()
        self.save(update_fields=["statut", "parti_le"])
        troncons = list(self.troncons.filter(statut=Troncon.A_VOYAGER).select_related("billet"))
        envois = list(self.colis.filter(statut=Colis.CHARGE, port=Colis.PAYE, recette_constatee=False, ecriture__isnull=False))
        local = _site_local()
        parametres = ParametresTransport.get()
        debits, lignes = {}, []
        for t in troncons:                             # billet vendu ailleurs : la somme est chez l'agence vendeuse
            compte = _compte_liaison(t.billet.site_origine) if t.billet.site_origine else parametres.compte_billets_a_voyager
            debits[compte] = debits.get(compte, ZERO) + t.part
        total_billets = sum((t.part for t in troncons), ZERO)
        if total_billets:
            lignes += [{**l, "vehicule": self.vehicule, "section": self.ligne.gare_depart.section}
                       for l in _ventiler(total_billets, parametres.compte_billets, parametres.taxe_billets)]
        for c in envois:                               # port payé à l'expédition : recette du véhicule qui transporte
            debits[parametres.compte_colis_a_transporter] = debits.get(parametres.compte_colis_a_transporter, ZERO) + c.prix
            lignes += [{**l, "vehicule": self.vehicule, "section": self.ligne.gare_depart.section}
                       for l in _ventiler(c.prix, c.compte_produit(parametres), parametres.taxe_colis)]
        if lignes:
            self.ecriture_recettes = creer_ecriture(
                Journal.objects.get(code="OD"), timezone.localdate(),
                f"Recettes du départ {self.numero} {self.ligne.code} - {self.vehicule.immatriculation}",
                [{"compte": c, "debit": m} for c, m in debits.items()] + lignes, reference=self.numero, origine=self.numero)
            self.save(update_fields=["ecriture_recettes"])
        Colis.objects.filter(pk__in=[c.pk for c in envois]).update(recette_constatee=True)
        if troncons:
            for t in troncons:
                t.statut, t.vehicule, t.effectue_le = Troncon.EFFECTUE, self.vehicule, self.parti_le
                t.site_effectue = local.code if local is not None and t.site_origine else ""
                t.save(update_fields=["statut", "vehicule", "effectue_le", "site_effectue"])
                if t.site_origine:                     # l'agence vendeuse soldera son « billet à voyager »
                    from apps.echanges.publication import publier

                    publier("troncon_effectue", t.uid, {"v": 1, "troncon": str(t.uid), "depart": str(self.uid),
                                                        "vehicule": str(self.vehicule.uid), "part": str(t.part),
                                                        "site": t.site_effectue, "date": timezone.localdate().isoformat()},
                            "EFFECTUE", timezone.localdate())
            Billet.objects.filter(troncons__in=troncons, statut=Billet.VENDU).update(statut=Billet.EMBARQUE)
        self.colis.filter(statut=Colis.CHARGE).update(statut=Colis.EN_ROUTE)

    @transaction.atomic
    def arriver(self):
        """Arrivée en gare : faite par l'agence de départ ou par celle d'arrivée (qui reçoit les colis)."""
        if self.statut != self.PARTI:
            raise ValidationError("Seul un départ parti peut arriver.")
        if self.site_origine and not _gare_ici(self.ligne.gare_arrivee):
            raise ValidationError("L'arrivée se constate dans la gare d'arrivée.")
        self.statut, self.arrive_le = self.ARRIVE, timezone.now()
        self.save(update_fields=["statut", "arrive_le"])
        self.colis.filter(statut=Colis.EN_ROUTE).update(statut=Colis.ARRIVE)
        if self.site_origine:                              # copie : l'agence de départ l'apprendra par le siège
            from apps.echanges.publication import publier

            publier("depart_arrivee", self.uid, {"v": 1, "depart": str(self.uid), "arrive_le": self.arrive_le.isoformat()},
                    "ARRIVE", self.date)

    @transaction.atomic
    def annuler(self):
        _proprietaire(self, f"Le départ {self.numero}")
        if self.statut != self.PROGRAMME:
            raise ValidationError("Seul un départ programmé peut être annulé.")
        if self.voyageurs.exists():
            raise ValidationError("Des voyageurs sont prévus sur ce départ : reportez-les ou annulez leurs billets d'abord.")
        self.colis.filter(statut=Colis.CHARGE).update(statut=Colis.ENREGISTRE, depart=None)
        self.statut = self.ANNULE
        self.save(update_fields=["statut"])


def _tarif(gare_depart, gare_arrivee):
    return Ligne.objects.filter(gare_depart=gare_depart, gare_arrivee=gare_arrivee, actif=True).first()


class Billet(models.Model):
    """Billet d'un voyageur, de sa gare de départ à sa destination. Il comprend un tronçon par véhicule emprunté :
    un seul pour un trajet direct, deux s'il change de véhicule en route (correspondance)."""

    VENDU, EMBARQUE, ANNULE = "VENDU", "EMBARQUE", "ANNULE"
    STATUTS = [(VENDU, "Vendu"), (EMBARQUE, "Embarqué"), (ANNULE, "Annulé")]
    ESPECES, MOBILE_MONEY, COMPTE = "ESPECES", "MOBILE_MONEY", "COMPTE"
    PAIEMENTS = [(ESPECES, "Espèces"), (MOBILE_MONEY, "Mobile Money"), (COMPTE, "En compte (client)")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date_vente = models.DateField(default=timezone.localdate)
    gare = models.ForeignKey(Gare, null=True, blank=True, on_delete=models.PROTECT, related_name="billets",
                             verbose_name="Gare de vente", help_text="Vide : gare de départ de la ligne")
    depart = models.ForeignKey(Depart, on_delete=models.PROTECT, related_name="billets", verbose_name="Départ",
                               help_text="Premier véhicule emprunté")
    gare_arrivee = models.ForeignKey(Gare, null=True, blank=True, on_delete=models.PROTECT, related_name="billets_arrivee",
                                     verbose_name="Destination",
                                     help_text="Vide : terminus du départ ; plus loin : correspondance à la gare d'arrivée du départ")
    voyageur = models.CharField(max_length=120)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    piece_identite = models.CharField("Pièce d'identité", max_length=40, blank=True)
    siege = models.PositiveIntegerField("Siège", null=True, blank=True)
    prix = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                               help_text="Vide : tarif de la gare de départ à la destination")
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

    @property
    def destination(self):
        return self.gare_arrivee or self.depart.ligne.gare_arrivee

    def _contrepartie(self):
        """Ligne de trésorerie ou de client du billet (montant à placer par l'appelant)."""
        if self.paiement == self.COMPTE:
            return {"compte": self.client.get_compte_collectif(), "tiers": self.client}
        return {"compte": self.caisse.compte_tresorerie}

    def _journal(self):
        from apps.comptabilite.models import Journal

        return Journal.objects.get(code="VT") if self.paiement == self.COMPTE else self.caisse

    @transaction.atomic
    def vendre(self, utilisateur=None, depart_correspondance=None, siege_correspondance=None):
        """Contrôle, crée les tronçons, numérote et comptabilise l'encaissement en « billets vendus, voyage à
        effectuer » : la recette sera constatée au départ de chaque véhicule, pour sa part."""
        from apps.comptabilite.services import creer_ecriture

        depart = Depart.objects.select_for_update().get(pk=self.depart_id)
        depart.ouvert_a_la_vente()
        if not self.gare_id:
            self.gare = depart.ligne.gare_depart
        if self.paiement == self.COMPTE and not self.client_id:
            raise ValidationError("Choisissez le client qui paie en compte.")
        if self.paiement == self.COMPTE and not self.client.vente_credit:
            raise ValidationError(f"Le client {self.client} est au comptant : vente en compte impossible.")
        if self.paiement == self.MOBILE_MONEY and not self.caisse_id:
            self.caisse = self.gare.journal_mobile_money()      # pas dans la caisse espèces : compte de l'opérateur
        if self.paiement != self.COMPTE:
            self.caisse = self.caisse or self.gare.journal_caisse()
            if not self.caisse or not self.caisse.compte_tresorerie_id:
                raise ValidationError("La caisse de la gare n'a pas de compte de trésorerie.")
        origine, correspondance = depart.ligne.gare_depart, depart.ligne.gare_arrivee
        destination = self.gare_arrivee or correspondance
        if destination == origine:
            raise ValidationError("La destination doit être différente de la gare de départ.")
        segments = [(origine, correspondance, depart, self.siege)]
        if destination != correspondance:
            if depart_correspondance is not None:
                depart_correspondance = Depart.objects.select_for_update().get(pk=depart_correspondance.pk)
                depart_correspondance.ouvert_a_la_vente()
                if (depart_correspondance.ligne.gare_depart, depart_correspondance.ligne.gare_arrivee) != (correspondance, destination):
                    raise ValidationError(f"Le départ de correspondance doit aller de {correspondance.ville} à {destination.ville}.")
                if (depart_correspondance.date, depart_correspondance.heure) < (depart.date, depart.heure):
                    raise ValidationError("La correspondance part avant le premier véhicule.")
            segments.append((correspondance, destination, depart_correspondance, siege_correspondance))
        tarifs = [_tarif(a, b) for a, b, _, _ in segments]
        if self.prix is None:
            direct = _tarif(origine, destination)
            if direct is not None:
                self.prix = direct.prix_billet
            elif all(tarifs):
                self.prix = sum((t.prix_billet for t in tarifs), ZERO)
            else:
                raise ValidationError(f"Aucun tarif de {origine.ville} à {destination.ville} : indiquez le prix du billet.")
        if self.prix < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")
        for _, _, d, siege in segments:
            if d is None:
                continue
            if d.places and d.places_libres <= 0:
                raise ValidationError(f"Le départ {d.numero} est complet ({d.places} places).")
            if siege is not None:
                if d.places and not 1 <= siege <= d.places:
                    raise ValidationError(f"Siège {siege} inexistant sur le départ {d.numero} (1 à {d.places}).")
                if siege in d.sieges_occupes():
                    raise ValidationError(f"Le siège {siege} est déjà vendu sur le départ {d.numero}.")
        self.gare_arrivee = destination
        self.vendu_par = self.vendu_par or utilisateur
        self.numero = self.numero or Sequence.piece("BIL", self.date_vente.year, largeur=6)
        self.save()
        for ordre, ((a, b, d, siege), part) in enumerate(zip(segments, _parts(self.prix, segments, tarifs)), 1):
            Troncon.objects.create(billet=self, ordre=ordre, gare_depart=a, gare_arrivee=b, depart=d, siege=siege, part=part)
        from apps.echanges.publication import publier_objet

        publier_objet(self)                                 # billet complet, avec ses tronçons
        if self.prix:
            parametres = ParametresTransport.get()
            libelle = f"Billet {self.numero} {origine.ville} → {destination.ville} - {self.voyageur}"
            lignes = [{**self._contrepartie(), "debit": self.prix},
                      {"compte": parametres.compte_billets_a_voyager, "credit": self.prix, "section": self.gare.section}]
            self.ecriture = creer_ecriture(self._journal(), self.date_vente, libelle, lignes, reference=self.numero,
                                           origine=self.numero)
            self.save(update_fields=["ecriture"])
        return self

    @transaction.atomic
    def reporter(self, nouveau_depart, siege=None):
        """Change de départ le tronçon pas encore effectué qui correspond au trajet du nouveau départ (sans écriture)."""
        _proprietaire(self, f"Le billet {self.numero}")
        if self.statut == self.ANNULE:
            raise ValidationError("Billet annulé.")
        troncon = self.troncons.filter(statut=Troncon.A_VOYAGER, gare_depart=nouveau_depart.ligne.gare_depart,
                                       gare_arrivee=nouveau_depart.ligne.gare_arrivee).first()
        if troncon is None:
            raise ValidationError("Le report se fait sur un départ du même trajet, pas encore effectué.")
        troncon.affecter(nouveau_depart, siege)
        return self

    @transaction.atomic
    def annuler(self, retenue=None, utilisateur=None, date=None):
        """Annule le billet avant tout voyage : rembourse le prix moins la retenue (qui devient un produit)."""
        from apps.comptabilite.services import creer_ecriture

        _proprietaire(self, f"Le billet {self.numero}")
        if self.statut != self.VENDU or self.troncons.filter(statut=Troncon.EFFECTUE).exists():
            raise ValidationError("Seul un billet dont le voyage n'a pas commencé peut être annulé.")
        parametres = ParametresTransport.get()
        if retenue is None:
            retenue = _arrondi(self.prix * parametres.retenue_annulation / 100)
        retenue = Decimal(retenue)
        if not ZERO <= retenue <= self.prix:
            raise ValidationError("La retenue doit être comprise entre 0 et le prix du billet.")
        rembourse = self.prix - retenue
        date = date or timezone.localdate()
        if self.prix:
            libelle = f"Annulation billet {self.numero} - {self.voyageur} (retenue {retenue})"
            lignes = [{"compte": parametres.compte_billets_a_voyager, "debit": self.prix, "section": self.gare.section},
                      {**self._contrepartie(), "credit": rembourse},
                      *[{**l, "section": self.gare.section}
                        for l in _ventiler(retenue, parametres.compte_billets, parametres.taxe_billets)]]
            self.ecriture_annulation = creer_ecriture(self._journal(), date, libelle, lignes, reference=self.numero,
                                                      origine=self.numero)
        self.troncons.update(statut=Troncon.ANNULE)
        self.statut, self.retenue, self.annule_par, self.annule_le = self.ANNULE, retenue, utilisateur, timezone.now()
        self.save(update_fields=["statut", "retenue", "annule_par", "annule_le", "ecriture_annulation"])
        return self

    @property
    def rembourse(self):
        return self.prix - self.retenue if self.statut == self.ANNULE else ZERO


def _parts(prix, segments, tarifs):
    """Partage du prix entre les véhicules : au prorata des tarifs des tronçons, sinon des distances, sinon à parts
    égales ; le dernier tronçon reçoit l'arrondi."""
    if len(segments) == 1:
        return [prix]
    if all(tarifs) and sum(t.prix_billet for t in tarifs):
        poids = [t.prix_billet for t in tarifs]
    elif all(tarifs) and all(t.distance_km for t in tarifs):
        poids = [Decimal(t.distance_km) for t in tarifs]
    else:
        poids = [Decimal(1)] * len(segments)
    total = sum(poids)
    parts = [_arrondi(prix * p / total) for p in poids[:-1]]
    return parts + [prix - sum(parts, ZERO)]


class Troncon(models.Model):
    """Partie du trajet d'un billet faite par un même véhicule. Sa part du prix est la recette de ce véhicule."""

    A_VOYAGER, EFFECTUE, ANNULE = "A_VOYAGER", "EFFECTUE", "ANNULE"
    STATUTS = [(A_VOYAGER, "À voyager"), (EFFECTUE, "Effectué"), (ANNULE, "Annulé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False)
    billet = models.ForeignKey(Billet, on_delete=models.CASCADE, related_name="troncons")
    ordre = models.PositiveSmallIntegerField(default=1)
    gare_depart = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="+")
    gare_arrivee = models.ForeignKey(Gare, on_delete=models.PROTECT, related_name="+")
    depart = models.ForeignKey(Depart, null=True, blank=True, on_delete=models.PROTECT, related_name="troncons",
                               help_text="Vide : correspondance pas encore affectée à un véhicule")
    siege = models.PositiveIntegerField(null=True, blank=True)
    part = models.DecimalField("Part du prix", max_digits=12, decimal_places=0, default=ZERO)
    statut = models.CharField(max_length=10, choices=STATUTS, default=A_VOYAGER)
    vehicule = models.ForeignKey(Vehicule, null=True, blank=True, on_delete=models.PROTECT, related_name="troncons",
                                 help_text="Véhicule qui a fait le trajet (au départ)")
    effectue_le = models.DateTimeField(null=True, blank=True)
    site_effectue = models.CharField("Constaté par l'agence", max_length=10, blank=True)

    class Meta:
        ordering = ["billet", "ordre"]
        unique_together = [("billet", "ordre")]
        verbose_name = "Tronçon de billet"

    def __str__(self):
        return f"{self.billet.numero}/{self.ordre} {self.gare_depart.ville} → {self.gare_arrivee.ville}"

    @transaction.atomic
    def affecter(self, depart, siege=None):
        """Place le voyageur sur un départ du même trajet (report, ou correspondance dans la gare de changement)."""
        depart = Depart.objects.select_for_update().get(pk=depart.pk)
        depart.ouvert_a_la_vente()
        if self.statut != self.A_VOYAGER or self.billet.statut == Billet.ANNULE:
            raise ValidationError("Ce tronçon est déjà effectué ou annulé.")
        if self.billet.site_origine and not _gare_ici(self.gare_depart):
            raise ValidationError(f"Le billet {self.billet.numero} appartient à l'agence {self.billet.site_origine}.")
        if (depart.ligne.gare_depart_id, depart.ligne.gare_arrivee_id) != (self.gare_depart_id, self.gare_arrivee_id):
            raise ValidationError(f"Le départ {depart.numero} ne fait pas le trajet {self.gare_depart.ville} → {self.gare_arrivee.ville}.")
        if self.depart_id != depart.pk:
            if depart.places and depart.places_libres <= 0:
                raise ValidationError(f"Le départ {depart.numero} est complet.")
        if siege is not None and siege in depart.sieges_occupes() - ({self.siege} if self.depart_id == depart.pk else set()):
            raise ValidationError(f"Le siège {siege} est déjà vendu sur ce départ.")
        self.depart, self.siege = depart, siege
        self.save(update_fields=["depart", "siege"])
        if self.ordre == 1 and not self.billet.site_origine:
            Billet.objects.filter(pk=self.billet_id).update(depart=depart, siege=siege)
        if self.site_origine:                           # agence de correspondance : l'agence vendeuse est prévenue
            from apps.echanges.publication import publier

            publier("troncon_affecte", self.uid, {"v": 1, "troncon": str(self.uid), "depart": str(depart.uid),
                                                  "siege": siege}, "AFFECTE", depart.date)
        return self


class Colis(models.Model):
    """Colis, courrier ou fret confié à l'agence entre deux gares."""

    COLIS, COURRIER, FRET = "COLIS", "COURRIER", "FRET"
    NATURES = [(COLIS, "Colis"), (COURRIER, "Courrier"), (FRET, "Fret / marchandises")]
    PAYE, DU = "PAYE", "DU"
    PORTS = [(PAYE, "Port payé (par l'expéditeur au départ)"), (DU, "Port dû (par le destinataire à l'arrivée)")]
    ENREGISTRE, CHARGE, EN_ROUTE, ARRIVE, LIVRE, ANNULE = "ENREGISTRE", "CHARGE", "EN_ROUTE", "ARRIVE", "LIVRE", "ANNULE"
    STATUTS = [(ENREGISTRE, "Enregistré"), (CHARGE, "Chargé"), (EN_ROUTE, "En route"), (ARRIVE, "Arrivé"),
               (LIVRE, "Livré"), (ANNULE, "Annulé")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
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
    recette_constatee = models.BooleanField(
        default=False, editable=False, help_text="Port payé passé en recette du véhicule (au départ) ; port dû : à la remise")
    livre_site = models.CharField("Remis dans l'agence", max_length=10, blank=True,
                                  help_text="Agence qui a remis l'envoi, si ce n'est pas celle d'expédition")
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
        self.numero = self.numero or Sequence.piece("COL", self.date.year, largeur=6)
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
            # Encaissé d'avance : la recette ira au véhicule qui transporte l'envoi, à son départ
            lignes = [{**contrepartie, "debit": self.prix},
                      {"compte": parametres.compte_colis_a_transporter, "credit": self.prix, "section": self.gare_depart.section}]
            self.ecriture = creer_ecriture(journal, self.date, f"{self.get_nature_display()} {self.numero} - {self.expediteur}",
                                           lignes, reference=self.numero, origine=self.numero)
            self.save(update_fields=["ecriture"])
        else:
            Colis.objects.filter(pk=self.pk).update(recette_constatee=self.port == self.PAYE)     # gratuit : rien à constater
        return self

    @transaction.atomic
    def charger(self, depart):
        _proprietaire(self, f"L'envoi {self.numero}")
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
        if not _gare_ici(self.gare_arrivee):
            raise ValidationError(f"L'envoi se remet à {self.gare_arrivee.nom}, dans l'agence de destination.")
        date = date or timezone.localdate()
        if self.a_encaisser:
            parametres = ParametresTransport.get()
            caisse = self.gare_arrivee.journal_caisse()
            lignes = [{"compte": caisse.compte_tresorerie, "debit": self.a_encaisser}]
            if self.port == self.DU and self.prix:            # recette du véhicule qui l'a transporté
                vehicule = self.depart.vehicule if self.depart_id else None
                lignes += [{**l, "section": self.gare_arrivee.section, "vehicule": vehicule}
                           for l in _ventiler(self.prix, self.compte_produit(parametres), parametres.taxe_colis)]
            if self.contre_remboursement:
                # Envoi d'une autre agence : la somme est due à cette agence (qui la reverse à l'expéditeur)
                compte_cr = _compte_liaison(self.site_origine) if self.site_origine else parametres.compte_contre_remboursement
                lignes.append({"compte": compte_cr, "credit": self.contre_remboursement,
                               "libelle": f"Contre-remboursement {self.numero} pour {self.expediteur}"})
            self.ecriture_livraison = creer_ecriture(caisse, date, f"Livraison {self.numero} - {self.destinataire}", lignes,
                                                     reference=self.numero, origine=self.numero)
        local = _site_local()
        self.statut, self.livre_le, self.retire_par, self.livre_par = self.LIVRE, timezone.now(), retire_par.strip(), utilisateur
        self.livre_site = local.code if local is not None and self.site_origine else ""
        self.save(update_fields=["statut", "livre_le", "retire_par", "livre_par", "livre_site", "ecriture_livraison"])
        if self.site_origine:                              # l'agence d'expédition l'apprendra par le siège
            from apps.echanges.publication import publier

            publier("colis_livraison", self.uid, {"v": 1, "colis": str(self.uid), "livre_le": self.livre_le.isoformat(),
                                                  "retire_par": self.retire_par, "site": self.livre_site,
                                                  "contre_remboursement": str(self.contre_remboursement)},
                    "LIVRE", date, utilisateur or "")
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
        _proprietaire(self, f"L'envoi {self.numero}")
        parametres = ParametresTransport.get()
        caisse = self.gare_depart.journal_caisse()
        # Remis dans une autre agence : c'est elle qui a encaissé, la somme est sur son compte de liaison
        compte_cr = _compte_liaison(self.livre_site) if self.livre_site else parametres.compte_contre_remboursement
        self.ecriture_reversement = creer_ecriture(
            caisse, date or timezone.localdate(), f"Reversement contre-remboursement {self.numero} - {self.expediteur}",
            [{"compte": compte_cr, "debit": self.contre_remboursement},
             {"compte": caisse.compte_tresorerie, "credit": self.contre_remboursement}],
            reference=self.numero, origine=self.numero)
        self.cr_reverse_le = timezone.now()
        self.save(update_fields=["ecriture_reversement", "cr_reverse_le"])
        return self

    @transaction.atomic
    def annuler(self, utilisateur=None, date=None):
        """Annule un envoi non chargé : rembourse le port payé (écriture inverse)."""
        from apps.comptabilite.services import creer_ecriture

        _proprietaire(self, f"L'envoi {self.numero}")
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

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False,
                                    help_text="Vide : créé dans ce dossier ; sinon copie reçue d'un autre site")
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
        self.numero = self.numero or Sequence.piece("DV", self.date.year)
        self.save()
        libelle = self.libelle or f"{self.get_nature_display()} {self.vehicule.immatriculation}"
        self.ecriture = creer_ecriture(self.caisse, self.date, libelle,
                                       [{"compte": self.compte, "section": self.vehicule.section, "vehicule": self.vehicule, "debit": self.montant},
                                        {"compte": self.caisse.compte_tresorerie, "credit": self.montant}],
                                       reference=self.reference or self.numero, origine=self.numero)
        self.save(update_fields=["ecriture"])
        return self
