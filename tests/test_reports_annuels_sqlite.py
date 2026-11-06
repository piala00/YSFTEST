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
        CREATE TABLE comptabilite_ecriture(
          id INTEGER PRIMARY KEY, journal_id INTEGER, exercice_id INTEGER,
          numero TEXT UNIQUE, date TEXT, libelle TEXT, reference TEXT,
          statut TEXT, origine TEXT, source_cle TEXT, source_empreinte TEXT,
          uid TEXT, site_origine TEXT, cree_le TEXT);
        CREATE TABLE comptabilite_ligneecriture(
          id INTEGER PRIMARY KEY, ecriture_id INTEGER, compte_id INTEGER,
          tiers_id INTEGER, libelle TEXT, debit DECIMAL, credit DECIMAL,
          lettrage TEXT, source_cle TEXT);
        INSERT INTO core_exercice VALUES(1,0);
        INSERT INTO comptabilite_compte VALUES(1,'4111000');
        INSERT INTO comptabilite_compte VALUES(2,'5210000');
        INSERT INTO comptabilite_journal VALUES(1,'AN','AN');
        INSERT INTO commercial_tiers VALUES(7);
    """)
    return c


class ReportsAnnuelsTests(unittest.TestCase):
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

    def test_refuse_balance_desequilibree(self):
        n, suivant = base(), base()
        n.execute("INSERT INTO comptabilite_ecriture(id, exercice_id, statut) VALUES(1,1,'VALIDEE')")
        n.execute("INSERT INTO comptabilite_ligneecriture(ecriture_id,compte_id,debit,credit) VALUES(1,1,100,0)")
        with self.assertRaisesRegex(ValueError,"déséquilibrée"):
            reporter_balance_validee(n,suivant,1,1,'2027-01-01')
        self.assertEqual(suivant.execute("SELECT COUNT(*) FROM comptabilite_ecriture").fetchone()[0],0)


if __name__ == "__main__":
    unittest.main()
