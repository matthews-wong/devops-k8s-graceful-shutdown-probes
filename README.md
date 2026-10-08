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

## Shutdown timeline

1. The pod is marked terminating and removed from Service endpoints.
2. `preStop` sleeps 10s: kube-proxy and ingress controllers learn about the
   removal while nginx keeps answering.
3. `nginx -s quit` stops accepting connections and finishes in-flight ones.
4. If the container is still alive at `terminationGracePeriodSeconds` (45s),
   it gets SIGKILL.

`maxUnavailable: 0` with `maxSurge: 1` means a new pod must pass its
readiness probe before an old one is taken down.

`scripts/check-shutdown.py` fails when the grace period is shorter than the
`preStop` sleep plus a 20s drain allowance, or when a container lacks a
startup, readiness or liveness probe. Validated locally with kubeconform
0.6.7 against Kubernetes 1.31.0; it was not applied to a live cluster.
