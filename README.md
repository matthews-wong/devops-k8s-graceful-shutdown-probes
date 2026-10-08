# devops-k8s-graceful-shutdown-probes

A small Deployment that shows how to roll out and shut down a web service
without dropping requests: startup/readiness/liveness probes, a `preStop`
delay so endpoints are removed before the process gets SIGTERM, and a
termination grace period that actually covers both.

## Layout

- `manifests/` - namespace, Deployment, Service
- `scripts/check-shutdown.py` - checks the timing budget across the Deployment
- `tests/` - unit tests for the checker

## Validate

    make validate
