"""Régressions de l'outil propriétaire : suppression ciblée, échecs disque et guide sans secret."""
import base64
import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from .tests_deux_modules import outil


class ComplementsLicencesTests(unittest.TestCase):
    def setUp(self):
        temporaire=tempfile.TemporaryDirectory();self.addCleanup(temporaire.cleanup)
        self.root=Path(temporaire.name)
        self.mdp=b'Essai-complements-fictif-2026'
        self.appeler(outil.creer_cles,self.root,mdp=self.mdp)
        self.cle=outil.charger_cle(self.root/'coffre.dat',self.mdp)
        self.licences=[self.emettre('Société Alpha'),self.emettre('Société Beta')]

    def appeler(self,fonction,*a,**kw):
        with contextlib.redirect_stdout(io.StringIO()):
            return fonction(*a,**kw)

    def emettre(self,client):
        a=SimpleNamespace(cle=str(self.root/'coffre.dat'),client=client,niu='',code='T-AAAA-BBBB-CCCC-DDDD',
            edition='transport',role='seul',site='',postes=5,definitive=True,jusqu_au=None,
            maj_jusqu_au='2030-12-31',demande=None,sortie=str(self.root),fichier=None)
        return self.appeler(outil.emettre,a,cle_deverrouillee=self.cle)

    def selection(self):
        return self.appeler(outil.preparer_suppression,self.root,outil.registre_lignes(self.root)[0]['numero'])

    def supprimer(self,selection=None):
        return self.appeler(outil.supprimer_licence,self.root,selection or self.selection(),confirme=True)

    def test_guide_dans_dossier_et_empreinte_compatible_sans_prive(self):
        texte=(self.root/'INSTALLATION_CLE_PUBLIQUE.md').read_text(encoding='utf-8')
        brute=(self.root/'parametres.dat').read_bytes()[6:]
        self.assertIn(hashlib.sha256(brute).hexdigest().upper(),texte)
        self.assertNotIn(base64.b64encode((self.root/'coffre.dat').read_bytes()).decode(),texte)
        for repere in ('Windows 10','Windows 11','Windows Server','ProgramData','Program Files',
                       'Installer la licence','64 Ko','8 Ko','ne révoque pas'):
            self.assertIn(repere,texte)

    def test_annulation_ne_modifie_aucun_fichier(self):
        avant={f.name:f.read_bytes() for f in self.root.iterdir() if f.is_file()}
        with self.assertRaises(ValueError):
            outil.supprimer_licence(self.root,self.selection(),confirme=False)
        self.assertEqual(avant,{f.name:f.read_bytes() for f in self.root.iterdir() if f.is_file()})

    def test_supprime_uniquement_selection_et_journalise_sans_reutiliser_numero(self):
        self.appeler(outil.exporter_client,self.licences[0],self.root)
        (self.root/'erp.sqlite3').write_bytes(b'donnees-metier-fictives')
        avant={f.name:f.read_bytes() for f in self.root.iterdir() if f.is_file()}
        s=self.selection();numero_suivant=outil.prochain_numero(self.root/'registre-licences.csv')
        archive=self.supprimer(s)
        self.assertEqual(archive.read_bytes(),avant[self.licences[0].name])
        self.assertFalse(self.licences[0].exists())
        for nom,contenu in avant.items():
            if nom!=self.licences[0].name:
                self.assertEqual((self.root/nom).read_bytes(),contenu,nom)
        self.assertEqual([l['client'] for l in outil.registre_lignes(self.root)],['Société Beta'])
        self.assertEqual(outil.prochain_numero(self.root/'registre-licences.csv'),numero_suivant)
        e=outil.journal_suppressions(self.root)[0]
        self.assertEqual((e['numero'],e['sha256'],e['etat']),(s['numero'],s['sha256'],'supprimee'))
        self.assertFalse((self.root/'.suppression-licences.lock').exists())

    def test_selection_perimee_apres_nouvelle_emission_refusee(self):
        s=self.selection();self.emettre('Société Gamma')
        with self.assertRaisesRegex(ValueError,'sélection a changé'):
            self.supprimer(s)
        self.assertTrue(self.licences[0].exists())
        self.assertEqual(outil.journal_suppressions(self.root),[])

    def test_fichier_ne_correspondant_pas_au_registre_refuse(self):
        self.licences[0].write_bytes(self.licences[1].read_bytes())
        with self.assertRaisesRegex(ValueError,'ne correspond pas'):
            self.selection()
        self.assertTrue(self.licences[0].exists())

    def test_numero_duplique_refuse(self):
        outil.ajouter_registre(self.root/'registre-licences.csv',outil.registre_lignes(self.root)[0])
        with self.assertRaisesRegex(ValueError,'sans doublon'):
            self.selection()

    def test_registre_ne_peut_designer_un_coffre_ou_un_fichier_exterieur(self):
        for chemin in (self.root/'coffre.dat',self.root.parent/'exterieur.erplic'):
            with mock.patch.object(outil,'registre_lignes',return_value=[{'numero':'FAUX','fichier':str(chemin)}]):
                with self.assertRaises(ValueError):
                    outil.preparer_suppression(self.root,'FAUX')
        self.assertTrue((self.root/'coffre.dat').exists())

    def test_public_altere_refuse_sans_deplacement(self):
        (self.root/'parametres.dat').write_bytes(b'ERPID\x01'+b'x'*32)
        with self.assertRaises(SystemExit):
            self.selection()
        self.assertTrue(self.licences[0].exists())

    def test_journal_impossible_interdit_deplacement(self):
        with mock.patch.object(outil,'enregistrer_suppressions',side_effect=OSError('disque plein')):
            with self.assertRaises(OSError):
                self.supprimer()
        self.assertTrue(self.licences[0].exists())
        self.assertEqual(len(outil.registre_lignes(self.root)),2)

    def test_echec_journal_final_retablit_fichier_et_trace_annulation(self):
        original=outil.enregistrer_suppressions;appels=[]
        def enregistrer(*a):
            appels.append(1)
            if len(appels)==2:
                raise OSError('disque plein à la finalisation')
            return original(*a)
        with mock.patch.object(outil,'enregistrer_suppressions',side_effect=enregistrer):
            with self.assertRaises(OSError):
                self.supprimer()
        self.assertTrue(self.licences[0].exists())
        self.assertEqual(len(outil.registre_lignes(self.root)),2)
        self.assertEqual(outil.journal_suppressions(self.root)[0]['etat'],'annulee')

    def test_echec_deplacement_conserve_fichier_et_journal(self):
        with mock.patch.object(Path,'rename',side_effect=PermissionError('fichier verrouillé')):
            with self.assertRaises(PermissionError):
                self.supprimer()
        self.assertTrue(self.licences[0].exists())
        self.assertEqual(outil.journal_suppressions(self.root)[0]['etat'],'annulee')

    def test_journal_invalide_et_operation_interrompue_refusent_suppression(self):
        journal=self.root/'journal-suppressions.json'
        journal.write_text('{"version":1,"evenements":[{}]}')
        with self.assertRaises(ValueError):
            self.selection()
        journal.unlink()
        s=self.selection()
        outil.enregistrer_suppressions(self.root,[dict(numero='INTERROMPUE',date='2026-01-01',etat='en_cours',
            fichier='ancien.erplic',sha256='0'*64,archive='corbeille-licences/ancien.erplic')])
        with self.assertRaisesRegex(ValueError,'incomplète'):
            self.supprimer(s)
        self.assertTrue(self.licences[0].exists())

    def test_liens_et_corbeille_exterieure_refuses(self):
        if os.name=='nt':
            self.skipTest('La création de liens Windows nécessite un privilège distinct ; essais liens sous Linux.')
        s=self.selection()
        cible=self.root/'parametres.dat';contenu=cible.read_bytes();cible.unlink()
        ailleurs=self.root/'public-original.dat';ailleurs.write_bytes(contenu);cible.symlink_to(ailleurs)
        with self.assertRaises(ValueError):
            self.selection()
        cible.unlink();cible.write_bytes(contenu)
        (self.root/'corbeille-licences').symlink_to(self.root.parent,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Corbeille liée'):
            self.supprimer(s)
        self.assertTrue(self.licences[0].exists())

    def test_lien_dur_ne_permet_pas_deplacer_un_fichier_partage(self):
        try:
            os.link(self.licences[0],self.root/'copie-liee.erplic')
        except OSError as exc:
            self.skipTest(f'Liens durs indisponibles : {exc}')
        with self.assertRaisesRegex(ValueError,'liée à un autre fichier'):
            self.selection()
        self.assertTrue(self.licences[0].exists())

    def test_guide_lie_ne_peut_ecraser_le_coffre(self):
        if os.name=='nt':
            self.skipTest('Création de liens symboliques testée sous Linux.')
        guide=self.root/'INSTALLATION_CLE_PUBLIQUE.md';guide.unlink()
        coffre=self.root/'coffre.dat';avant=coffre.read_bytes()
        guide.symlink_to(coffre)
        with self.assertRaises(ValueError):
            outil.ecrire_guide(self.root)
        self.assertEqual(coffre.read_bytes(),avant)
        guide.unlink();os.link(coffre,guide)
        with self.assertRaisesRegex(ValueError,'non partagé'):
            outil.ecrire_guide(self.root)
        self.assertEqual(coffre.read_bytes(),avant)

    def test_regroupement_ne_ressuscite_pas_une_licence_supprimee(self):
        archive=self.supprimer()
        destination=self.root/'regroupement'
        self.appeler(outil.regrouper_identite,self.root/'coffre.dat',destination,self.mdp)
        self.assertEqual([l['client'] for l in outil.registre_lignes(destination)],['Société Beta'])
        self.assertEqual(len(outil.registre_lignes(destination,inclure_supprimees=True)),2)
        self.assertFalse((destination/self.licences[0].name).exists())
        self.assertEqual(outil.prochain_numero(destination/'registre-licences.csv'),
                         outil.prochain_numero(self.root/'registre-licences.csv'))
        restauree=destination/self.licences[0].name
        restauree.write_bytes(archive.read_bytes())
        with self.assertRaisesRegex(SystemExit,'supprimée'):
            self.appeler(outil.exporter_client,restauree,destination)

    def test_reexport_apres_restauration_manuelle_refuse(self):
        archive=self.supprimer()
        self.licences[0].write_bytes(archive.read_bytes())
        with self.assertRaisesRegex(SystemExit,'supprimée'):
            self.appeler(outil.exporter_client,self.licences[0],self.root)


if __name__=='__main__':
    unittest.main()
