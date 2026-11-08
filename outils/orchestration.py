"""Contrôles indépendants, sans API ni lancement implicite d'assistants."""
import argparse
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    'p03': ('agent-qa-tests', ['-m', 'unittest', '-v',
        'apps.core.test_cloture_annuelle_sqlite',
        'apps.core.test_reprise_configuration_sqlite',
        'tests.test_cloture_annuelle_integrite',
        'tests.test_cloture_annuelle_transactions',
        'tests.test_cloture_transport_integration',
        'tests.test_reports_annuels_sqlite',
        'tests.test_reprise_declencheurs',
        'tests.test_reprise_gares_annuelles',
        'tests.test_cloture_django_migree']),
    'ohada': ('agent-comptabilite-ohada', ['manage.py', 'test', 'apps.comptabilite', '--noinput']),
    'transport': ('agent-transport-metier', ['manage.py', 'test', 'apps.transport', '--noinput']),
    'qa': ('agent-qa-tests', ['manage.py', 'test', '--noinput', '--parallel', '4', '-v2']),
}

def run_task(name, output, timeout):
    branch, arguments = TASKS[name]
    started = time.monotonic()
    # Chaque processus reçoit son dossier temporaire et sa base SQLite propre.
    with tempfile.TemporaryDirectory(prefix='erp-' + name + '-', dir=output, ignore_cleanup_errors=True) as tmp:
        env = dict(os.environ, TMP=tmp, TEMP=tmp, TMPDIR=tmp,
                   DB_ENGINE='sqlite', SQLITE_FICHIER=str(Path(tmp) / 'erp.sqlite3'),
                   PYTHONUTF8='1', PYTHONUNBUFFERED='1')
        for key in ('DATABASE_URL', 'MIROIR_DB_ENGINE'):
            env.pop(key, None)
        command = [sys.executable, *arguments]
        with (output / (name + '.log')).open('w', encoding='utf-8') as log:
            try:
                code = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                      stderr=subprocess.STDOUT, timeout=timeout).returncode
                status = 'reussi' if code == 0 else 'echec'
            except subprocess.TimeoutExpired:
                code, status = None, 'timeout'
            except OSError as error:
                log.write(str(error))
                code, status = None, 'erreur_execution'
    return dict(task=name, branch=branch, status=status, exit_code=code,
                seconds=round(time.monotonic()-started, 2), command=command)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tasks', nargs='*', choices=list(TASKS))
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--output', type=Path, default=ROOT / 'work' / 'preuves')
    args = parser.parse_args()
    selected = list(dict.fromkeys(args.tasks or ['p03']))
    if not args.execute:
        print(json.dumps({n: TASKS[n] for n in selected}, ensure_ascii=False, indent=2))
        return 0
    if args.timeout <= 0:
        parser.error('--timeout doit être positif')
    output = args.output.resolve() / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True, exist_ok=False)
    git = ['git', '-c', 'safe.directory=' + ROOT.as_posix()]
    revision = subprocess.run([*git, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    changes = subprocess.run([*git, 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, capture_output=True, text=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(lambda n: run_task(n, output, args.timeout), selected))
    report = dict(revision=revision.stdout.strip() or None,
                  tracked_changes=changes.stdout.splitlines(), results=results,
                  agents_actifs='non mesure; aucun assistant lance par cet outil')
    (output / 'rapport.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(output)
    return int(any(r['status'] != 'reussi' for r in results))

if __name__ == '__main__':
    sys.exit(main())
