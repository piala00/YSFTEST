"""CI SQL Server: periodic Python stack dumps identify stalled test/DB calls."""
import faulthandler
from pathlib import Path
import runpy
import sys


def main():
    # Executing tests_navigateur/script.py makes that directory sys.path[0],
    # unlike `python manage.py`; Django settings package must be importable.
    repository_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repository_root))
    faulthandler.enable(all_threads=True)
    faulthandler.dump_traceback_later(120, repeat=True, file=sys.stderr)
    sys.argv = ["manage.py", "test", "--noinput", "-v2"]
    try:
        runpy.run_path(str(repository_root / "manage.py"), run_name="__main__")
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
