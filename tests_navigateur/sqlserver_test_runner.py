"""SQL Server CI runner: per-test timing and periodic stack diagnostics.

The duration log is flushed immediately so a global timeout still leaves the
name and elapsed time of the last unfinished test in GitHub Actions logs.
"""
import hashlib
import atexit
import faulthandler
import os
import subprocess
from pathlib import Path
import runpy
import signal
import sys
import time
import unittest
from threading import Lock, local


def instrument_tests():
    original_run = unittest.TestCase.run
    threshold = float(os.environ.get("SQL_TEST_SLOW_SECONDS", "15"))
    durations = []
    body_durations = {}
    active = {"name": None, "started": None}
    resources = {}
    resource_lock = Lock()
    atomic_local = local()

    def _resource_record(name, kind, elapsed, alias=None, exceptional=False, rollback=False):
        """Agrège les ouvertures/fermetures réelles et les blocs atomic, par test ou fixture."""
        with resource_lock:
            data = resources.setdefault(name, {
                "connects": 0, "connect_seconds": 0.0, "connect_max": 0.0,
                "closes": 0, "close_seconds": 0.0, "close_max": 0.0,
                "atomic_blocks": 0, "atomic_seconds": 0.0, "atomic_max": 0.0,
                "atomic_exceptions": 0, "atomic_rollbacks": 0, "aliases": set(),
            })
            if kind == "connect":
                data["connects"] += 1
                data["connect_seconds"] += elapsed
                data["connect_max"] = max(data["connect_max"], elapsed)
            elif kind == "close":
                data["closes"] += 1
                data["close_seconds"] += elapsed
                data["close_max"] = max(data["close_max"], elapsed)
            elif kind == "atomic":
                data["atomic_blocks"] += 1
                data["atomic_seconds"] += elapsed  # durée inclusive : les atomic imbriqués se recouvrent
                data["atomic_max"] = max(data["atomic_max"], elapsed)
                data["atomic_exceptions"] += int(exceptional)
                data["atomic_rollbacks"] += int(rollback)
            if alias:
                data["aliases"].add(alias)

    def report_resource(name):
        with resource_lock:
            data = resources.get(name)
            if not data:
                return
            data = {**data, "aliases": sorted(data["aliases"])}
        if not (data["connects"] or data["closes"] or data["atomic_blocks"]):
            return
        print(
            f"[SQL-RESOURCE] {name} "
            f"connects={data['connects']} connect={data['connect_seconds']:.3f}s max_connect={data['connect_max']:.3f}s "
            f"closes={data['closes']} close={data['close_seconds']:.3f}s max_close={data['close_max']:.3f}s "
            f"atomic={data['atomic_blocks']} atomic_inclusive={data['atomic_seconds']:.3f}s "
            f"max_atomic={data['atomic_max']:.3f}s exceptions={data['atomic_exceptions']} "
            f"rollbacks={data['atomic_rollbacks']} aliases={','.join(data['aliases']) or '-'}",
            flush=True,
        )

    def report_resources():
        with resource_lock:
            items = [(name, {**data, "aliases": sorted(data["aliases"])}) for name, data in resources.items()]
        if not items:
            return
        totals = {key: sum(data[key] for _, data in items) for key in (
            "connects", "connect_seconds", "closes", "close_seconds", "atomic_blocks",
            "atomic_seconds", "atomic_exceptions", "atomic_rollbacks")}
        print(
            f"[SQL-RESOURCE-SUMMARY] connections_opened={totals['connects']} "
            f"open_seconds={totals['connect_seconds']:.3f} connections_closed={totals['closes']} "
            f"close_seconds={totals['close_seconds']:.3f} atomic_blocks={totals['atomic_blocks']} "
            f"atomic_inclusive_seconds={totals['atomic_seconds']:.3f} "
            f"atomic_exceptions={totals['atomic_exceptions']} atomic_rollbacks={totals['atomic_rollbacks']}",
            flush=True,
        )
        for name, data in sorted(items, key=lambda item: item[1]["atomic_max"], reverse=True)[:10]:
            if data["atomic_blocks"]:
                print(
                    f"[SQL-RESOURCE-ATOMIC-TOP] max={data['atomic_max']:.3f}s "
                    f"inclusive={data['atomic_seconds']:.3f}s blocks={data['atomic_blocks']} {name}",
                    flush=True,
                )
        for name, data in sorted(items, key=lambda item: item[1]["connect_max"], reverse=True)[:10]:
            if data["connects"]:
                print(
                    f"[SQL-RESOURCE-CONNECT-TOP] max={data['connect_max']:.3f}s "
                    f"total={data['connect_seconds']:.3f}s opens={data['connects']} {name}",
                    flush=True,
                )

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
    atexit.register(report_resources)

    # GNU timeout sends SIGTERM: atexit handlers do not run for this signal.
    # Preserve the original termination semantics while retaining diagnostics.
    def on_termination(signum, frame):
        if active["name"] is not None:
            elapsed = time.monotonic() - active["started"]
            print(f"[SQL-TEST-INCOMPLETE] {elapsed:.3f}s {active['name']}", flush=True)
        print(f"[SQL-TEST-TERMINATED] signal={signum}", flush=True)
        report_slowest()
        report_resources()
        faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_termination)

    def timed_run(self, result=None):
        test_name = unittest.TestCase.id(self)
        started = time.monotonic()
        active["name"], active["started"] = test_name, started
        print(f"[SQL-TEST-START] {test_name}", flush=True)
        try:
            return original_run(self, result)
        finally:
            elapsed = time.monotonic() - started
            active["name"], active["started"] = None, None
            durations.append((elapsed, test_name))
            marker = "SLOW" if elapsed >= threshold else "END"
            print(f"[SQL-TEST-{marker}] {elapsed:.3f}s {test_name}", flush=True)
            report_resource(test_name)

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
        previous = getattr(result, "_previousTestClass", None)
        current = test.__class__
        if previous is current:
            return original_class_setup(self, test, result)
        fixture_name = f"setUpClass {current.__module__}.{current.__qualname__}"
        started = time.monotonic()
        prior = (active["name"], active["started"])
        active["name"], active["started"] = fixture_name, started
        print(f"[SQL-FIXTURE-START] {fixture_name}", flush=True)
        try:
            return original_class_setup(self, test, result)
        finally:
            active["name"], active["started"] = prior
            print(f"[SQL-FIXTURE-END] {fixture_name} {time.monotonic() - started:.3f}s", flush=True)
            report_resource(fixture_name)

    def timed_class_teardown(self, test, result):
        previous = getattr(result, "_previousTestClass", None)
        current = test.__class__ if test is not None else None
        if previous is None or previous is current:
            return original_class_teardown(self, test, result)
        started = time.monotonic()
        name = f"{previous.__module__}.{previous.__qualname__}"
        prior = (active["name"], active["started"])
        active["name"], active["started"] = f"tearDownClass {name}", started
        print(f"[SQL-FIXTURE-START] tearDownClass {name}", flush=True)
        try:
            return original_class_teardown(self, test, result)
        finally:
            active["name"], active["started"] = prior
            print(f"[SQL-FIXTURE-END] tearDownClass {name} "
                  f"{time.monotonic() - started:.3f}s", flush=True)
            report_resource(f"tearDownClass {name}")

    unittest.TestSuite._handleClassSetUp = timed_class_setup
    unittest.TestSuite._tearDownPreviousClass = timed_class_teardown

    # Mesurer les connexions réellement ouvertes/fermées et les blocs transaction.atomic.
    # Les compteurs restent passifs : aucune politique de connexion ou de transaction ne change.
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.transaction import Atomic

    original_connect = BaseDatabaseWrapper.connect
    original_close = BaseDatabaseWrapper.close
    original_atomic_enter = Atomic.__enter__
    original_atomic_exit = Atomic.__exit__

    def timed_connect(self):
        deja_ouverte = self.connection is not None
        started = time.monotonic()
        try:
            return original_connect(self)
        finally:
            elapsed = time.monotonic() - started
            if not deja_ouverte and self.connection is not None:
                nom = active["name"] or "[runner]"
                alias = f"{self.alias}/{self.vendor}"
                _resource_record(nom, "connect", elapsed, alias=alias)
                if elapsed >= threshold:
                    print(f"[SQL-CONNECTION-SLOW] open {elapsed:.3f}s {alias} {nom}", flush=True)

    def timed_close(self):
        etait_ouverte = self.connection is not None
        started = time.monotonic()
        try:
            return original_close(self)
        finally:
            elapsed = time.monotonic() - started
            if etait_ouverte and self.connection is None:
                nom = active["name"] or "[runner]"
                alias = f"{self.alias}/{self.vendor}"
                _resource_record(nom, "close", elapsed, alias=alias)
                if elapsed >= threshold:
                    print(f"[SQL-CONNECTION-SLOW] close {elapsed:.3f}s {alias} {nom}", flush=True)

    def timed_atomic_enter(self):
        started = time.monotonic()
        nom = active["name"] or "[runner]"
        resultat = original_atomic_enter(self)
        piles = getattr(atomic_local, "piles", None)
        if piles is None:
            piles = {}
            atomic_local.piles = piles
        piles.setdefault(id(self), []).append((started, nom))
        return resultat

    def timed_atomic_exit(self, exc_type, exc_value, traceback):
        piles = getattr(atomic_local, "piles", {})
        pile = piles.get(id(self), [])
        entree = pile.pop() if pile else None
        if not pile:
            piles.pop(id(self), None)
        connexion = getattr(self, "connection", None)
        alias = f"{connexion.alias}/{connexion.vendor}" if connexion is not None else None
        rollback = bool(getattr(connexion, "needs_rollback", False)) if connexion is not None else False
        try:
            return original_atomic_exit(self, exc_type, exc_value, traceback)
        finally:
            if entree is not None:
                started, nom = entree
                elapsed = time.monotonic() - started
                _resource_record(
                    nom, "atomic", elapsed, alias=alias,
                    exceptional=exc_type is not None, rollback=rollback,
                )
                if elapsed >= threshold:
                    print(
                        f"[SQL-TRANSACTION-SLOW] atomic {elapsed:.3f}s "
                        f"exception={exc_type is not None} rollback={rollback} {alias or '-'} {nom}",
                        flush=True,
                    )

    BaseDatabaseWrapper.connect = timed_connect
    BaseDatabaseWrapper.close = timed_close
    Atomic.__enter__ = timed_atomic_enter
    Atomic.__exit__ = timed_atomic_exit


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
