"""Scénario de bout en bout sur quatre dossiers séparés (siège, Douala, Yaoundé, Bertoua) qui ne communiquent que par
fichiers : billets, colis entre agences, voyageur Douala → Garoua-Boulaï qui change de véhicule à Bertoua.
Utilisé par le test d'intégration ; lançable à la main : python -m apps.echanges.scenario DOSSIER_DE_TRAVAIL
"""
import json
import os
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


class Dossier:
    def __init__(self, travail, nom):
        self.nom, self.base = nom, str(Path(travail) / f"{nom}.sqlite3")
        self.env = {**os.environ, "SQLITE_FICHIER": self.base, "DB_ENGINE": "sqlite", "DJANGO_SETTINGS_MODULE": "erp.settings"}

    def manage(self, *args):
        r = subprocess.run([sys.executable, "manage.py", *args], cwd=RACINE, env=self.env, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"[{self.nom}] manage.py {' '.join(args)}\n{r.stdout}\n{r.stderr}")
        return r.stdout

    def py(self, code):
        """Exécute du code Django dans ce dossier ; la dernière ligne imprimée en JSON est renvoyée."""
        sortie = self.manage("shell", "-c", code)
        return json.loads(sortie.strip().splitlines()[-1]) if sortie.strip() else None

    def creer(self):
        self.manage("migrate", "-v0")
        self.manage("init_erp", "--activite", "transport", "-v0")


def lots_de(sortie):
    return [l.strip() for l in sortie.splitlines() if l.strip().endswith(".erpx")]


