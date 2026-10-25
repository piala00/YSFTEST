"""Caisses des guichets et clôtures de la journée (audit P1 ; skill réf. 07 et 11).

Chaque agent (billetterie, colis) ouvre sa session de caisse avec un fonds de départ. Ses encaissements et
décaissements en espèces y sont rattachés automatiquement. À la fermeture, il déclare le montant compté : l'écart
avec le montant attendu est calculé ; le chef de gare approuve (justification obligatoire en cas d'écart) et l'écart
est comptabilisé (manquant : à la charge de l'agent ou de l'agence ; excédent : produit divers).
Les fonds envoyés à la banque ou au siège passent par 585 Virements de fonds jusqu'à leur réception.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.core.models import Sequence

ZERO = Decimal("0")


def _compte(numero, intitule):
    from apps.comptabilite.models import Compte

    return Compte.objects.get_or_create(numero=numero, defaults={"intitule": intitule})[0]


class SessionCaisse(models.Model):
    BILLETTERIE, COLIS, AUTRE = "BILLETTERIE", "COLIS", "AUTRE"
    SERVICES = [(BILLETTERIE, "Billetterie"), (COLIS, "Colis et expéditions"), (AUTRE, "Autre")]
    OUVERTE, FERMEE, APPROUVEE = "OUVERTE", "FERMEE", "APPROUVEE"
    STATUTS = [(OUVERTE, "Ouverte"), (FERMEE, "Fermée, à approuver"), (APPROUVEE, "Approuvée")]
    CHARGE, AGENT = "CHARGE", "AGENT"
    IMPUTATIONS = [(CHARGE, "Charge de l'agence"), (AGENT, "À la charge de l'agent (retenue)")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    site_origine = models.CharField(max_length=10, blank=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sessions_caisse")
    service = models.CharField(max_length=12, choices=SERVICES, default=BILLETTERIE)
    gare = models.ForeignKey("transport.Gare", null=True, blank=True, on_delete=models.PROTECT, related_name="sessions_caisse")
    caisse = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+",
                               limit_choices_to={"type_journal": "TRESORERIE"})
    fonds_initial = models.DecimalField("Fonds de caisse au départ", max_digits=14, decimal_places=0, default=ZERO)
    ouverte_le = models.DateTimeField(default=timezone.now)
    fermee_le = models.DateTimeField(null=True, blank=True)
    montant_compte = models.DecimalField("Montant compté", max_digits=14, decimal_places=0, null=True, blank=True)
    attendu = models.DecimalField("Montant attendu", max_digits=14, decimal_places=0, null=True, blank=True)
    ecart = models.DecimalField(max_digits=14, decimal_places=0, null=True, blank=True)
    justification = models.CharField(max_length=250, blank=True)
    remis_a = models.CharField("Fonds remis à", max_length=120, blank=True, help_text="Chef de gare, coffre…")
    statut = models.CharField(max_length=10, choices=STATUTS, default=OUVERTE)
    approuvee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approuvee_le = models.DateTimeField(null=True, blank=True)
    imputation_ecart = models.CharField(max_length=10, choices=IMPUTATIONS, blank=True)
    ecriture_ecart = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-ouverte_le"]
        verbose_name = "Session de caisse"
        verbose_name_plural = "Sessions de caisse"

    def __str__(self):
        return f"{self.numero} {self.agent} {self.ouverte_le:%d/%m %H:%M}"

    @classmethod
    def ouverte_de(cls, utilisateur):
        if utilisateur is None or not getattr(utilisateur, "pk", None):
            return None
        return cls.objects.filter(agent=utilisateur, statut=cls.OUVERTE).first()

    @classmethod
    @transaction.atomic
    def ouvrir(cls, agent, caisse, service=BILLETTERIE, gare=None, fonds_initial=ZERO):
        if cls.ouverte_de(agent):
            raise ValidationError("Vous avez déjà une caisse ouverte : fermez-la d'abord.")
        if Decimal(fonds_initial) < 0:
            raise ValidationError("Le fonds de caisse ne peut pas être négatif.")
        return cls.objects.create(agent=agent, caisse=caisse, service=service, gare=gare, fonds_initial=fonds_initial,
                                  numero=Sequence.piece("SC", timezone.localdate().year))

    def detail(self):
        """Ce que la session a encaissé et décaissé, par nature (espèces et autres moyens)."""
        from .models import Billet, Colis

        billets = self.billets.all()
        d = {
            "billets_especes": sum((b.prix for b in billets if b.paiement == Billet.ESPECES), ZERO),
            "billets_mobile": sum((b.prix for b in billets if b.paiement == Billet.MOBILE_MONEY), ZERO),
            "billets_compte": sum((b.prix for b in billets if b.paiement == Billet.COMPTE), ZERO),
            "nb_billets": billets.count(),
            "remboursements": sum((b.rembourse for b in self.remboursements_billets.all() if b.paiement == Billet.ESPECES), ZERO),
            "colis": sum((c.prix for c in self.colis_enregistres.all() if c.port == Colis.PAYE and not c.client_id
                          and c.statut != Colis.ANNULE), ZERO),
            "livraisons": sum((c.a_encaisser for c in self.colis_livres.all()), ZERO),
            "reversements": sum((c.contre_remboursement for c in self.colis_reverses.all()), ZERO),
        }
        d["attendu"] = (self.fonds_initial + d["billets_especes"] - d["remboursements"] + d["colis"] + d["livraisons"]
                        - d["reversements"])
        return d

    @transaction.atomic
    def fermer(self, montant_compte, justification="", remis_a=""):
        if self.statut != self.OUVERTE:
            raise ValidationError("Cette caisse est déjà fermée.")
        montant_compte = Decimal(montant_compte)
        if montant_compte < 0:
            raise ValidationError("Le montant compté ne peut pas être négatif.")
        self.attendu = self.detail()["attendu"]
        self.montant_compte, self.ecart = montant_compte, montant_compte - self.attendu
        self.justification, self.remis_a, self.fermee_le = justification.strip(), remis_a.strip(), timezone.now()
        self.statut = self.FERMEE
        self.save()
        return self

    @transaction.atomic
    def approuver(self, utilisateur, justification="", imputation=CHARGE):
        """Le chef de gare contrôle et approuve ; l'écart éventuel est comptabilisé."""
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.FERMEE:
            raise ValidationError("Seule une caisse fermée peut être approuvée.")
        if utilisateur is not None and utilisateur.pk == self.agent_id and not utilisateur.is_superuser:
            raise ValidationError("L'agent ne peut pas approuver sa propre caisse.")
        if justification:
            self.justification = justification.strip()
        if self.ecart and not self.justification:
            raise ValidationError("Justifiez l'écart de caisse avant de l'approuver.")
        if self.ecart:
            caisse = self.caisse.compte_tresorerie
            if self.ecart < 0:
                manque = -self.ecart
                compte = (_compte("421", "Personnel, avances et acomptes") if imputation == self.AGENT
                          else _compte("658", "Charges diverses"))
                lignes = [{"compte": compte, "debit": manque}, {"compte": caisse, "credit": manque}]
            else:
                lignes = [{"compte": caisse, "debit": self.ecart}, {"compte": _compte("758", "Produits divers"), "credit": self.ecart}]
            self.ecriture_ecart = creer_ecriture(self.caisse, timezone.localdate(),
                                                 f"Écart de caisse {self.numero} {self.agent} : {self.justification}"[:200],
                                                 lignes, reference=self.numero)
            self.imputation_ecart = imputation if self.ecart < 0 else ""
        self.statut, self.approuvee_par, self.approuvee_le = self.APPROUVEE, utilisateur, timezone.now()
        self.save()
        return self


