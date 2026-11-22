# AI worker

## Purpose

Turns a stable CT series into AI results. For each job it reads the series from the gateway, converts it to one NIfTI volume, asks the MONAI Label server for a mask, and turns the mask into a DICOM SEG (one segment per hemorrhage subtype), an SR with the volume of each subtype, and a priority flag.

## Architecture block

AI inference layer, VLAN 30 (the "task orchestrator" in the report). Holds no PACS credentials. Design: [Flow 2](https://jikei25.github.io/ich-architecture/index.html#flow-triage), [D11](https://github.com/jikei25/ich-architecture/blob/docs/slicer-monai-architecture/decisions.html).

## Interfaces

| Direction | Protocol | Content |
|---|---|---|
| In from gateway | Stable-series event, WADO-RS | CT series |
| Out to MONAI | `POST /infer/hemorrhage?output=image`, multipart `file=series.nii.gz`, `params={"result_extension": ".nii.gz"}` | NIfTI volume (int16 HU, RAS affine) |
| In from MONAI | HTTP response | Mask on the same grid, labels 0–5 |
| Out to gateway | STOW-RS | DICOM SEG + SR |
| Out to HIS/RIS | HL7 ORU or FHIR | Priority flag |
| Out to results DB | PostgreSQL | Result metadata: model version, preprocessing hash, run time, status |

The mask must be on the same grid (shape, affine) as the volume sent; otherwise the job fails and the study shows "no AI result".

## Status

In staging this runs as the `ai_bridge.py` plugin inside Orthanc (`ich-architecture/deploy/staging/gateway/plugin/`). It currently posts to a mock AI and treats the mask as binary. The target is a separate service with its own job queue.

## Next steps

- Call the MONAI Label server (option A in the [contract](https://github.com/jikei25/ich-architecture/blob/docs/slicer-monai-architecture/slicer.html), slicer.html section 11).
- Build one SEG segment per label 1–5 and the per-subtype volumes in the SR (the AI team supplies the label table).
- Deduplicate jobs per Study Instance UID when several gateway nodes raise the same event.
