"""Passe le plan comptable d'un dossier existant à une longueur fixe (7 chiffres par défaut).

    python manage.py longueur_comptes              # montre ce qui changerait, sans rien modifier
    python manage.py longueur_comptes --appliquer  # renumérote (4111 → 4111000) et fixe la longueur du dossier

Seul le numéro des comptes change : les écritures, tiers, journaux, taxes et paramètres pointent vers le compte
lui-même et le suivent, aucun montant n'est touché. Refusé si deux comptes deviendraient le même numéro (à régler
d'abord avec l'expert-comptable), et tant que le dossier est une copie synchronisée d'un autre logiciel.
"""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.comptabilite import services
from apps.core.models import Societe


class Command(BaseCommand):
    help = "Passe le plan comptable à N chiffres (zéros à droite) ; sans --appliquer, simulation"

    def add_arguments(self, parser):
        parser.add_argument("--longueur", type=int, default=7)
        parser.add_argument("--appliquer", action="store_true")

    def handle(self, *args, **o):
        longueur = o["longueur"]
        if not 4 <= longueur <= 12:
            raise CommandError("Longueur entre 4 et 12 chiffres.")
        if Societe.get().source_mode == Societe.SYNCHRO_MIROIR:
            raise CommandError("Copie synchronisée d'un autre logiciel : le plan d'origine fait foi jusqu'à la bascule.")
        changements, collisions, trop_longs = services.projet_longueur_comptes(longueur)
        for ancien, nouveau in changements[:30]:
            self.stdout.write(f"  {ancien} → {nouveau}")
        if len(changements) > 30:
            self.stdout.write(f"  … et {len(changements) - 30} autres")
        for numero in trop_longs:
            self.stdout.write(f"  {numero} : plus long que {longueur} chiffres, conversion interdite")
        if trop_longs:
            raise CommandError(
                f"{len(trop_longs)} compte(s) dépassent {longueur} chiffres : "
                "établissez un mapping manuel après sauvegarde, aucune modification effectuée."
            )
        for cible, numeros in sorted(collisions.items()):
            self.stdout.write(f"  COLLISION : {', '.join(numeros)} deviendraient tous {cible}")
        if collisions:
            raise CommandError(f"{len(collisions)} collision(s) : rien n'est modifié.")
        if not o["appliquer"]:
            self.stdout.write(f"{len(changements)} compte(s) à renuméroter. Relancez avec --appliquer pour le faire.")
            return
        try:
            n = services.appliquer_longueur_comptes(longueur)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages))
        self.stdout.write(self.style.SUCCESS(f"Plan comptable à {longueur} chiffres : {n} compte(s) renuméroté(s)."))
