"""SQL Server CI runner: per-test timing and periodic stack diagnostics.

The duration log is flushed immediately so a global timeout still leaves the
name and elapsed time of the last unfinished test in GitHub Actions logs.
"""
import hashlib
import atexit
from functools import wraps
import faulthandler
import os
import subprocess
from pathlib import Path
import runpy
import signal
import sys
import time
import unittest


_ACTIVE_TEST = None
_DATABASE_METRICS_REPORTER = None


def instrument_tests():
    original_run = unittest.TestCase.run
    threshold = float(os.environ.get("SQL_TEST_SLOW_SECONDS", "15"))
    durations = []
    body_durations = {}
    active = {"name": None, "started": None}

    def report_slowest():
        if not durations:
            return
        print(f"[SQL-TEST-SUMMARY] {len(durations)} tests timed; 20 slowest:", flush=True)
        for elapsed, test_name in sorted(durations, reverse=True)[:20]:
            print(f"[SQL-TEST-TOP] {elapsed:.3f}s {test_name}", flush=True)
        # TestCase.run includes setUp/tearDown; rank that overhead separately
        # so slow fixtures are not mistaken for slow business calculations.
        overhead = [(max(0.0, elapsed - body_durations[name]), name)
                    for elapsed, name in durations if name in body_durations]
        for elapsed, name in sorted(overhead, reverse=True)[:10]:
            print(f"[SQL-TEST-OVERHEAD-TOP] {elapsed:.3f}s {name}", flush=True)

    atexit.register(report_slowest)

    # GNU timeout sends SIGTERM: atexit handlers do not run for this signal.
    # Preserve the original termination semantics while retaining diagnostics.
    def on_termination(signum, frame):
        if active["name"] is not None:
            elapsed = time.monotonic() - active["started"]
            print(f"[SQL-TEST-INCOMPLETE] {elapsed:.3f}s {active['name']}", flush=True)
        print(f"[SQL-TEST-TERMINATED] signal={signum}", flush=True)
        report_slowest()
        if _DATABASE_METRICS_REPORTER is not None:
            try:
                _DATABASE_METRICS_REPORTER()
            except Exception as exc:  # le diagnostic ne doit pas masquer SIGTERM
                print(f"[SQL-DB-REPORT-ERROR] {exc!r}", flush=True)
        faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_termination)

    def timed_run(self, result=None):
        global _ACTIVE_TEST
        test_name = unittest.TestCase.id(self)
        previous_test = _ACTIVE_TEST
        _ACTIVE_TEST = test_name
        started = time.monotonic()
        active["name"], active["started"] = test_name, started
        print(f"[SQL-TEST-START] {test_name}", flush=True)
        try:
            return original_run(self, result)
        finally:
            elapsed = time.monotonic() - started
            active["name"], active["started"] = None, None
            _ACTIVE_TEST = previous_test
            durations.append((elapsed, test_name))
            marker = "SLOW" if elapsed >= threshold else "END"
            print(f"[SQL-TEST-{marker}] {elapsed:.3f}s {test_name}", flush=True)

    unittest.TestCase.run = timed_run

    # Mesurer séparément le corps du test : TestCase.run inclut également
    # setUp/tearDown et les transactions Django. Ce marqueur permet de
    # distinguer un calcul métier lent d'une attente de fixture SQL Server.
    original_call_test_method = unittest.TestCase._callTestMethod

    def timed_test_method(self, method):
        started = time.monotonic()
        try:
            return original_call_test_method(self, method)
        finally:
            elapsed = time.monotonic() - started
            body_durations[unittest.TestCase.id(self)] = elapsed
            print(f"[SQL-TEST-BODY] {elapsed:.3f}s {unittest.TestCase.id(self)}", flush=True)

    unittest.TestCase._callTestMethod = timed_test_method

    # Django's per-test fixture lifecycle runs inside TestCase.run. Separate
    # database flush/fixture loading from the actual test method without
    # changing transaction or connection semantics.
    import inspect
    from django.test import SimpleTestCase
    for phase in ("_pre_setup", "_post_teardown"):
        # Preserve the original descriptor: Django versions may expose these
        # hooks as instance methods or classmethods. A plain function assigned
        # over a classmethod loses binding and breaks every SQL Server test.
        descriptor = inspect.getattr_static(SimpleTestCase, phase)
        is_classmethod = isinstance(descriptor, classmethod)
        original = descriptor.__func__ if is_classmethod else descriptor

        def make_timed_fixture(phase_name, original_method, class_bound):
            def timed_fixture(receiver):
                started = time.monotonic()
                try:
                    return original_method(receiver)
                finally:
                    elapsed = time.monotonic() - started
                    if elapsed >= threshold:
                        name = (receiver.__module__ + "." + receiver.__qualname__
                                if class_bound else unittest.TestCase.id(receiver))
                        print(f"[SQL-TEST-FIXTURE-SLOW] {phase_name} {elapsed:.3f}s {name}", flush=True)
            return classmethod(timed_fixture) if class_bound else timed_fixture

        setattr(SimpleTestCase, phase, make_timed_fixture(phase, original, is_classmethod))


    # Les lenteurs de setUpClass/tearDownClass ne passent pas par TestCase.run.
    # Le runner Django les déclenche via unittest.TestSuite : instrumenter ces
    # points pour distinguer préparation de données, attente SQL et test métier.
    original_class_setup = unittest.TestSuite._handleClassSetUp
    original_class_teardown = unittest.TestSuite._tearDownPreviousClass

    def timed_class_setup(self, test, result):
        global _ACTIVE_TEST
        previous = getattr(result, "_previousTestClass", None)
        current = test.__class__
        if previous is current:
            return original_class_setup(self, test, result)
        started = time.monotonic()
        prior = (active["name"], active["started"])
        prior_test = _ACTIVE_TEST
        _ACTIVE_TEST = f"setUpClass {current.__module__}.{current.__qualname__}"
        active["name"], active["started"] = f"setUpClass {current.__module__}.{current.__qualname__}", started
        print(f"[SQL-FIXTURE-START] setUpClass {current.__module__}.{current.__qualname__}", flush=True)
        try:
            return original_class_setup(self, test, result)
        finally:
            active["name"], active["started"] = prior
            _ACTIVE_TEST = prior_test
            print(f"[SQL-FIXTURE-END] setUpClass {current.__module__}.{current.__qualname__} "
                  f"{time.monotonic() - started:.3f}s", flush=True)

    def timed_class_teardown(self, test, result):
        global _ACTIVE_TEST
        previous = getattr(result, "_previousTestClass", None)
        current = test.__class__ if test is not None else None
        if previous is None or previous is current:
            return original_class_teardown(self, test, result)
        started = time.monotonic()
        name = f"{previous.__module__}.{previous.__qualname__}"
        prior = (active["name"], active["started"])
        prior_test = _ACTIVE_TEST
        _ACTIVE_TEST = f"tearDownClass {name}"
        active["name"], active["started"] = f"tearDownClass {name}", started
        print(f"[SQL-FIXTURE-START] tearDownClass {name}", flush=True)
        try:
            return original_class_teardown(self, test, result)
        finally:
            active["name"], active["started"] = prior
            _ACTIVE_TEST = prior_test
            print(f"[SQL-FIXTURE-END] tearDownClass {name} "
                  f"{time.monotonic() - started:.3f}s", flush=True)

    unittest.TestSuite._handleClassSetUp = timed_class_setup
    unittest.TestSuite._tearDownPreviousClass = timed_class_teardown


