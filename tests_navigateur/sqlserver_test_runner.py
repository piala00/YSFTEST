"""SQL Server CI runner: per-test timing and periodic stack diagnostics.

The duration log is flushed immediately so a global timeout still leaves the
name and elapsed time of the last unfinished test in GitHub Actions logs.
"""
import hashlib
import faulthandler
import os
import subprocess
from pathlib import Path
import runpy
import sys
import time
import unittest


def instrument_tests():
    original_run = unittest.TestCase.run
    threshold = float(os.environ.get("SQL_TEST_SLOW_SECONDS", "15"))

    def timed_run(self, result=None):
        test_name = self.id()
        started = time.monotonic()
        print(f"[SQL-TEST-START] {test_name}", flush=True)
        try:
            return original_run(self, result)
        finally:
            elapsed = time.monotonic() - started
            marker = "SLOW" if elapsed >= threshold else "END"
            print(f"[SQL-TEST-{marker}] {elapsed:.3f}s {test_name}", flush=True)

    unittest.TestCase.run = timed_run


def partition_suite():
    """Partition stable par test, sans omettre les tests imbriqués Django."""
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
        selected = [test for test in walk(suite)
                    if int.from_bytes(hashlib.sha256(test.id().encode()).digest()[:8], "big") % count == shard]
        print(f"[SQL-SHARD] {shard + 1}/{count}: {len(selected)} tests", flush=True)
        return unittest.TestSuite(selected)
    DiscoverRunner.build_suite = build_partition


def main():
    # Chaque processus possède sa base de tests indépendante. Deux suites
    # tournent en parallèle plutôt que de dépasser la borne globale de CI.
    if "SQL_TEST_SHARD" not in os.environ:
        children = []
        for shard in range(2):
            env = os.environ.copy()
            env["SQL_TEST_SHARDS"] = "2"
            env["SQL_TEST_SHARD"] = str(shard)
            env["DB_NAME"] = f"{env.get('DB_NAME', 'ERP_ESSAI')}_SHARD_{shard}"
            print(f"[SQL-SHARD-START] {shard + 1}/2 database={env['DB_NAME']}", flush=True)
            children.append(subprocess.Popen([sys.executable, "-u", __file__], env=env))
        codes = []
        try:
            for child in children:
                codes.append(child.wait())
        except BaseException:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            for child in children:
                child.wait()
            raise
        print(f"[SQL-SHARD-RESULTS] {codes}", flush=True)
        if any(code != 0 for code in codes):
            raise SystemExit(1)
        return
    repository_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository_root))
    os.chdir(repository_root)
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    instrument_tests()
    partition_suite()
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
