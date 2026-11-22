# Local dev stack

## Purpose

One Docker Compose file that runs the whole system on a single machine, for development and demos: PACS, gateway, AI worker, MONAI Label (CPU or a local GPU), triage API and the simulators in [`tools`](../../tools).

## Status

Not started. Today the closest thing is `ich-architecture/poc/viewer/docker-compose.yml` (OHIF PoC with a simulated AI) and the "local test on one machine" section of the staging README.

## Next steps

- Reuse the staging images with one shared network and published ports on localhost.
- Document the 3D Slicer setup on Windows against this stack, including WSL2 networking for MONAI Label.