def instrument_database_lifecycle():
    """Expose the expensive Django database phases separately from test bodies."""
    from django.test.runner import DiscoverRunner

    for phase in ("setup_databases", "teardown_databases", "run_suite"):
        original = getattr(DiscoverRunner, phase)

        def timed(self, *args, _phase=phase, _original=original, **kwargs):
            started = time.monotonic()
            print(f"[SQL-PHASE-START] {_phase}", flush=True)
            try:
                return _original(self, *args, **kwargs)
            finally:
                print(
                    f"[SQL-PHASE-END] {_phase} {time.monotonic() - started:.3f}s",
                    flush=True,
                )

        setattr(DiscoverRunner, phase, timed)



def _alias_pour_base(receiver):
    """Résout l'alias Django, y compris Atomic(using=None) => default."""
    alias = getattr(receiver, "alias", None)
    if alias is None:
        alias = getattr(receiver, "using", None)
    return alias or "default"


def _enregistrer_mesure(metrics, operation, elapsed, failed=False, nested=False):
    """Agrège une opération chronométrée sans conserver de données sensibles."""
    metric = metrics.setdefault(operation, {
        "count": 0, "total": 0.0, "max": 0.0, "errors": 0, "nested": 0,
    })
    metric["count"] += 1
    metric["total"] += elapsed
    metric["max"] = max(metric["max"], elapsed)
    metric["errors"] += int(failed)
    metric["nested"] += int(nested)


def _emballer_methode(original, operation, enregistrer):
    """Décore une méthode de connexion sans modifier son retour ni ses exceptions."""
    @wraps(original)
    def timed(self, *args, **kwargs):
        started = time.monotonic()
        failed = False
        try:
            return original(self, *args, **kwargs)
        except BaseException:
            failed = True
            raise
        finally:
            enregistrer(self, operation, time.monotonic() - started, failed)
    return timed


