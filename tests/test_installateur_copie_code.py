"""Régression du bouton Copier le code dans l'assistant Inno Setup.

Le test vérifie le contrat du script compilé sur Windows : la réussite ne peut être
annoncée qu'après vérification d'un format texte dans le presse-papiers ; les
échecs doivent laisser le code sélectionnable et expliquer Ctrl+C.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "deploy" / "installateur" / "erp_ohada.iss").read_text(
    encoding="utf-8-sig"
)


class CopieCodeInstallateurTests(unittest.TestCase):
    def test_champ_code_visible_seulement_en_lecture_et_bouton_conditionnel(self):
        self.assertIn("ChampCodeInstallation.ReadOnly := True;", SOURCE)
        self.assertIn("BoutonCopierCode.Caption := 'Copier le code';", SOURCE)
        self.assertIn("BoutonCopierCode.Enabled := CodeInstallation <> '';", SOURCE)

    def test_copie_verifiee_et_echec_explicite(self):
        debut = SOURCE.index("procedure CopierCodeInstallation")
        fin = SOURCE.index("\nprocedure InitializeWizard", debut)
        procedure = SOURCE[debut:fin]

        self.assertIn("OuvrirPressePapiers(ChampCodeInstallation.Handle)", procedure)
        self.assertIn("ViderPressePapiers()", procedure)
        self.assertIn("FormatPressePapiersDisponible(FormatPressePapiersUnicode)", procedure)
        self.assertIn("FormatPressePapiersDisponible(FormatPressePapiersTexte)", procedure)
        self.assertIn("BoutonCopierCode.Caption := 'Copie impossible';", procedure)
        self.assertIn("Ctrl+C", procedure)

        verification = procedure.index("CopieVerifiee :=")
        confirmation = procedure.index("BoutonCopierCode.Caption := 'Code copié !'")
        self.assertLess(verification, confirmation)

    def test_focus_utilise_les_api_win32_disponibles_dans_pascal_script(self):
        self.assertIn("function DefinirFocus(Fenetre: HWND): HWND;", SOURCE)
        self.assertIn("external 'SetFocus@user32.dll stdcall';", SOURCE)
        self.assertIn("function ObtenirFocus: HWND;", SOURCE)
        self.assertIn("external 'GetFocus@user32.dll stdcall';", SOURCE)
        self.assertNotIn("ChampCodeInstallation.SetFocus", SOURCE)
        debut = SOURCE.index("procedure CopierCodeInstallation")
        fin = SOURCE.index("\nprocedure InitializeWizard", debut)
        procedure = SOURCE[debut:fin]
        self.assertIn("DefinirFocus(ChampCodeInstallation.Handle);", procedure)
        self.assertIn("ObtenirFocus() <> ChampCodeInstallation.Handle", procedure)

    def test_les_formats_windows_utilises_sont_cf_text_et_cf_unicodetext(self):
        self.assertIn("FormatPressePapiersTexte = 1;", SOURCE)
        self.assertIn("FormatPressePapiersUnicode = 13;", SOURCE)


if __name__ == "__main__":
    unittest.main()
