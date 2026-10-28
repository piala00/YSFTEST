# Spécification PyInstaller : tout l'ERP dans un programme (dossier ERP-OHADA-<Édition> avec son .exe).
#   ERP_EDITION=transport pyinstaller deploy/executable/erp_ohada.spec      (depuis la racine du dépôt)
# Avant : python manage.py collectstatic --noinput (les fichiers statiques sont inclus tels quels).
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

RACINE = Path(SPECPATH).resolve().parents[1]
sys.path.insert(0, str(RACINE))                        # pour inventorier apps et erp (sous-processus compris)
os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [str(RACINE), os.environ.get("PYTHONPATH", "")]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp.settings")
EDITION = os.environ.get("ERP_EDITION", "transport").lower()
NOM = f"ERP-OHADA-{EDITION.capitalize()}"
TRAVAIL = Path(os.environ.get("ERP_TRAVAIL", RACINE / "build")) / EDITION
TRAVAIL.mkdir(parents=True, exist_ok=True)
(TRAVAIL / "edition.txt").write_text(EDITION, encoding="utf-8")

try:                                                   # pilote SQL Server : inclus s'il est installé
    import mssql  # noqa: F401
    pilote_sql = collect_submodules("mssql")
except ImportError:
    pilote_sql = []
modules = pilote_sql + (collect_submodules("apps") + collect_submodules("erp") + collect_submodules("django")
           + collect_submodules("rest_framework") + collect_submodules("whitenoise") + collect_submodules("waitress")
           + collect_submodules("cryptography"))     # importée en différé : invisible après compilation native
donnees = (collect_data_files("apps", include_py_files=False) + collect_data_files("django")
           + collect_data_files("rest_framework") + collect_data_files("tzdata")
           + [(str(RACINE / "templates"), "templates"), (str(RACINE / "staticfiles"), "staticfiles"),
              (str(RACINE / "static"), "static"), (str(TRAVAIL / "edition.txt"), ".")])

# Traductions de Django : français et anglais seulement
donnees = [(src, dst) for src, dst in donnees
           if "locale" not in Path(dst).parts or {"fr", "en"} & set(Path(dst).parts)]

a = Analysis([str(RACINE / "deploy" / "executable" / "erp_ohada.py")], pathex=[str(RACINE)], hiddenimports=modules,
             datas=donnees, excludes=["tkinter", "django.contrib.gis", "numpy", "PIL", "yaml", "pandas", "matplotlib",
                       "IPython", "pytest", "playwright"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NOM, console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, upx=False, name=NOM)

# À côté du programme : la notice et la documentation (sans les paquets .zip)
import shutil  # noqa: E402

DOSSIER = Path(DISTPATH) / NOM
shutil.copy2(RACINE / "deploy" / "executable" / "LISEZ-MOI.txt", DOSSIER / "LISEZ-MOI.txt")
shutil.copytree(RACINE / "docs", DOSSIER / "documentation", ignore=shutil.ignore_patterns("*.zip"), dirs_exist_ok=True)