def instrument_database_activity():
    """Mesure connexions, commits/rollbacks et durées des blocs transaction.atomic."""
    global _DATABASE_METRICS_REPORTER

    if _DATABASE_METRICS_REPORTER is not None:
        return _DATABASE_METRICS_REPORTER

    from threading import local

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.transaction import Atomic

    par_alias = {}
    par_test = {}
    pile = local()
    etat = {"reported": False}

    def enregistrer(receiver, operation, elapsed, failed=False, nested=False):
        alias = _alias_pour_base(receiver)
        _enregistrer_mesure(par_alias.setdefault(alias, {}), operation, elapsed, failed, nested)
        test_name = _ACTIVE_TEST
        if test_name:
            _enregistrer_mesure(par_test.setdefault((test_name, alias), {}), operation, elapsed, failed, nested)

    for operation in ("ensure_connection", "connect", "close", "commit", "rollback",
                      "set_autocommit", "savepoint", "savepoint_commit", "savepoint_rollback"):
        original = getattr(BaseDatabaseWrapper, operation, None)
        if original is not None:
            setattr(BaseDatabaseWrapper, operation, _emballer_methode(original, operation, enregistrer))

    original_enter = Atomic.__enter__
    original_exit = Atomic.__exit__

    def timed_atomic_enter(self):
        started = time.monotonic()
        failed = False
        try:
            result = original_enter(self)
        except BaseException:
            failed = True
            raise
        finally:
            enregistrer(self, "atomic_enter", time.monotonic() - started, failed)
        transactions = getattr(pile, "transactions", [])
        alias = _alias_pour_base(self)
        nested = any(item["alias"] == alias for item in transactions)
        transactions.append({
            "id": id(self), "alias": alias,
            "started": time.monotonic(), "nested": nested,
        })
        pile.transactions = transactions
        return result

    def timed_atomic_exit(self, exc_type, exc_value, traceback):
        started = time.monotonic()
        failed = False
        try:
            return original_exit(self, exc_type, exc_value, traceback)
        except BaseException:
            failed = True
            raise
        finally:
            enregistrer(self, "atomic_exit", time.monotonic() - started, failed or exc_type is not None)
            transactions = getattr(pile, "transactions", [])
            index = next((i for i in range(len(transactions) - 1, -1, -1)
                          if transactions[i]["id"] == id(self)), None)
            if index is not None:
                transaction = transactions.pop(index)
                enregistrer(
                    self, "atomic_scope", time.monotonic() - transaction["started"],
                    failed or exc_type is not None, transaction["nested"],
                )
                pile.transactions = transactions

    Atomic.__enter__ = timed_atomic_enter
    Atomic.__exit__ = timed_atomic_exit

    def reporter():
        if etat["reported"]:
            return
        etat["reported"] = True
        try:
            _reporter_interne()
        except Exception as exc:
            import traceback
            print(f"[SQL-DB-REPORT-ERROR] {exc!r}", flush=True)
            traceback.print_exc(file=sys.stderr)

    def _reporter_interne():
        if not par_alias:
            print("[SQL-DB-SUMMARY] aucune opération de base observée", flush=True)
            return
        for alias, operations in sorted(par_alias.items(), key=lambda item: str(item[0])):
            details = []
            for operation, metric in sorted(operations.items()):
                details.append(
                    f"{operation}:n={metric['count']},total={metric['total']:.3f}s,"
                    f"max={metric['max']:.3f}s,err={metric['errors']},nested={metric['nested']}"
                )
            print(f"[SQL-DB-SUMMARY] alias={alias} " + " ".join(details), flush=True)

        def score(item):
            operations = item[1]
            return sum(metric["total"] for name, metric in operations.items()
                       if name in ("atomic_scope", "ensure_connection", "connect", "close", "commit", "rollback",
                                   "set_autocommit", "savepoint", "savepoint_commit", "savepoint_rollback"))

        for (test_name, alias), operations in sorted(par_test.items(), key=score, reverse=True)[:15]:
            tx = operations.get("atomic_scope", {})
            ensure = operations.get("ensure_connection", {})
            connect = operations.get("connect", {})
            close = operations.get("close", {})
            commit = operations.get("commit", {})
            rollback = operations.get("rollback", {})
            savepoint = operations.get("savepoint", {})
            savepoint_commit = operations.get("savepoint_commit", {})
            savepoint_rollback = operations.get("savepoint_rollback", {})
            autocommit = operations.get("set_autocommit", {})
            print(
                f"[SQL-DB-TEST-TOP] {test_name} alias={alias} "
                f"atomic={tx.get('count', 0)}/{tx.get('total', 0.0):.3f}s "
                f"atomic_max={tx.get('max', 0.0):.3f}s "
                f"nested={tx.get('nested', 0)} "
                f"ensure={ensure.get('count', 0)}/{ensure.get('total', 0.0):.3f}s "
                f"connect={connect.get('count', 0)}/{connect.get('total', 0.0):.3f}s "
                f"close={close.get('count', 0)}/{close.get('total', 0.0):.3f}s "
                f"commit={commit.get('count', 0)}/{commit.get('total', 0.0):.3f}s "
                f"rollback={rollback.get('count', 0)}/{rollback.get('total', 0.0):.3f}s "
                f"savepoint={savepoint.get('count', 0)}/{savepoint.get('total', 0.0):.3f}s "
                f"savepoint_commit={savepoint_commit.get('count', 0)}/{savepoint_commit.get('total', 0.0):.3f}s "
                f"savepoint_rollback={savepoint_rollback.get('count', 0)}/{savepoint_rollback.get('total', 0.0):.3f}s "
                f"set_autocommit={autocommit.get('count', 0)}/{autocommit.get('total', 0.0):.3f}s",
                flush=True,
            )

    _DATABASE_METRICS_REPORTER = reporter
    atexit.register(reporter)
    return reporter

