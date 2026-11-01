"""Mesure reproductible sur base SQLite jetable, profil complet, 250 départs réels à échelle réduite."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time

RACINE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RACINE))


def main():
    with tempfile.TemporaryDirectory(prefix='erp-mesure-simulation-') as t:
        os.environ.update(DJANGO_SETTINGS_MODULE='erp.settings',DB_ENGINE='sqlite',DATABASE_URL='',MIROIR_DB_ENGINE='',
                          SQLITE_FICHIER=str(Path(t)/'simulation-volume.sqlite3'),CONTROLE_HEURE_DEPART='0')
        import django
        django.setup()
        from django.core.management import call_command
        from apps.transport.management.commands.simulation import Command
        from apps.core import dossiers_simulation as ds
        debut=time.perf_counter()
        call_command('migrate',interactive=False,verbosity=0)
        rapport=Path(os.environ.get('RUNNER_TEMP',t))/'simulation-volume'
        rapport.mkdir(exist_ok=True)
        c=Command()
        call_command(c,mois='2026-09',jours=1,vehicules=60,salaries=25,echelle=.05,departs_jour=250,
                     scenarios_complets=True,forcer=True,rapport=str(rapport/'BILAN-SIMULATION.md'),
                     journal_scenarios=str(rapport/'SCENARIOS-SIMULATION.json'),stdout=io.StringIO())
        assert c.compteurs['voyages']==250,c.compteurs
        assert all(ok for _,ok in c.controles),c.controles
        (rapport/'MESURE.json').write_text(json.dumps({'fictif':True,'jours':1,'departs':250,'echelle':.05,'salaries_demandes':25,
            'global_secondes_incluant_migrations_et_fin_de_mois':round(time.perf_counter()-debut,3),
            'journalier':c.mesures,'note':'Mesure CI à 5 % du remplissage ; ne prédit pas un mois complet à 100 %.'},ensure_ascii=False,indent=2))
        # Livrer un exemple de dossier importable, avec ses rapports et sans identifiants d'origine.
        identifiant,dossier=ds.creer(Path(t)/'distribution','2026-09','1',
            {'departs_jour':250,'echelle':.05,'scenarios_complets':True})
        from django.db import connection
        connection.close()
        import shutil
        shutil.copyfile(Path(t)/'simulation-volume.sqlite3',dossier/ds.BASE)
        for nom in ds.RAPPORTS:
            shutil.copyfile(rapport/nom,dossier/nom)
        ds.terminer(dossier)
        with ds.exporter(Path(t)/'distribution',identifiant) as archive:
            (rapport/'SIMULATION-250-DEPARTS-ESSAI.erpsim').write_bytes(archive.read())
        print('250 départs, scénarios complets et rapprochements OK : '+json.dumps(c.mesures))


if __name__=='__main__':
    main()