def session_pour(utilisateur):
    """Session de caisse de l'agent qui encaisse. Obligatoire si les Paramètres transport l'exigent."""
    from .models import ParametresTransport

    session = SessionCaisse.ouverte_de(utilisateur)
    if session is None and utilisateur is not None and getattr(utilisateur, "pk", None) \
            and ParametresTransport.get().sessions_caisse_obligatoires:
        raise ValidationError("Ouvrez votre caisse (menu Ma caisse) avant d'encaisser.")
    return session


class TransfertFonds(models.Model):
    """Fonds envoyés de la caisse vers la banque ou une autre caisse : en transit (585) jusqu'à leur réception."""

    EN_TRANSIT, RECU = "EN_TRANSIT", "RECU"
    STATUTS = [(EN_TRANSIT, "En transit"), (RECU, "Reçu")]

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date_envoi = models.DateField(default=timezone.localdate)
    origine = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+", verbose_name="Depuis",
                                limit_choices_to={"type_journal": "TRESORERIE"})
    destination = models.ForeignKey("comptabilite.Journal", on_delete=models.PROTECT, related_name="+", verbose_name="Vers",
                                    limit_choices_to={"type_journal": "TRESORERIE"})
    montant = models.DecimalField(max_digits=14, decimal_places=0)
    porteur = models.CharField("Porteur / référence", max_length=150, blank=True, help_text="Convoyeur, n° de bordereau de versement…")
    statut = models.CharField(max_length=12, choices=STATUTS, default=EN_TRANSIT)
    date_reception = models.DateField(null=True, blank=True)
    ecriture_envoi = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    ecriture_reception = models.OneToOneField("comptabilite.Ecriture", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    envoye_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    recu_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date_envoi", "-numero"]
        verbose_name = "Transfert de fonds"
        verbose_name_plural = "Transferts de fonds"

    @transaction.atomic
    def envoyer(self, utilisateur=None):
        from apps.comptabilite.services import creer_ecriture

        if self.montant is None or self.montant <= 0:
            raise ValidationError("Le montant doit être positif.")
        if self.origine_id == self.destination_id:
            raise ValidationError("Choisissez une destination différente.")
        for j in (self.origine, self.destination):
            if not j.compte_tresorerie_id:
                raise ValidationError(f"Le journal {j.code} n'a pas de compte de trésorerie.")
        self.numero = self.numero or Sequence.piece("TF", self.date_envoi.year)
        self.envoye_par = utilisateur
        self.save()
        self.ecriture_envoi = creer_ecriture(self.origine, self.date_envoi, f"Transfert {self.numero} vers {self.destination.intitule}",
                                             [{"compte": _compte("585", "Virements de fonds"), "debit": self.montant},
                                              {"compte": self.origine.compte_tresorerie, "credit": self.montant}],
                                             reference=self.numero)
        self.save(update_fields=["ecriture_envoi"])
        return self

    @transaction.atomic
    def recevoir(self, utilisateur=None, date=None):
        from apps.comptabilite.services import creer_ecriture

        if self.statut != self.EN_TRANSIT:
            raise ValidationError("Transfert déjà reçu.")
        self.date_reception = date or timezone.localdate()
        if self.date_reception < self.date_envoi:
            raise ValidationError("La réception ne peut précéder l'envoi.")
        self.ecriture_reception = creer_ecriture(
            self.destination, self.date_reception, f"Réception du transfert {self.numero}",
            [{"compte": self.destination.compte_tresorerie, "debit": self.montant},
             {"compte": _compte("585", "Virements de fonds"), "credit": self.montant}], reference=self.numero)
        self.statut, self.recu_par = self.RECU, utilisateur
        self.save(update_fields=["statut", "date_reception", "ecriture_reception", "recu_par"])
        return self


class ClotureJournee(models.Model):
    """Clôture d'une journée par service, puis de l'agence (statut du rapport journalier)."""

    BILLETTERIE, COLIS, GARAGE, AGENCE = "BILLETTERIE", "COLIS", "GARAGE", "AGENCE"
    PERIMETRES = [(BILLETTERIE, "Billetterie"), (COLIS, "Colis et expéditions"), (GARAGE, "Garage"), (AGENCE, "Agence (toute la journée)")]

    date = models.DateField()
    perimetre = models.CharField("Service", max_length=12, choices=PERIMETRES)
    cloture_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    cloture_le = models.DateTimeField(auto_now_add=True)
    commentaire = models.CharField(max_length=250, blank=True)
    anomalies = models.JSONField(default=list, blank=True, help_text="Points ouverts au moment de la clôture (acceptés)")

    class Meta:
        ordering = ["-date", "perimetre"]
        unique_together = [("date", "perimetre")]
        verbose_name = "Clôture de journée"


def anomalies_du_jour(jour, perimetre=ClotureJournee.AGENCE):
    """Points qui empêchent de dire la journée « complète » (le chef peut clôturer en les acceptant, sauf blocages)."""
    from apps.echanges.models import Evenement, EvenementRecu, LotEmis
    from apps.garage.models import OrdreReparation

    from .models import Billet, Colis, Depart, Troncon

    bloquants, signales = [], []
    services = {ClotureJournee.BILLETTERIE: [SessionCaisse.BILLETTERIE], ClotureJournee.COLIS: [SessionCaisse.COLIS]}.get(
        perimetre, [SessionCaisse.BILLETTERIE, SessionCaisse.COLIS, SessionCaisse.AUTRE])
    sessions = SessionCaisse.objects.filter(ouverte_le__date=jour, service__in=services)
    for s in sessions.filter(statut=SessionCaisse.OUVERTE):
        bloquants.append(f"Caisse {s.numero} de {s.agent} encore ouverte")
    for s in sessions.filter(statut=SessionCaisse.FERMEE):
        bloquants.append(f"Caisse {s.numero} de {s.agent} fermée mais pas approuvée (écart {s.ecart})")
    if perimetre in (ClotureJournee.BILLETTERIE, ClotureJournee.AGENCE):
        for d in Depart.objects.filter(date=jour, statut=Depart.PROGRAMME, site_origine=""):
            signales.append(f"Départ {d.numero} {d.heure:%H:%M} {d.ligne.code} pas parti")
        for d in Depart.objects.filter(date__lte=jour, statut=Depart.ARRIVE, site_origine=""):
            signales.append(f"Voyage {d.numero} arrivé mais pas clôturé")
        from .models_exploitation import AvanceMission

        for a in AvanceMission.objects.filter(statut=AvanceMission.REMISE, date__lte=jour):
            signales.append(f"Avance de mission {a.numero} ({a.beneficiaire}, {a.montant:,.0f}) pas encore justifiée".replace(",", " "))
        attente = Troncon.objects.filter(depart__isnull=True, statut=Troncon.A_VOYAGER, billet__statut=Billet.VENDU,
                                         site_origine="")
        n = attente.filter(depart_manque__isnull=True).count()
        if n:
            signales.append(f"{n} voyageur(s) en correspondance à placer")
        n = attente.filter(depart_manque__isnull=False).count()
        if n:
            signales.append(f"{n} voyageur(s) absent(s) au départ, billet à reporter ou rembourser")
        n = Billet.objects.filter(remboursement=Billet.AUTORISE, site_origine="").count()
        if n:
            signales.append(f"{n} remboursement(s) de billet autorisé(s) pas encore payé(s)")
    if perimetre in (ClotureJournee.COLIS, ClotureJournee.AGENCE):
        n = Colis.objects.filter(date__lte=jour, statut=Colis.ENREGISTRE, site_origine="").count()
        if n:
            signales.append(f"{n} envoi(s) enregistré(s) pas encore chargé(s)")
    if perimetre in (ClotureJournee.GARAGE, ClotureJournee.AGENCE):
        for o in OrdreReparation.objects.filter(statut=OrdreReparation.OUVERT, date_entree__lte=jour):
            signales.append(f"Réparation {o.numero} en cours ({o.vehicule.immatriculation})")
    if perimetre == ClotureJournee.AGENCE:
        for p, _ in ClotureJournee.PERIMETRES[:3]:
            if not ClotureJournee.objects.filter(date=jour, perimetre=p).exists():
                signales.append(f"Service {dict(ClotureJournee.PERIMETRES)[p]} pas clôturé")
        attente = EvenementRecu.objects.filter(statut__in=[EvenementRecu.ATTENTE, EvenementRecu.CONFLIT]).count()
        if attente:
            signales.append(f"{attente} fait(s) reçu(s) d'autres agences en attente ou en conflit")
        dernier = max(LotEmis.objects.values_list("sequence_a", flat=True), default=0)
        non_envoyes = Evenement.objects.filter(sequence__gt=dernier).count()
        if non_envoyes:
            signales.append(f"{non_envoyes} fait(s) pas encore envoyé(s) au siège (préparez le fichier)")
    return bloquants, signales


@transaction.atomic
def cloturer_journee(jour, perimetre, utilisateur, commentaire=""):
    bloquants, signales = anomalies_du_jour(jour, perimetre)
    if bloquants:
        raise ValidationError("Clôture impossible : " + " ; ".join(bloquants))
    if ClotureJournee.objects.filter(date=jour, perimetre=perimetre).exists():
        raise ValidationError("Cette journée est déjà clôturée pour ce service.")
    return ClotureJournee.objects.create(date=jour, perimetre=perimetre, cloture_par=utilisateur, commentaire=commentaire,
                                         anomalies=signales)
