import shutil
import subprocess
from pathlib import Path
from unittest import skipUnless
from django.conf import settings
from django.test import SimpleTestCase


class RechercheDepartJavaScriptTests(SimpleTestCase):
    @skipUnless(shutil.which('node'), 'Node nécessaire pour la recherche progressive')
    def test_filtrage_du_script_livre(self):
        p = subprocess.run([shutil.which('node'), str(Path(settings.BASE_DIR) / 'tests_js/test_recherche_depart.js')],
                           capture_output=True, text=True, timeout=25)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
