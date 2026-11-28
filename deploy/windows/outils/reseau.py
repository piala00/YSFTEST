"""Poste serveur du réseau local de l'agence : prépare l'accès des autres ordinateurs.

Lancé par 4-DEMARRER-SERVEUR-RESEAU.bat avant le serveur. Les autres postes n'installent rien : ils ouvrent
l'adresse du serveur dans leur navigateur (raccourci « ERP OHADA (poste utilisateur).url » à copier sur leur bureau).
"""
import socket
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
ENV = RACINE / "logiciel" / ".env"
PORT = 8000


def adresses():
    noms = [socket.gethostname()]
    try:
        ips = {i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except OSError:
        ips = set()
    return noms, sorted(ip for ip in ips if not ip.startswith("127."))


def autoriser_les_postes():
    """Le serveur accepte les connexions des autres postes (adresse IP ou nom du serveur)."""
    lignes = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    if "ALLOWED_HOSTS=*" in lignes:
        return
    lignes = [l for l in lignes if not l.startswith("ALLOWED_HOSTS=")] + ["ALLOWED_HOSTS=*"]
    ENV.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print("Accès des autres postes du réseau local autorisé.")


def ouvrir_pare_feu():
    regle = "ERP OHADA (port 8000)"
    existe = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={regle}"],
                            capture_output=True, text=True)
    if existe.returncode == 0:
        return
    ajout = subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", f"name={regle}", "dir=in", "action=allow",
                            "protocol=TCP", f"localport={PORT}", "profile=private,domain"], capture_output=True, text=True)
    if ajout.returncode == 0:
        print("Pare-feu Windows : port 8000 ouvert pour le réseau privé.")
    else:
        print("Pare-feu : ouverture automatique impossible sans droits d'administrateur.")
        print("  -> Faites un clic droit sur 4-DEMARRER-SERVEUR-RESEAU.bat > Exécuter en tant qu'administrateur (une fois),")
        print("     ou acceptez la question du pare-feu Windows (cochez « Réseaux privés »).")


def raccourci(adresse):
    fichier = RACINE / "ERP OHADA (poste utilisateur).url"
    fichier.write_text(f"[InternetShortcut]\r\nURL=http://{adresse}:{PORT}/\r\n", encoding="utf-8")
    return fichier


if __name__ == "__main__":
    autoriser_les_postes()
    if sys.platform == "win32":
        ouvrir_pare_feu()
    noms, ips = adresses()
    print()
    print("=" * 70)
    print("  SERVEUR ERP DE L'AGENCE")
    print("=" * 70)
    print("Sur les autres ordinateurs du réseau, ouvrez le navigateur à l'une de ces adresses :")
    for a in noms + ips:
        print(f"    http://{a}:{PORT}")
    fichier = raccourci(ips[0] if ips else noms[0])
    print(f"\nOu copiez sur leur bureau le raccourci : {fichier.name}")
    print("Conseil : donnez à ce serveur une adresse IP fixe (box / routeur) pour que l'adresse ne change pas.")
    print("Gardez cette fenêtre ouverte : la fermer arrête le logiciel pour tous les postes.\n")