def shard_for_class(key, count):
    """Affectation stable d'une classe entière, ajustée avec les durées CI observées."""
    if count < 1:
        raise ValueError("nombre de shards invalide")
    assigned = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") % count
    if count == 2:
        # Mesure réelle CI #627 (27/11/2026) :
        # shard 0 = 308 tests / 347.849s ; shard 1 = 494 tests / 668.259s.
        # SimulationPlusieursMois a pris 166.595s sur le shard 1 ; la déplacer
        # vers le shard 0 donne une charge estimée à 514.444s / 501.664s.
        # Bascule SQL Server (51.110s) et AdministrationOnglets (50.127s)
        # restent sur le shard 1. Les classes restent indivisibles pour
        # préserver setUpClass/tearDownClass.
        overrides = {
            "apps.transport.tests.SimulationPlusieursMoisTests": 0,
            "apps.core.tests_base_donnees.BaseSQLServerTests": 1,
            "apps.core.tests_administration_onglets.AdministrationOngletsTests": 1,
            "apps.echanges.tests.ScenarioTroisDossiersTests": 0,
            "apps.echanges.tests_synchro.SynchronisationRelaisInternetTests": 0,
        }
        assigned = overrides.get(key, assigned)
    return assigned


def partition_suite():
    """Partition stable par classe, sans dupliquer les fixtures Django."""
    shard = int(os.environ.get("SQL_TEST_SHARD", "0"))
    count = int(os.environ.get("SQL_TEST_SHARDS", "1"))
    if count < 1 or not 0 <= shard < count:
        raise ValueError("SQL_TEST_SHARD/SQL_TEST_SHARDS invalides")
    if count == 1:
        return
    from django.test.runner import DiscoverRunner
    original_build = DiscoverRunner.build_suite

    def build_partition(self, *args, **kwargs):
        suite = original_build(self, *args, **kwargs)
        def walk(node):
            for child in node:
                if isinstance(child, unittest.TestSuite):
                    yield from walk(child)
                else:
                    yield child
        selected = []
        for test in walk(suite):
            cls = type(test)
            key = cls.__module__ + "." + cls.__qualname__
            assigned = shard_for_class(key, count)
            if assigned == shard:
                selected.append(test)
        print(f"[SQL-SHARD] {shard + 1}/{count}: {len(selected)} tests", flush=True)
        return unittest.TestSuite(selected)
    DiscoverRunner.build_suite = build_partition


def main():
    # Sans matrice explicite, exécuter la suite entière dans un seul processus.
    # Le lancement implicite de deux SQL Server sur un même runner a causé
    # SIGBUS (-7). La matrice CI définit SQL_TEST_SHARD explicitement.
    if "SQL_TEST_SHARD" not in os.environ:
        os.environ["SQL_TEST_SHARD"] = "0"
        os.environ["SQL_TEST_SHARDS"] = "1"
    repository_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository_root))
    os.chdir(repository_root)
    os.environ.setdefault("SQL_TEST_TIMINGS", "1")
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    instrument_tests()
    instrument_database_lifecycle()
    instrument_database_activity()
    partition_suite()
    # Preserve explicit Django test labels/options for targeted diagnosis.
    # The default invocation still runs the complete assigned CI shard.
    sys.argv = ["manage.py", "test", "--noinput", "-v2", *sys.argv[1:]]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