def executer(travail):
    travail = Path(travail)
    for f in travail.glob("*"):
        f.unlink()
    siege, dla, yde = Dossier(travail, "siege"), Dossier(travail, "douala"), Dossier(travail, "yaounde")
    bta = Dossier(travail, "bertoua")
    for d in (siege, dla, yde, bta):
        d.creer()
    r = {}
    siege.manage("echanges", "siege", "--code", "SIEGE", "--nom", "Siège")
    siege.manage("echanges", "agence", "--code", "DLA", "--nom", "Agence de Douala", "--ville", "Douala")
    siege.manage("echanges", "agence", "--code", "YDE", "--nom", "Agence de Yaoundé", "--ville", "Yaoundé")
    siege.manage("echanges", "agence", "--code", "BTA", "--nom", "Agence de Bertoua", "--ville", "Bertoua")
    siege.py("""
from apps.core.models import Agence
from apps.transport.models import Chauffeur, Gare, Ligne, Vehicule
dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala", agence=Agence.objects.get(code="DLA"))
yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé", agence=Agence.objects.get(code="YDE"))
Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000, colis_forfait=1500, colis_prix_kg=100)
Ligne.objects.create(code="YDE-DLA", gare_depart=yde, gare_arrivee=dla, prix_billet=6000, colis_forfait=1500, colis_prix_kg=100)
bta = Gare.objects.create(code="BTA", nom="Gare de Bertoua", ville="Bertoua", agence=Agence.objects.get(code="BTA"))
gbl = Gare.objects.create(code="GBL", nom="Gare de Garoua-Boulaï", ville="Garoua-Boulaï", agence=Agence.objects.get(code="BTA"))
Ligne.objects.create(code="DLA-BTA", gare_depart=dla, gare_arrivee=bta, prix_billet=8000)
Ligne.objects.create(code="BTA-GBL", gare_depart=bta, gare_arrivee=gbl, prix_billet=4000)
Ligne.objects.create(code="DLA-GBL", gare_depart=dla, gare_arrivee=gbl, prix_billet=11000)
Vehicule.objects.create(immatriculation="LT 101 AA", nombre_places=30)
Vehicule.objects.create(immatriculation="EN 202 BB", nombre_places=30)
Vehicule.objects.create(immatriculation="LT 303 CC", nombre_places=30)
Chauffeur.objects.create(nom="Chauffeur Un")
print("null")""")
    inst_dla = lots_de(siege.manage("echanges", "installation", "--agence", "DLA", "--dossier", str(travail)))[0]
    inst_yde = lots_de(siege.manage("echanges", "installation", "--agence", "YDE", "--dossier", str(travail)))[0]
    inst_bta = lots_de(siege.manage("echanges", "installation", "--agence", "BTA", "--dossier", str(travail)))[0]
    dla.manage("echanges", "installer", inst_dla)
    yde.manage("echanges", "installer", inst_yde)
    bta.manage("echanges", "installer", inst_bta)
    r["dla_referentiels"] = dla.py("""
import json
from apps.transport.models import Gare, Ligne
from apps.core.models import Agence
print(json.dumps({"gares": Gare.objects.count(), "lignes": Ligne.objects.count(),
                  "liaisons": sorted(a.compte_liaison.numero for a in Agence.objects.filter(locale=False))}))""")
    # Douala vend, expédie un colis en port dû avec contre-remboursement, fait partir le car
    r["dla_vente"] = dla.py("""
import datetime, json
from apps.transport.models import *
d = Depart.objects.create(ligne=Ligne.objects.get(code="DLA-YDE"), date=datetime.date.today(), heure=datetime.time(7),
                          vehicule=Vehicule.objects.get(immatriculation="LT 101 AA"), chauffeur=Chauffeur.objects.first())
Billet(depart=d, voyageur="Voyageur Fictif", siege=1).vendre()
Billet(depart=d, voyageur="Voyageuse Fictive", siege=2).vendre()
c = Colis(gare_depart=Gare.objects.get(code="DLA"), gare_arrivee=Gare.objects.get(code="YDE"), expediteur="Boutique Fictive",
          destinataire="Client Fictif", prix=2000, port=Colis.DU, contre_remboursement=50000).enregistrer()
c.charger(d); d.partir()
# Voyageur Douala -> Garoua-Boulaï : car LT 101 AA jusqu'à Bertoua, correspondance choisie à Bertoua
d2 = Depart.objects.create(ligne=Ligne.objects.get(code="DLA-BTA"), date=datetime.date.today(), heure=datetime.time(6),
                           vehicule=Vehicule.objects.get(immatriculation="LT 303 CC"), chauffeur=Chauffeur.objects.first())
b = Billet(depart=d2, gare_arrivee=Gare.objects.get(code="GBL"), voyageur="Voyageur en correspondance").vendre()
d2.partir()
print(json.dumps({"code": c.code_retrait, "colis": c.numero, "billet_corr": b.numero,
                  "parts": [str(t.part) for t in b.troncons.all()]}))""")
    lot1 = lots_de(dla.manage("echanges", "exporter", "--dossier", str(travail)))[0]
    r["siege_import1"] = siege.manage("echanges", "importer", lot1)
    r["siege_rejeu"] = siege.manage("echanges", "importer", lot1)
    lots_siege = lots_de(siege.manage("echanges", "exporter", "--vers", "tous", "--dossier", str(travail)))
    vers_yde = [l for l in lots_siege if "vers-YDE" in l][0]
    r["yde_import"] = yde.manage("echanges", "importer", vers_yde)
    # Yaoundé constate l'arrivée et remet le colis contre le code (encaisse port dû + contre-remboursement)
    r["yde_remise"] = yde.py(f"""
import json
from apps.transport.models import *
from apps.comptabilite.models import LigneEcriture
c = Colis.objects.get(numero="{r['dla_vente']['colis']}")
avant = c.statut
c.depart.arriver(); c.refresh_from_db()
c.livrer("{r['dla_vente']['code']}", "Client Fictif CNI 1")
cr = c.ecriture_livraison.lignes.get(credit=50000).compte.numero
print(json.dumps({{"avant": avant, "statut": c.statut, "compte_cr": cr, "billets_ici": Billet.objects.count()}}))""")
    lot_yde = lots_de(yde.manage("echanges", "exporter", "--dossier", str(travail)))[0]
    siege.manage("echanges", "importer", lot_yde)
    # Bertoua place le voyageur sur son car et le fait partir : la part du tronçon va à ce véhicule
    vers_bta = [l for l in lots_siege if "vers-BTA" in l][0]
    r["bta_import"] = bta.manage("echanges", "importer", vers_bta)
    r["bta_correspondance"] = bta.py(f"""
import datetime, json
from apps.transport.models import *
d = Depart.objects.create(ligne=Ligne.objects.get(code="BTA-GBL"), date=datetime.date.today(), heure=datetime.time(15),
                          vehicule=Vehicule.objects.get(immatriculation="EN 202 BB"), chauffeur=Chauffeur.objects.first())
attente = list(d.correspondances_a_affecter())
attente[0].affecter(d, siege=3)
d.partir()
from apps.garage.models import PleinCarburant
from apps.comptabilite.models import Journal
PleinCarburant(vehicule=d.vehicule, depart=d, litres=150, prix_litre=840, kilometrage=52000, station="Station fictive",
               caisse=Journal.objects.get(code="CA")).enregistrer()
lignes = {{l.compte.numero: (str(l.debit), str(l.credit), l.vehicule.immatriculation if l.vehicule else None)
          for l in d.ecriture_recettes.lignes.select_related("compte", "vehicule")}}
print(json.dumps({{"attente": [t.billet.numero for t in attente], "lignes": lignes}}))""")
    siege.manage("echanges", "importer", lots_de(bta.manage("echanges", "exporter", "--dossier", str(travail)))[0])
    lots_siege = lots_de(siege.manage("echanges", "exporter", "--vers", "tous", "--dossier", str(travail)))
    vers_dla = [l for l in lots_siege if "vers-DLA" in l][0]
    r["dla_import2"] = dla.manage("echanges", "importer", vers_dla)
    # Douala apprend la remise et reverse le contre-remboursement à l'expéditeur
    r["dla_reversement"] = dla.py(f"""
import json
from apps.transport.models import *
c = Colis.objects.get(numero="{r['dla_vente']['colis']}")
c.reverser_contre_remboursement()
t = Troncon.objects.get(billet__numero="{r['dla_vente']['billet_corr']}", ordre=2)
print(json.dumps({{"statut": c.statut, "livre_site": c.livre_site,
                   "compte": c.ecriture_reversement.lignes.get(debit=50000).compte.numero,
                   "troncon2": [t.statut, t.vehicule.immatriculation if t.vehicule else None, t.site_effectue]}}))""")
    lot2 = lots_de(dla.manage("echanges", "exporter", "--dossier", str(travail)))[0]
    siege.manage("echanges", "importer", lot2)
    r["siege_consolide"] = siege.py("""
import json
from decimal import Decimal
from apps.comptabilite.models import Ecriture, LigneEcriture
from apps.transport.models import Billet
def solde(prefixe):
    return str(sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero__startswith=prefixe)), Decimal(0)))
from apps.garage.models import PleinCarburant
def vehicule_charge(immat, compte):
    return str(sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero=compte, vehicule__immatriculation=immat)), Decimal(0)))
def vehicule(immat):
    return str(-sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero="70611", vehicule__immatriculation=immat)), Decimal(0)))
print(json.dumps({"ecritures": Ecriture.objects.filter(site_origine__in=["DLA", "YDE", "BTA"]).count(),
                  "billets_a_voyager": solde("41911"), "recette_LT101": vehicule("LT 101 AA"), "recette_EN202": vehicule("EN 202 BB"),
                  "recette_LT303": vehicule("LT 303 CC"),
                  "journaux": sorted(set(Ecriture.objects.exclude(site_origine="").values_list("journal__code", flat=True))),
                  "liaisons_185": solde("185"), "produits_70611": solde("70611"), "produits_70612": solde("70612"),
                  "caisse": solde("57"), "billets": Billet.objects.count(),
                  "carburant_EN202": vehicule_charge("EN 202 BB", "6053"), "pleins": list(PleinCarburant.objects.values_list("litres", flat=True).order_by("pk"))}, default=str))""")
    # Lot altéré : refusé
    octets = bytearray(Path(lot2).read_bytes())
    octets[len(octets) // 2] ^= 0xFF
    altere = travail / "altere.erpx"
    altere.write_bytes(bytes(octets))
    try:
        siege.manage("echanges", "importer", str(altere))
        r["altere"] = "accepté"
    except RuntimeError as exc:
        r["altere"] = str(exc).splitlines()[-1]
    return r


if __name__ == "__main__":
    print(json.dumps(executer(sys.argv[1]), ensure_ascii=False, indent=1))
