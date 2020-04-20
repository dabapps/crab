from unittest import TestCase
from crab.cli import get_free_port
from crab import __version__
import subprocess


class CLITestCase(TestCase):
    def test_get_free_port(self):
        free_port = get_free_port()
        self.assertTrue(free_port.isdigit())

    def test_version(self):
        cmd = subprocess.run(["crab", "--version"], stdout=subprocess.PIPE)
        self.assertEqual(cmd.returncode, 0)
        self.assertIn(__version__, cmd.stdout.decode())
        self.assertIn("crab", cmd.stdout.decode())
