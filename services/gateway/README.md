# Gateway (Orthanc)

## Purpose

The only AI-side system that talks to the PACS. It receives the series the PACS pushes, keeps a working copy for the AI, de-identifies copies for research (fail-closed), serves them over DICOMweb, and sends AI results back to the PACS.

## Architecture block

AI inference layer, VLAN 30. Runs as N+1 active-active nodes sharing one PostgreSQL index and SeaweedFS storage. Design: [gateway (D2)](https://jikei25.github.io/ich-architecture/decisions.html#d2), [Flow 2](https://jikei25.github.io/ich-architecture/index.html#flow-triage).

## Interfaces

| Direction | Protocol | Content |
|---|---|---|
| In from PACS | DICOM C-STORE, port 4242 | Selected CT series (export rule, retried by the PACS) |
| Out to AI worker | Stable-series event, DICOMweb (WADO-RS), port 8042 | Series for inference |
| In from AI worker | DICOMweb STOW-RS | DICOM SEG + SR |
| Out to PACS | DICOM C-STORE to AE `AI_RESULTS`, port 11113 | AI results only |
| Out to research | DICOMweb, de-identified copies only | Images for the research MONAI Label server; SEG labels back |
| Storage | PostgreSQL (index), S3 on SeaweedFS (files) | |

## Status

Code still in `ich-architecture/deploy/staging/gateway/`: Orthanc 26.9.1 image, `plugin/ai_bridge.py` (the AI worker in staging, see [`../ai-worker`](../ai-worker)), `plugin/nifti_bridge.py` and its self-test.

## Next steps

- Move the gateway image and plugins here.
- Add the fail-closed de-identification plugin step and its tests.
