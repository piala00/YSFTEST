"""Le rapport doit refléter un échec et ne jamais réutiliser la base utilisateur."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('orchestration', Path(__file__).resolve().parents[1] / 'outils/orchestration.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class OrchestrationTests(unittest.TestCase):
    def test_echec_et_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(module.os.environ, DATABASE_URL='postgres://interdit', MIROIR_DB_ENGINE='mssql'):
                with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 7)) as run:
                    result = module.run_task('ohada', Path(tmp), 30)
            self.assertEqual(result['status'], 'echec')
            self.assertEqual(result['exit_code'], 7)
            env = run.call_args.kwargs['env']
            self.assertNotIn('DATABASE_URL', env)
            self.assertNotIn('MIROIR_DB_ENGINE', env)
            self.assertEqual(env['DB_ENGINE'], 'sqlite')
            self.assertTrue(Path(env['SQLITE_FICHIER']).is_relative_to(Path(tmp)))

    def test_timeout_ne_devient_pas_succes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(module.subprocess, 'run', side_effect=subprocess.TimeoutExpired('test', 1)):
                result = module.run_task('p03', Path(tmp), 1)
            self.assertEqual(result['status'], 'timeout')
            self.assertIsNone(result['exit_code'])
