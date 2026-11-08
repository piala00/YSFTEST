"""Tests ciblés du report de balance annuelle (SQLite sans Django)."""
import sqlite3
import unittest

from apps.core.reports_annuels_sqlite import reporter_balance_validee


def base():
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE core_exercice(id INTEGER PRIMARY KEY, cloture INTEGER);
        CREATE TABLE comptabilite_compte(id INTEGER PRIMARY KEY, numero TEXT);
        CREATE TABLE comptabilite_journal(id INTEGER PRIMARY KEY, code TEXT, type_journal TEXT);
        CREATE TABLE commercial_tiers(id INTEGER PRIMARY KEY);
        CREATE TABLE comptabilite_sectionanalytique(id INTEGER PRIMARY KEY);
        CREATE TABLE transport_vehicule(id INTEGER PRIMARY KEY);
        CREATE TABLE comptabilite_ecriture(
          id INTEGER PRIMARY KEY, journal_id INTEGER, exercice_id INTEGER,
          numero TEXT UNIQUE, date TEXT, libelle TEXT, reference TEXT,
          statut TEXT, origine TEXT, source_cle TEXT, source_empreinte TEXT,
          uid TEXT, site_origine TEXT, cree_le TEXT);
        CREATE TABLE comptabilite_ligneecriture(
          id INTEGER PRIMARY KEY, ecriture_id INTEGER, compte_id INTEGER,
          tiers_id INTEGER, section_id INTEGER, vehicule_id INTEGER, libelle TEXT, debit DECIMAL, credit DECIMAL,
          lettrage TEXT, source_cle TEXT);
        INSERT INTO core_exercice VALUES(1,0);
        INSERT INTO comptabilite_compte VALUES(1,'4111000');
        INSERT INTO comptabilite_compte VALUES(2,'5210000');
        INSERT INTO comptabilite_journal VALUES(1,'AN','AN');
        INSERT INTO commercial_tiers VALUES(7);
        INSERT INTO comptabilite_sectionanalytique VALUES(8);
        INSERT INTO transport_vehicule VALUES(9);
    """)
    return c


class ReportsAnnuelsTests(unittest.TestCase):
    def test_refuse_date_ouverture_non_conforme(self):
        n, suivant = base(), base()
        for date_invalide in ("2027-02-01", "2027-01-02", "2027-13-01", "2027-1-1"):
            with self.subTest(date=date_invalide):
                with self.assertRaisesRegex(ValueError, "date d'ouverture"):
                    reporter_balance_validee(n, suivant, 1, 1, date_invalide)
        self.assertEqual(suivant.execute(
            "SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 0)

    def test_refuse_annee_an_incompatible_avec_exercice_cible(self):
        n, suivant = base(), base()
        suivant.execute("ALTER TABLE core_exercice ADD COLUMN code TEXT")
        suivant.execute("UPDATE core_exercice SET code='2028'")
        with self.assertRaisesRegex(ValueError, "année de la pièce AN"):
            reporter_balance_validee(n, suivant, 1, 1, "2027-01-01")
        self.assertEqual(suivant.execute(
            "SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 0)

    def test_report_equilibre_et_tiers(self):
        n, suivant = base(), base()
        n.execute("""INSERT INTO comptabilite_ecriture
          (id, exercice_id, statut) VALUES(1,1,'VALIDEE')""")
        n.executemany("""INSERT INTO comptabilite_ligneecriture
          (ecriture_id, compte_id, tiers_id, debit, credit) VALUES(1,?,?,?,?)""",
          [(1,7,100,0),(2,None,0,100)])
        self.assertEqual(reporter_balance_validee(n,suivant,1,1,'2027-01-01'),2)
        self.assertEqual(suivant.execute(
            "SELECT statut FROM comptabilite_ecriture WHERE numero='AN-2027-OUVERTURE'"
        ).fetchone()[0], 'VALIDEE')
        self.assertEqual(suivant.execute(
            "SELECT tiers_id FROM comptabilite_ligneecriture WHERE compte_id=1"
        ).fetchone()[0],7)
        with self.assertRaisesRegex(ValueError, "déjà présents"):
            reporter_balance_validee(n,suivant,1,1,'2027-01-01')

    def test_reports_preservent_ventilation_analytique_et_vehicule(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.executemany("""INSERT INTO comptabilite_ligneecriture
          (ecriture_id, compte_id, tiers_id, section_id, vehicule_id, debit, credit)
          VALUES (1,?,?,?,?,?,?)""", [
            (1,7,8,9,60,0), (1,7,None,None,40,0),
            (2,None,None,None,0,100),
        ])
        self.assertEqual(reporter_balance_validee(n, suivant, 1, 1, '2027-01-01'), 3)
        lignes = suivant.execute("""SELECT section_id, vehicule_id, debit
            FROM comptabilite_ligneecriture WHERE compte_id=1 ORDER BY id""").fetchall()
        self.assertCountEqual(lignes, [(8,9,60), (None,None,40)])

    def test_refuse_vehicule_absent_sans_ecriture_partielle(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.executemany("""INSERT INTO comptabilite_ligneecriture
          (ecriture_id, compte_id, vehicule_id, debit, credit)
          VALUES (1,?,?,?,?)""", [(1,9,100,0), (2,None,0,100)])
        suivant.execute("DELETE FROM transport_vehicule WHERE id=9")
        with self.assertRaisesRegex(ValueError, "véhicule manquant"):
            reporter_balance_validee(n, suivant, 1, 1, '2027-01-01')
        self.assertEqual(suivant.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 0)

    def test_refuse_balance_desequilibree(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.execute("INSERT INTO comptabilite_ligneecriture(ecriture_id,compte_id,debit,credit) VALUES(1,1,100,0)")
        with self.assertRaisesRegex(ValueError,"déséquilibrée"):
            reporter_balance_validee(n,suivant,1,1,'2027-01-01')
        self.assertEqual(suivant.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0],0)


    def test_refuse_comptes_de_gestion_non_soldes(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_compte VALUES(3,'6010000')")
        n.execute("INSERT INTO comptabilite_compte VALUES(4,'7010000')")
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.executemany("""INSERT INTO comptabilite_ligneecriture
          (ecriture_id, compte_id, debit, credit) VALUES(1,?,?,?)""",
          [(3,100,0),(4,0,100)])
        with self.assertRaisesRegex(ValueError, "comptes de gestion non soldés"):
            reporter_balance_validee(n,suivant,1,1,'2027-01-01')
        self.assertEqual(suivant.execute(
            "SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 0)

    def test_report_decimal_exact_sur_grand_montant(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.executemany("""INSERT INTO comptabilite_ligneecriture
          (ecriture_id, compte_id, tiers_id, debit, credit) VALUES(1,?,?,?,?)""",
          [(1,7,'999999999999.99',0),(2,None,0,'999999999999.99')])
        self.assertEqual(reporter_balance_validee(n,suivant,1,1,'2027-01-01'),2)
        lignes = suivant.execute(
            "SELECT debit,credit FROM comptabilite_ligneecriture ORDER BY compte_id").fetchall()
        self.assertEqual(str(lignes[0][0]), '999999999999.99')
        self.assertEqual(str(lignes[1][1]), '999999999999.99')


    def test_refuse_deux_pieces_desequilibrees_qui_se_compensent(self):
        n, suivant = base(), base()
        n.executemany(
            "INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(?,1,'VALIDEE')",
            [(1,), (2,)],
        )
        n.executemany(
            "INSERT INTO comptabilite_ligneecriture(ecriture_id, compte_id, debit, credit) VALUES(?,?,?,?)",
            [(1, 1, 100, 0), (2, 2, 0, 100)],
        )
        with self.assertRaisesRegex(ValueError, "pièce validée déséquilibrée"):
            reporter_balance_validee(n, suivant, 1, 1, "2027-01-01")
        self.assertEqual(suivant.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0], 0)

    def test_refuse_piece_validee_sans_ligne(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        with self.assertRaisesRegex(ValueError, "sans ligne"):
            reporter_balance_validee(n, suivant, 1, 1, "2027-01-01")


if __name__ == "__main__":
    unittest.main()
