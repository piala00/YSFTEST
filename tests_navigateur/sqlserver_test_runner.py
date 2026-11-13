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


def instrument_tests():
    original_run = unittest.TestCase.run
    threshold = float(os.environ.get("SQL_TEST_SLOW_SECONDS", "15"))
    durations = []
    active = {"name": None, "started": None}

    def report_slowest():
        if not durations:
            return
        print(f"[SQL-TEST-SUMMARY] {len(durations)} tests timed; 20 slowest:", flush=True)
        for elapsed, test_name in sorted(durations, reverse=True)[:20]:
            print(f"[SQL-TEST-TOP] {elapsed:.3f}s {test_name}", flush=True)

    atexit.register(report_slowest)

    # GNU timeout sends SIGTERM: atexit handlers do not run for this signal.
    # Preserve the original termination semantics while retaining diagnostics.
    def on_termination(signum, frame):
        if active["name"] is not None:
            elapsed = time.monotonic() - active["started"]
            print(f"[SQL-TEST-INCOMPLETE] {elapsed:.3f}s {active['name']}", flush=True)
        print(f"[SQL-TEST-TERMINATED] signal={signum}", flush=True)
        report_slowest()
        faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_termination)

    def timed_run(self, result=None):
        test_name = self.id()
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

    unittest.TestCase.run = timed_run

    # Django's per-test fixture lifecycle runs inside TestCase.run. Separate
    # database flush/fixture loading from the actual test method without
    # changing transaction or connection semantics.
    from django.test import SimpleTestCase
    for phase in ("_pre_setup", "_post_teardown"):
        original = getattr(SimpleTestCase, phase)

        def timed_fixture(self, _phase=phase, _original=original):
            started = time.monotonic()
            try:
                # Django declares these hooks as classmethods. getattr() returns
                # an already-bound method, so passing self adds an invalid arg.
                return _original.__func__(type(self)) if isinstance(getattr(_original, "__self__", None), type) else _original(self)
            finally:
                elapsed = time.monotonic() - started
                if elapsed >= threshold:
                    print(f"[SQL-TEST-FIXTURE-SLOW] {_phase} {elapsed:.3f}s {self.id()}", flush=True)

        setattr(SimpleTestCase, phase, timed_fixture)


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
        started = time.monotonic()
        prior = (active["name"], active["started"])
        active["name"], active["started"] = f"setUpClass {current.__module__}.{current.__qualname__}", started
        print(f"[SQL-FIXTURE-START] setUpClass {current.__module__}.{current.__qualname__}", flush=True)
        try:
            return original_class_setup(self, test, result)
        finally:
            active["name"], active["started"] = prior
            print(f"[SQL-FIXTURE-END] setUpClass {current.__module__}.{current.__qualname__} "
                  f"{time.monotonic() - started:.3f}s", flush=True)

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
            assigned = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") % count
            # CI #461: shard 1 took 829s vs 440s on shard 0. The multi-month
            # simulation class alone contained a 168s test. Move the entire
            # class (not individual tests) to the lighter shard, preserving
            # class fixtures and full coverage. Other shard counts keep hashing.
            if count == 2 and key == "apps.transport.tests.SimulationPlusieursMoisTests":
                assigned = 0
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
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
