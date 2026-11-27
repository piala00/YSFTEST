"""Tests unitaires de l'affectation des classes au runner SQL Server."""
import importlib.util
from pathlib import Path
import unittest

RACINE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sqlserver_test_runner", RACINE / "tests_navigateur" / "sqlserver_test_runner.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
shard_for_class = MODULE.shard_for_class


class SqlServerPartitionTests(unittest.TestCase):
    def test_classes_lentes_deplacees_vers_le_shard_le_moins_charge(self):
        attendus = {
            "apps.transport.tests.SimulationPlusieursMoisTests": 0,
            "apps.core.tests_base_donnees.BaseSQLServerTests": 1,
            "apps.core.tests_administration_onglets.AdministrationOngletsTests": 1,
            "apps.echanges.tests.ScenarioTroisDossiersTests": 0,
            "apps.echanges.tests_synchro.SynchronisationRelaisInternetTests": 0,
        }
        for classe, shard in attendus.items():
            with self.subTest(classe=classe):
                self.assertEqual(shard_for_class(classe, 2), shard)

    def test_une_classe_est_affectee_a_un_seul_shard(self):
        classes = [
            "apps.transport.tests.SimulationPlusieursMoisTests",
            "apps.core.tests_base_donnees.BaseSQLServerTests",
            "apps.core.tests_administration_onglets.AdministrationOngletsTests",
            "apps.echanges.tests.ScenarioTroisDossiersTests",
            "apps.echanges.tests_synchro.SynchronisationRelaisInternetTests",
            "apps.core.tests_reprise_sage.RepriseSageTests",
            "apps.transport.tests.PlanAnalytiqueCompletTests",
        ]
        for classe in classes:
            affectations = [shard_for_class(classe, 2) == n for n in (0, 1)]
            self.assertEqual(sum(affectations), 1, classe)

    def test_hachage_reste_stable_pour_les_autres_matrices(self):
        classe = "apps.transport.tests.ReportingSurLesEtatsTests"
        self.assertEqual(shard_for_class(classe, 2), shard_for_class(classe, 2))
        self.assertEqual(shard_for_class(classe, 1), 0)
        self.assertEqual(shard_for_class(classe, 3), int.from_bytes(
            __import__("hashlib").sha256(classe.encode()).digest()[:8], "big"
        ) % 3)

    def test_nombre_de_shards_invalide_refuse(self):
        with self.assertRaises(ValueError):
            shard_for_class("apps.core.tests.Exemple", 0)


class SqlServerMetricsTests(unittest.TestCase):
    def test_agregation_des_durees_compte_maximum_erreurs_et_imbrication(self):
        mesures = {}
        MODULE._enregistrer_mesure(mesures, "atomic_scope", 1.25)
        MODULE._enregistrer_mesure(mesures, "atomic_scope", 0.50, failed=True, nested=True)
        self.assertEqual(mesures["atomic_scope"]["count"], 2)
        self.assertAlmostEqual(mesures["atomic_scope"]["total"], 1.75)
        self.assertAlmostEqual(mesures["atomic_scope"]["max"], 1.25)
        self.assertEqual(mesures["atomic_scope"]["errors"], 1)
        self.assertEqual(mesures["atomic_scope"]["nested"], 1)

    def test_alias_none_est_normalise_vers_default(self):
        class AtomicSansAlias:
            using = None

        class ConnexionSqlServer:
            alias = "sqlserver"

        self.assertEqual(MODULE._alias_pour_base(AtomicSansAlias()), "default")
        self.assertEqual(MODULE._alias_pour_base(ConnexionSqlServer()), "sqlserver")

    def test_wrapper_preserve_le_retour_et_mesure_la_methode(self):
        evenements = []

        class Connexion:
            alias = "default"

        def enregistrer(receiver, operation, elapsed, failed=False):
            evenements.append((receiver.alias, operation, elapsed, failed))

        def originale(self, valeur):
            return valeur + 1

        mesuree = MODULE._emballer_methode(originale, "connect", enregistrer)
        self.assertEqual(mesuree(Connexion(), 41), 42)
        self.assertEqual(len(evenements), 1)
        self.assertEqual(evenements[0][:2], ("default", "connect"))
        self.assertGreaterEqual(evenements[0][2], 0)
        self.assertFalse(evenements[0][3])

    def test_wrapper_compte_les_erreurs_sans_les_masquer(self):
        evenements = []

        class Connexion:
            alias = "sqlserver"

        def enregistrer(receiver, operation, elapsed, failed=False):
            evenements.append((receiver.alias, operation, failed))

        def originale(self):
            raise RuntimeError("échec de connexion simulé")

        mesuree = MODULE._emballer_methode(originale, "connect", enregistrer)
        with self.assertRaisesRegex(RuntimeError, "simulé"):
            mesuree(Connexion())
        self.assertEqual(evenements, [("sqlserver", "connect", True)])


if __name__ == "__main__":
    unittest.main()
