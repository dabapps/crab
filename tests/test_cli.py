from unittest import TestCase
from crab.cli import get_free_port, main
from crab import __version__
import subprocess
from unittest.mock import patch
import os


class CLITestCase(TestCase):
    def test_get_free_port(self):
        free_port = get_free_port()
        self.assertTrue(free_port.isdigit())

    def test_version(self):
        cmd = subprocess.run(["crab", "--version"], stdout=subprocess.PIPE)
        self.assertEqual(cmd.returncode, 0)
        self.assertIn(__version__, cmd.stdout.decode())
        self.assertIn("crab", cmd.stdout.decode())

    def test_missing_command(self):
        cmd = subprocess.run(
            ["crab", "this-command-shouldnt-exist"], stdout=subprocess.PIPE
        )
        self.assertEqual(cmd.returncode, 1)
        self.assertIn(
            'Could not find "this-command-shouldnt-exist" in your procfile or $PATH.',
            cmd.stdout.decode(),
        )


class CLIExecutionTestCase(TestCase):
    def setUp(self):
        super().setUp()

        execvpe_patcher = patch("crab.cli.os.execvpe")
        self.execvpe = execvpe_patcher.start()
        self.addCleanup(execvpe_patcher.stop)

    def test_calls_correctly(self):
        main(["echo", "hello"])
        self.assertEqual(self.execvpe.call_count, 1)
        self.assertEqual(self.execvpe.call_args[0][0], "echo")
        self.assertEqual(self.execvpe.call_args[0][1], ["echo", "hello"])

    def test_has_updated_path(self):
        main(["env"])
        self.assertEqual(self.execvpe.call_count, 1)
        path = self.execvpe.call_args[0][2]["PATH"].split(":")
        self.assertEqual(path[0], "env/bin")
        self.assertEqual(path[1], os.getcwd())

    def test_port_provided_for_web_command_in_procfile(self):
        os.environ["PROC_FILE"] = "tests/Procfile"
        main(["web"])
        provided_port = self.execvpe.call_args[0][2].get("PORT")
        self.assertTrue(provided_port and provided_port.isdigit())
        del os.environ["PROC_FILE"]

    def test_port_provided_for_command_containing_port(self):
        main(["echo", "$PORT"])
        provided_port = self.execvpe.call_args[0][2].get("PORT")
        self.assertTrue(provided_port and provided_port.isdigit())

    def test_port_provided_if_explicitly_requested(self):
        os.environ["CRAB_PROVIDE_PORT"] = "true"
        main(["echo"])
        provided_port = self.execvpe.call_args[0][2].get("PORT")
        self.assertTrue(provided_port and provided_port.isdigit())
        del os.environ["CRAB_PROVIDE_PORT"]

    def test_port_not_provided_by_default(self):
        main(["echo"])
        self.assertNotIn("PORT", self.execvpe.call_args[0][2])
