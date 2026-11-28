"""Deux outils onefile embarqués par Inno ; la même identité publique native que l'ERP."""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

RACINE = Path(SPECPATH).resolve().parents[1]
sys.path.insert(0, str(RACINE))
from apps.licences.cle_editeur import CLES
from apps.licences.identite import verifier_distribution
verifier_distribution(CLES)  # Aucun installateur commercial dépourvu d'autorité.

modules = ["apps.licences." + n for n in ("licence", "cle_editeur", "format_cles", "installation", "nettoyage")]
modules += ["base64", "hashlib", "hmac", "json", "datetime", "dataclasses", "uuid", "winreg", "secrets",
            "sqlite3", "zipfile", "urllib.parse", "stat", "re", "os", "contextlib", "shutil", "tempfile"]
modules += collect_submodules("cryptography")
for nom, source in (("ERP-Controle-Installation", "controle.py"), ("ERP-Nettoyage", "nettoyage.py")):
    a = Analysis([str(RACINE / "deploy/installateur" / source)], pathex=[str(RACINE)], hiddenimports=modules)
    pyz = PYZ(a.pure)
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, name=nom, console=(source == "controle.py"), upx=False)
