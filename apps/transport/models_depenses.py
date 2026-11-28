"""Dépenses de fonctionnement (loyer, eau, électricité, téléphone, entretien des locaux…) autorisées par le siège.

Chaque agence travaille sur son serveur ; une dépense est demandée, autorisée par le siège (par les fichiers
d'échange), puis payée par n'importe quelle agence ou par le siège : c'est la même société.
  - payée par l'agence à qui elle appartient :   D charge (section de l'agence) / C caisse
  - payée par une autre agence (ou le siège) :   chez le payeur      D liaison de l'agence concernée / C caisse
                                                 chez l'agence concernée, automatiquement à la réception du fichier :
                                                                     D charge / C liaison du payeur
    Au siège, les comptes de liaison 185 se compensent ; la charge est une seule fois dans la consolidation.
Comptes proposés par nature : à valider par l'expert-comptable (modifiables sur chaque demande).
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


class DemandeDepense(models.Model):
    LOYER, EAU_ELECTRICITE, TELECOM, ENTRETIEN, IMPOTS, AUTRE = "LOYER", "EAU_ELECTRICITE", "TELECOM", "ENTRETIEN", "IMPOTS", "AUTRE"
    NATURES = [(LOYER, "Loyer"), (EAU_ELECTRICITE, "Eau et électricité"), (TELECOM, "Téléphone et Internet"),
               (ENTRETIEN, "Entretien et réparation des locaux"), (IMPOTS, "Impôts et taxes"), (AUTRE, "Autre dépense")]
    COMPTES = {LOYER: ("6222", "Locations de bâtiments"), EAU_ELECTRICITE: ("605", "Autres achats (eau, électricité)"),
               TELECOM: ("628", "Frais de télécommunications"), ENTRETIEN: ("624", "Entretien, réparations et maintenance"),
               IMPOTS: ("64", "Impôts et taxes")}
    DEMANDEE, AUTORISEE, REFUSEE, PAYEE, ANNULEE = "DEMANDEE", "AUTORISEE", "REFUSEE", "PAYEE", "ANNULEE"
    STATUTS = [(DEMANDEE, "En attente d'autorisation"), (AUTORISEE, "Autorisée, à payer"), (REFUSEE, "Refusée"),
               (PAYEE, "Payée"), (ANNULEE, "Annulée")]
    ORDRE = {DEMANDEE: 0, AUTORISEE: 1, REFUSEE: 1, PAYEE: 2, ANNULEE: 3}

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField("Site d'origine", max_length=10, blank=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    agence = models.CharField("Dépense de l'agence (code)", max_length=10, blank=True,
                              help_text="Agence à qui appartient la dépense ; vide : celle qui demande")
    nature = models.CharField(max_length=20, choices=NATURES, default=LOYER)
    compte = models.ForeignKey("comptabilite.Compte", on_delete=models.PROTECT, related_name="+", null=True, blank=True,
                               verbose_name="Compte de charge", help_text="Vide : compte proposé pour la nature (à valider)")
    libelle = models.CharField("Libellé", max_length=150)
    beneficiaire = models.CharField("Payé à", max_length=120, blank=True)
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    vehicule = models.ForeignKey("transport.Vehicule", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                                 help_text="Si la dépense concerne un véhicule")
    statut = models.CharField(max_length=10, choices=STATUTS, default=DEMANDEE)
    demande_par = models.CharField(max_length=150, blank=True)
    decision_par = models.CharField("Décision de", max_length=150, blank=True)
    decision_le = models.DateTimeField(null=True, blank=True)
    motif = models.CharField("Motif (refus, annulation)", max_length=200, blank=True)
    caisse = models.ForeignKey("comptabilite.Journal", null=True, blank=True, on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"}, verbose_name="Payée par")
    payeur = models.CharField("Payée par le site", max_length=10, blank=True)
    paye_le = models.DateField(null=True, blank=True)
    paye_par = models.CharField(max_length=150, blank=True)
    ecriture = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_regularisation = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL,
                                                   related_name="+")

    class Meta:
        ordering = ["-date", "-numero"]
        verbose_name = "Demande de dépense"

    def __str__(self):
        return f"{self.numero} {self.libelle} {self.montant}"

    def compte_de_charge(self):
        from apps.comptabilite.models import Compte

        if self.compte_id:
            return self.compte
        numero, intitule = self.COMPTES.get(self.nature, ("658", "Charges diverses"))
        return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]

    @staticmethod
    def _local():
        from apps.echanges.publication import site_local

        return site_local()

    def _section(self, code):
        from apps.comptabilite.models import SectionAnalytique

        if not code:
            return None
        return SectionAnalytique.objects.get_or_create(code=f"AG-{code}"[:20], defaults={"plan": "Agences",
                                                                                         "intitule": f"Agence {code}"})[0]

    @classmethod
    def autorisation_locale(cls):
        """Sans échanges ou au siège, la décision se prend dans ce dossier ; une agence attend le siège."""
        local = cls._local()
        return local is None or local.role == local.SIEGE

    @transaction.atomic
    def demander(self, utilisateur=None):
        from .models import ParametresTransport

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        local = self._local()
        self.agence = (self.agence or (local.code if local else "")).upper()
        self.numero = self.numero or Sequence.piece("DD", self.date.year)
        self.demande_par = str(utilisateur or "")
        plafond = ParametresTransport.get().plafond_depense_sans_autorisation
        if plafond and self.montant <= plafond:                 # petite dépense : autorisée d'office
            self.statut, self.decision_par, self.decision_le = self.AUTORISEE, "Autorisation permanente (plafond)", timezone.now()
        self.save()
        return self

    @transaction.atomic
    def decider(self, autoriser, utilisateur=None, motif=""):
        """Le siège (ou, sans échanges, un autre utilisateur que le demandeur) autorise ou refuse."""
        from apps.echanges.publication import publier

        if not self.autorisation_locale():
            raise ValidationError("Seul le siège autorise les dépenses : envoyez-lui le fichier d'échange.")
        if self.statut != self.DEMANDEE:
            raise ValidationError("Cette demande a déjà reçu une décision.")
        if utilisateur is not None and str(utilisateur) == self.demande_par and not utilisateur.is_superuser \
                and self._local() is None:
            raise ValidationError("Le demandeur ne peut pas autoriser sa propre dépense.")
        if not autoriser and not motif.strip():
            raise ValidationError("Indiquez le motif du refus.")
        self.statut = self.AUTORISEE if autoriser else self.REFUSEE
        self.decision_par, self.decision_le, self.motif = str(utilisateur or "Siège"), timezone.now(), motif.strip()
        self.save(update_fields=["statut", "decision_par", "decision_le", "motif"])
        if self.site_origine:                                    # demande d'une agence : la décision lui est renvoyée
            publier("depense_decision", self.uid, {"v": 1, "demande": str(self.uid), "statut": self.statut,
                                                   "par": self.decision_par, "le": self.decision_le.isoformat(),
                                                   "motif": self.motif}, self.statut, self.date)
        return self

    @transaction.atomic
    def payer(self, caisse, utilisateur=None, date=None):
        """Sortie de caisse ; si la dépense appartient à une autre agence, passe par le compte de liaison."""
        from apps.comptabilite.services import creer_ecriture
        from apps.echanges.publication import publier

        from .models import _compte_liaison

        if self.site_origine:
            raise ValidationError("Cette demande vient d'une autre agence : elle la paie elle-même.")
        if self.statut != self.AUTORISEE:
            raise ValidationError("La dépense doit être autorisée avant d'être payée.")
        if not caisse.compte_tresorerie_id:
            raise ValidationError("Cette caisse n'a pas de compte de trésorerie.")
        local = self._local()
        ici = local.code if local else ""
        date = date or timezone.localdate()
        if not self.agence or self.agence == ici:
            lignes = [{"compte": self.compte_de_charge(), "debit": self.montant, "section": self._section(ici),
                       "vehicule": self.vehicule}]
        else:
            lignes = [{"compte": _compte_liaison(self.agence), "debit": self.montant}]
        lignes.append({"compte": caisse.compte_tresorerie, "credit": self.montant})
        self.ecriture = creer_ecriture(caisse, date, f"Dépense {self.numero} {self.libelle}"[:200], lignes,
                                       reference=self.numero, origine=self.numero)
        self.statut, self.caisse, self.payeur, self.paye_le, self.paye_par = self.PAYEE, caisse, ici, date, str(utilisateur or "")
        self.save()
        if self.agence and self.agence != ici:                  # l'agence concernée passe sa charge à la réception
            publier("depense_payee", self.uid, {
                "v": 1, "demande": str(self.uid), "numero": self.numero, "pour_agence": self.agence, "payeur": ici,
                "compte": self.compte_de_charge().numero, "intitule": self.compte_de_charge().intitule,
                "libelle": self.libelle, "montant": str(self.montant), "date": date.isoformat(),
                "vehicule": str(self.vehicule.uid) if self.vehicule_id else None}, "PAYEE", date)
        return self

    @transaction.atomic
    def annuler(self, motif, utilisateur=None):
        if self.site_origine:
            raise ValidationError("Seule l'agence qui a demandé la dépense peut l'annuler.")
        if self.statut in (self.PAYEE, self.ANNULEE):
            raise ValidationError("Une dépense payée ne s'annule pas : passez une écriture de correction.")
        self.statut, self.motif = self.ANNULEE, motif.strip() or "Annulée"
        self.save(update_fields=["statut", "motif"])
        return self


def regulariser_depense_recue(p, payeur):
    """Chez l'agence à qui appartient la dépense : D charge / C liaison du payeur (une seule fois)."""
    from apps.comptabilite.models import Compte, Journal
    from apps.comptabilite.services import creer_ecriture
    from apps.echanges.publication import hors_import

    from .models import Vehicule, _compte_liaison

    trace = DemandeDepense.objects.filter(uid=p["demande"]).first()
    if trace is not None and trace.ecriture_regularisation_id:
        return trace
    if trace is None:
        trace = DemandeDepense(uid=p["demande"], site_origine=payeur, numero=p["numero"], libelle=p["libelle"][:150],
                               montant=Decimal(p["montant"]), agence=p["pour_agence"], statut=DemandeDepense.PAYEE,
                               payeur=payeur, nature=DemandeDepense.AUTRE)
    compte = Compte.objects.get_or_create(numero=p["compte"], defaults={"intitule": (p.get("intitule") or p["compte"])[:200]})[0]
    vehicule = Vehicule.objects.filter(uid=p.get("vehicule")).first() if p.get("vehicule") else None
    import datetime

    date = datetime.date.fromisoformat(p["date"])
    with hors_import():
        trace.ecriture_regularisation = creer_ecriture(
            Journal.objects.get(code="OD"), date, f"Dépense {p['numero']} payée par {payeur} : {p['libelle']}"[:200],
            [{"compte": compte, "debit": Decimal(p["montant"]), "section": trace._section(p["pour_agence"]), "vehicule": vehicule},
             {"compte": _compte_liaison(payeur), "credit": Decimal(p["montant"])}],
            reference=p["numero"], origine=p["numero"])
    trace.compte, trace.paye_le, trace.vehicule = compte, date, vehicule
    trace.save()
    return trace
