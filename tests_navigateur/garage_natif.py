"""Exécuter les recettes critiques avec les modules .pyd du runner Windows jetable."""
import json
import os
from pathlib import Path
import sys


def main():
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Recette réservée au runner Windows fictif de CI.")
    racine = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(racine))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
    import django
    django.setup()
    from apps.garage import models, models_magasin, validation
    from apps.reporting import exports
    modules = [models, models_magasin, validation, exports]
    for module in modules:
        if Path(module.__file__).suffix.lower() != ".pyd":
            raise AssertionError(f"Module non natif : {module.__name__}")
    print(json.dumps({"modules_natifs": [m.__name__ for m in modules],
                      "donnees": "Fictives, base de test créée et détruite par Django"}, ensure_ascii=False), flush=True)
    from django.core.management import call_command
    call_command("test", "apps.garage", "apps.reporting.tests_exports_excel", interactive=False, verbosity=1)


if __name__ == "__main__":
    main()
