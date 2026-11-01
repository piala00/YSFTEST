"""Outil propriétaire : deux parcours indépendants, identité conservée et paquet client sans coffre."""
import base64
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from cryptography.hazmat.primitives import serialization
from apps.licences import format_cles as fc

OUTIL=Path(__file__).resolve().parents[2]/'deploy/licences/licences.py'
spec=importlib.util.spec_from_file_location('outil_licences_deux_modules',OUTIL)
outil=importlib.util.module_from_spec(spec)
spec.loader.exec_module(outil)


class DeuxModulesTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.mdp=b'Essai-proprietaire-fictif-2026'

    def appeler(self, fonction,*args,**kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return fonction(*args,**kwargs)

    def identite(self):
        self.appeler(outil.creer_cles,self.root,mdp=self.mdp)
        return outil.charger_cle(self.root/'coffre.dat',self.mdp)

    def licence(self):
        cle=self.identite()
        a=SimpleNamespace(cle=str(self.root/'coffre.dat'),client='Société fictive',niu='',code='T-AAAA-BBBB-CCCC-DDDD',
            edition='transport',role='seul',site='',postes=3,definitive=True,jusqu_au=None,maj_jusqu_au='2030-12-31',
            demande=None,sortie=str(self.root),fichier=None)
        return self.appeler(outil.emettre,a,cle_deverrouillee=cle)

    def test_installation_ne_charge_aucune_cle_et_ne_demande_aucune_societe(self):
        with mock.patch.object(outil,'charger_cle',side_effect=AssertionError('coffre interdit')):
            numero,code,f=self.appeler(outil.generer_installation,self.root)
        self.assertRegex(code,r'^[A-Z2-7]{6}(?:-[A-Z2-7]{6}){3}$')
        self.assertEqual(f.parent,self.root)
        self.assertFalse((self.root/'coffre.dat').exists())
        self.assertFalse((self.root/'parametres.dat').exists())
        n2,c2,_=self.appeler(outil.generer_installation,self.root)
        self.assertNotEqual((numero,code),(n2,c2))

    def test_code_court_n_est_pas_une_fausse_signature_installation(self):
        _,code,_=self.appeler(outil.generer_installation,self.root)
        with self.assertRaises(fc.CleInvalide):
            fc.installation_lire(code)

    def test_console_installation_sans_env_password_ni_autres_arguments(self):
        env={k:v for k,v in os.environ.items() if k!='ERP_LICENCES_MDP'}
        r=subprocess.run([sys.executable,str(OUTIL),'installation','--dossier',str(self.root)],
            env=env,input='',capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertRegex(r.stdout.strip().splitlines()[-1],r'^[A-Z2-7]{6}(?:-[A-Z2-7]{6}){3}$')
        self.assertNotIn('Mot de passe',r.stdout)
        self.assertFalse((self.root/'coffre.dat').exists())

    def test_console_cles_binaire_par_defaut(self):
        r=subprocess.run([sys.executable,str(OUTIL),'cles','--dossier',str(self.root)],
            env={**os.environ,'ERP_LICENCES_MDP':self.mdp.decode()},capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue((self.root/'coffre.dat').exists())
        self.assertEqual((self.root/'parametres.dat').read_bytes()[:6],b'ERPID\x01')
        self.assertFalse((self.root/'cle-publique.txt').exists())
        with self.assertRaises((ValueError,TypeError)):
            serialization.load_der_private_key((self.root/'coffre.dat').read_bytes(),password=None)

    def test_trois_elements_reunis_et_export_seulement_client(self):
        licence=self.licence()
        self.assertEqual(licence.parent,self.root)
        for n in ('coffre.dat','parametres.dat'):
            self.assertTrue((self.root/n).exists())
        paquet=self.appeler(outil.exporter_client,licence,self.root)
        with zipfile.ZipFile(paquet) as z:
            self.assertEqual(set(z.namelist()),{licence.name,'parametres.dat',licence.stem+'-LIRE-MOI.txt'})
            self.assertFalse(any('coffre' in n or 'prive' in n or 'registre' in n for n in z.namelist()))
            self.assertEqual(z.read('parametres.dat'),(self.root/'parametres.dat').read_bytes())
        with self.assertRaises(FileExistsError):
            self.appeler(outil.exporter_client,licence,self.root)

    def test_regroupement_ne_change_pas_l_identite_ni_le_fichier_original(self):
        ancien=self.root/'ancienne';destination=self.root/'rassemble'
        self.appeler(outil.creer_cles,ancien,noms_neutres=False,mdp=self.mdp)
        original=(ancien/'cle-privee.pem').read_bytes()
        publique=(ancien/'cle-publique.txt').read_text().strip()
        coffre=outil.regrouper_identite(ancien/'cle-privee.pem',destination,self.mdp)
        self.assertEqual(coffre.name,'coffre.dat')
        self.assertEqual(base64.b64encode((destination/'parametres.dat').read_bytes()[6:]).decode(),publique)
        self.assertEqual((ancien/'cle-privee.pem').read_bytes(),original)
        self.assertFalse((destination/'cle-publique.txt').exists())
        self.assertFalse(coffre.read_bytes().startswith(b'-----BEGIN'))
        cle=outil.charger_cle(coffre,self.mdp)
        cle.public_key().verify(cle.sign(b'essai-regroupement'),b'essai-regroupement')

    def test_regroupement_recupere_licence_et_numero_sans_recreer_l_identite(self):
        licence=self.licence()
        destination=self.root/'regroupe'
        self.appeler(outil.regrouper_identite,self.root/'coffre.dat',destination,self.mdp)
        self.assertEqual((destination/licence.name).read_bytes(),licence.read_bytes())
        self.assertEqual(outil.prochain_numero(destination/'registre-licences.csv'),outil.prochain_numero(self.root/'registre-licences.csv'))
        self.assertEqual(len(outil.registre_lignes(destination)),1)
        self.appeler(outil.regrouper_identite,self.root/'coffre.dat',destination,self.mdp)
        self.assertEqual(len(outil.registre_lignes(destination)),1)

    def test_regroupement_refuse_de_remplacer_un_autre_editeur(self):
        source=self.root/'source';destination=self.root/'dest'
        self.appeler(outil.creer_cles,source,mdp=self.mdp)
        self.appeler(outil.creer_cles,destination,mdp=self.mdp)
        avant={f.name:f.read_bytes() for f in destination.iterdir()}
        with self.assertRaises(SystemExit):
            outil.regrouper_identite(source/'coffre.dat',destination,self.mdp)
        self.assertEqual({f.name:f.read_bytes() for f in destination.iterdir()},avant)

    def test_export_refuse_licence_exterieure_et_fichier_public_altere(self):
        licence=self.licence()
        with self.assertRaises(SystemExit):
            self.appeler(outil.exporter_client,licence,self.root/'autre')
        (self.root/'parametres.dat').write_bytes(b'identite-invalide')
        with self.assertRaises(SystemExit):
            self.appeler(outil.exporter_client,licence,self.root)


if __name__=='__main__':
    unittest.main()
