from crab.router import get_route_for_hostname
from unittest import TestCase
import subprocess
import os


class RouterTestCase(TestCase):
    def test_get_routes(self):
        with subprocess.Popen(
            ["sleep", "5"],
            env={**os.environ, "VIRTUAL_HOST": "test.localhost", "PORT": "1234"},
        ) as subproc:
            self.assertEqual(get_route_for_hostname("test.localhost"), "1234")
            self.assertIsNone(get_route_for_hostname("not-test.localhost"))
            subproc.terminate()

    def test_multiple_routes(self):
        with subprocess.Popen(
            ["sleep", "5"],
            env={
                **os.environ,
                "VIRTUAL_HOST": "test.localhost,other-test.localhost",
                "PORT": "1234",
            },
        ) as subproc:
            self.assertEqual(get_route_for_hostname("test.localhost"), "1234")
            self.assertEqual(get_route_for_hostname("other-test.localhost"), "1234")
            self.assertIsNone(get_route_for_hostname("not-test.localhost"))
            subproc.terminate()
