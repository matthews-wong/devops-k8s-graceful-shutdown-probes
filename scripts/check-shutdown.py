#!/usr/bin/env python3
"""Check that a Deployment's shutdown timing budget is consistent.

Rules, per Deployment in manifests/:
  - terminationGracePeriodSeconds must exceed the preStop sleep plus DRAIN_SECONDS
  - every container must define startup, readiness and liveness probes
"""
import re
import sys
from pathlib import Path

import yaml

DRAIN_SECONDS = 20  # time allowed for in-flight requests after the preStop sleep
KUBE_DEFAULT_GRACE = 30
REQUIRED_PROBES = ("startupProbe", "readinessProbe", "livenessProbe")
SLEEP_RE = re.compile(r"\bsleep\s+(\d+)")


def prestop_sleep(container):
    command = (
        container.get("lifecycle", {}).get("preStop", {}).get("exec", {}).get("command", [])
    )
    match = SLEEP_RE.search(" ".join(command))
    return int(match.group(1)) if match else 0


def check_pod_spec(name, pod_spec):
    errors = []
    grace = pod_spec.get("terminationGracePeriodSeconds", KUBE_DEFAULT_GRACE)
    for container in pod_spec.get("containers", []):
        cname = f"{name}/{container['name']}"
        for probe in REQUIRED_PROBES:
            if probe not in container:
                errors.append(f"{cname}: missing {probe}")
        needed = prestop_sleep(container) + DRAIN_SECONDS
        if grace < needed:
            errors.append(
                f"{cname}: terminationGracePeriodSeconds={grace} is below "
                f"preStop sleep + drain ({needed}s)"
            )
    return errors


def check_file(path):
    errors = []
    for doc in yaml.safe_load_all(path.read_text()):
        if not doc or doc.get("kind") != "Deployment":
            continue
        name = doc["metadata"]["name"]
        errors += check_pod_spec(name, doc["spec"]["template"]["spec"])
    return errors


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path("manifests")
    errors = [e for f in sorted(root.glob("*.yaml")) for e in check_file(f)]
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if not errors:
        print(f"shutdown budget OK ({root})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
