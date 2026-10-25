from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.models import Agence

from ... import lots
from ...publication import site_local


class Command(BaseCommand):
    help = ("Échanges entre le siège et les agences hors ligne, par fichiers .erpx (WhatsApp, Telegram, clé USB…). "
            "Sous-commandes : siege, agence, installation, installer, exporter, importer, etat.")

    def add_arguments(self, parser):
        sous = parser.add_subparsers(dest="action", required=True)
        p = sous.add_parser("siege", help="Ce poste devient le siège (consolidation)")
        p.add_argument("--code", required=True)
        p.add_argument("--nom", required=True)
        p = sous.add_parser("agence", help="Au siège : déclarer une agence")
        p.add_argument("--code", required=True)
        p.add_argument("--nom", required=True)
        p.add_argument("--ville", default="")
        p = sous.add_parser("installation", help="Au siège : fichier d'installation d'une agence (contient sa clé)")
        p.add_argument("--agence", required=True)
        p.add_argument("--dossier", default=".")
        p = sous.add_parser("installer", help="Dans l'agence : installer avec le fichier du siège")
        p.add_argument("fichier")
        p = sous.add_parser("exporter", help="Fabriquer le lot à envoyer")
        p.add_argument("--vers", default="", help="Code du destinataire (agence : le siège par défaut ; siège : « tous »)")
        p.add_argument("--dossier", default=".")
        p.add_argument("--depuis", type=int, help="Renvoyer depuis ce n° de fait")
        p = sous.add_parser("importer", help="Intégrer un ou plusieurs lots reçus")
        p.add_argument("fichiers", nargs="+")
        sous.add_parser("etat", help="Identité du site, sites connus, lots en retard")

    def handle(self, *args, **o):
        try:
            getattr(self, f"_{o['action']}")(o)
        except lots.LotInvalide as exc:
            raise CommandError(str(exc))

    def _siege(self, o):
        s = lots.configurer_siege(o["code"], o["nom"])
        self.stdout.write(f"Siège {s.code} configuré.")

    def _agence(self, o):
        a = lots.ajouter_agence(o["code"], o["nom"], o["ville"])
        self.stdout.write(f"Agence {a.code} déclarée (n° {a.rang}, compte de liaison {a.compte_liaison.numero}).")

    def _ecrire(self, dossier, nom, octets):
        chemin = Path(dossier) / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(octets)
        self.stdout.write(str(chemin))

    def _installation(self, o):
        agence = Agence.objects.filter(code=o["agence"]).first()
        if agence is None:
            raise CommandError(f"Agence {o['agence']} inconnue.")
        self._ecrire(o["dossier"], *lots.fichier_installation(agence))

    def _installer(self, o):
        chemin = Path(o["fichier"])
        rapport = lots.installer_agence(chemin.read_bytes(), chemin.name)
        self.stdout.write(f"Agence {site_local().code} installée.\n{rapport.texte()}")

    def _exporter(self, o):
        local = site_local()
        if local is None:
            raise CommandError("Ce poste n'est pas configuré pour les échanges.")
        if local.role == local.SIEGE:
            cibles = (Agence.objects.filter(role=Agence.AGENCE, actif=True, uid__isnull=False) if o["vers"] in ("", "tous")
                      else Agence.objects.filter(code=o["vers"]))
        else:
            cibles = Agence.objects.filter(role=Agence.SIEGE, uid__isnull=False)
        if not cibles:
            raise CommandError("Aucun destinataire.")
        for cible in cibles:
            self._ecrire(o["dossier"], *lots.exporter(cible, depuis=o["depuis"]))

    def _importer(self, o):
        for f in o["fichiers"]:
            chemin = Path(f)
            self.stdout.write(f"{chemin.name} : {lots.importer(chemin.read_bytes(), chemin.name).texte()}")

    def _etat(self, o):
        from ...models import Evenement, EvenementRecu

        local = site_local()
        if local is None:
            self.stdout.write("Ce poste n'est pas configuré pour les échanges.")
            return
        self.stdout.write(f"Ce site : {local.code} ({local.get_role_display()}) · {Evenement.objects.count()} fait(s) publié(s)")
        for a in Agence.objects.exclude(pk=local.pk).filter(uid__isnull=False):
            attente = EvenementRecu.objects.filter(site_origine=a, statut=EvenementRecu.ATTENTE).count()
            self.stdout.write(f"  {a.code:<8} {a.get_role_display():<22} reçu jusqu'au fait n° {a.sequence_integree:<6} "
                              f"dernier lot : {a.derniere_reception or 'jamais'} · en attente : {attente}")
