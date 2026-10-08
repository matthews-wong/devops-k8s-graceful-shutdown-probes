import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_shutdown", Path(__file__).parent.parent / "scripts" / "check-shutdown.py"
)
check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check)

PROBE = {"httpGet": {"path": "/", "port": "http"}}


def container(sleep=None, probes=check.REQUIRED_PROBES):
    c = {"name": "web", **{p: PROBE for p in probes}}
    if sleep is not None:
        c["lifecycle"] = {"preStop": {"exec": {"command": ["/bin/sh", "-c", f"sleep {sleep}"]}}}
    return c


class ShutdownBudgetTest(unittest.TestCase):
    def test_prestop_sleep_is_parsed(self):
        self.assertEqual(check.prestop_sleep(container(sleep=10)), 10)
        self.assertEqual(check.prestop_sleep(container()), 0)

    def test_grace_covering_sleep_and_drain_passes(self):
        spec = {"terminationGracePeriodSeconds": 45, "containers": [container(sleep=10)]}
        self.assertEqual(check.check_pod_spec("web", spec), [])

    def test_short_grace_is_reported(self):
        spec = {"terminationGracePeriodSeconds": 15, "containers": [container(sleep=10)]}
        errors = check.check_pod_spec("web", spec)
        self.assertEqual(len(errors), 1)
        self.assertIn("terminationGracePeriodSeconds=15", errors[0])

    def test_default_grace_is_used_when_unset(self):
        spec = {"containers": [container(sleep=20)]}
        self.assertEqual(len(check.check_pod_spec("web", spec)), 1)

    def test_missing_probe_is_reported(self):
        spec = {"terminationGracePeriodSeconds": 45,
                "containers": [container(probes=("readinessProbe",))]}
        errors = check.check_pod_spec("web", spec)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("startupProbe" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
