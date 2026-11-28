"""Trois dossiers fictifs : transvasement, frais payés et port dû encaissé à destination."""
from pathlib import Path
from .scenario import Dossier, lots_de


def executer(travail):
    travail = Path(travail)
    if any(travail.iterdir()):
        raise ValueError("La recette exige un dossier de travail vide.")
    siege, depart, arrivee = (Dossier(travail, n) for n in ("siege", "douala", "yaounde"))
    for dossier in (siege, depart, arrivee):
        dossier.creer()
    siege.manage("echanges", "siege", "--code", "SIEGE", "--nom", "Siège fictif")
    for code in ("DLA", "YDE"):
        siege.manage("echanges", "agence", "--code", code, "--nom", code + " fictif")
    siege.py('''
import json
from apps.core.models import Agence
from apps.transport.models import Gare,Ligne,Vehicule,Chauffeur
for code in ('DLA','YDE'):
 Gare.objects.create(code=code,nom=code+' fictif',agence=Agence.objects.get(code=code))
Ligne.objects.create(code='DLA-YDE',gare_depart=Gare.objects.get(code='DLA'),gare_arrivee=Gare.objects.get(code='YDE'),prix_billet=6000)
for immat in ('REPRO-INITIAL','REPRO-SECOURS'):
 Vehicule.objects.create(immatriculation=immat,nombre_places=40)
Chauffeur.objects.create(nom='Chauffeur fictif')
print('null')''')
    for code, dossier in (("DLA", depart), ("YDE", arrivee)):
        installation = lots_de(siege.manage("echanges", "installation", "--agence", code, "--dossier", str(travail)))[0]
        dossier.manage("echanges", "installer", installation)
    depart.py('''
import json,datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.comptabilite.models import Compte,Journal
from apps.comptabilite.services import creer_ecriture
from apps.transport.models import Depart,Ligne,Vehicule,Chauffeur,Colis,Gare
from apps.transport.models_incidents import Incident,FraisIncident
a=get_user_model().objects.create_superuser('agent-imprevu-fictif','','Fictif-2026')
j=Journal.objects.get(code='CA')
creer_ecriture(j,timezone.localdate(),'Apport fictif',[
 {'compte':j.compte_tresorerie,'debit':10000},{'compte':Compte.objects.get(numero='1010000'),'credit':10000}])
d=Depart.objects.create(ligne=Ligne.objects.get(code='DLA-YDE'),vehicule=Vehicule.objects.get(immatriculation='REPRO-INITIAL'),
 chauffeur=Chauffeur.objects.first(),date=timezone.localdate(),heure=datetime.time(7))
c=Colis(gare_depart=Gare.objects.get(code='DLA'),gare_arrivee=Gare.objects.get(code='YDE'),expediteur='E fictif',
 destinataire='D fictif',prix=2500,port=Colis.DU).enregistrer(a)
c.charger(d);d.partir()
i=Incident.transborder(d,40,Vehicule.objects.get(immatriculation='REPRO-SECOURS'),'Étape fictive','Panne fictive',a)
compte=Compte.objects.get_or_create(numero='6240000',defaults={'intitule':'Entretien fictif'})[0]
FraisIncident(incident=i,nature=FraisIncident.DEPANNAGE,libelle='Remorquage fictif',montant=1000,compte=compte,caisse=j).enregistrer()
print('null')''')
    lot = lots_de(depart.manage("echanges", "exporter", "--dossier", str(travail)))[0]
    siege.manage("echanges", "importer", lot)
    siege.manage("echanges", "importer", lot)
    relais = lots_de(siege.manage("echanges", "exporter", "--vers", "YDE", "--dossier", str(travail)))[0]
    arrivee.manage("echanges", "importer", relais)
    arrivee.manage("echanges", "importer", relais)
    resultats = {"destination": arrivee.py('''
import json
from django.core.exceptions import ValidationError
from apps.transport.models import Colis,Depart
from apps.transport.models_incidents import Incident,FraisIncident
from apps.comptabilite.models import Ecriture
c=Colis.objects.get();d=Depart.objects.get();d.arriver();c.refresh_from_db()
c.livrer(c.code_retrait,'Destinataire fictif')
try:
 c.livrer(c.code_retrait,'Destinataire fictif')
except ValidationError:
 pass
else:
 raise AssertionError('La livraison répétée doit être refusée')
i=Incident.objects.get()
lignes=list(c.ecriture_livraison.lignes.filter(credit__gt=0).values_list('vehicule__immatriculation','credit'))
print(json.dumps({'imprevus':Incident.objects.count(),'frais_locaux':FraisIncident.objects.count(),
 'credits':{k:str(v) for k,v in lignes},'total_credits':str(sum(v for _,v in lignes)),
 'ecritures':Ecriture.objects.count(),'trace':i.trace_origine,'auteur_local':i.cree_par_id}))''')}
    retour = lots_de(arrivee.manage("echanges", "exporter", "--dossier", str(travail)))[0]
    siege.manage("echanges", "importer", retour)
    siege.manage("echanges", "importer", retour)
    resultats["central"] = siege.py('''
import json
from decimal import Decimal
from django.db.models import Sum
from apps.comptabilite.models import Ecriture,LigneEcriture
from apps.transport.models import ParametresTransport
from apps.transport.models_incidents import Incident,FraisIncident
p=ParametresTransport.get()
credits={}
for immat,m in LigneEcriture.objects.filter(compte=p.compte_colis).values_list('vehicule__immatriculation','credit'):
 credits[immat]=credits.get(immat,Decimal('0'))+m
i=Incident.objects.get()
print(json.dumps({'imprevus':Incident.objects.count(),'frais_locaux':FraisIncident.objects.count(),'ecritures':Ecriture.objects.count(),
 'depannage':str(LigneEcriture.objects.filter(compte__numero='6240000').aggregate(s=Sum('debit'))['s'] or 0),
 'credits':{k:str(v) for k,v in credits.items()},'trace':i.trace_origine}))''')
    return resultats
