from django.core.management.base import BaseCommand, CommandError

from ...models import SiteRelais


class Command(BaseCommand):
    help = ("Sur le serveur du relais : déclarer un site (ou lui donner un nouveau jeton), lister, désactiver. "
            "Le jeton n'est affiché qu'une fois : à recopier dans la configuration du site (ECHANGES_RELAIS_JETON).")

    def add_arguments(self, parser):
        parser.add_argument("--code", help="Code du site (le même que dans les échanges : SIEGE, DLA…)")
        parser.add_argument("--nom", default="")
        parser.add_argument("--desactiver", action="store_true")
        parser.add_argument("--liste", action="store_true")

    def handle(self, *args, **o):
        if o["liste"]:
            for s in SiteRelais.objects.all():
                self.stdout.write(f"{s.code:<8} {'actif' if s.actif else 'désactivé':<10} {s.boite.count()} lot(s) en attente · "
                                  f"dernier contact : {s.dernier_contact or 'jamais'}")
            return
        if not o["code"]:
            raise CommandError("--code obligatoire")
        site = SiteRelais.objects.filter(code=o["code"]).first() or SiteRelais(code=o["code"])
        if o["desactiver"]:
            if site.pk is None:
                raise CommandError("site inconnu")
            site.actif = False
            site.save()
            self.stdout.write(f"Site {site.code} désactivé.")
            return
        jeton = site.nouveau_jeton()
        site.nom, site.actif = o["nom"] or site.nom, True
        site.save()
        self.stdout.write(f"Site {site.code} prêt. Jeton (à recopier, il ne sera plus affiché) :\n{jeton}")
