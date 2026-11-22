# MONAI Label app

## Purpose

The MONAI Label app that holds the `hemorrhage` segmentation model (a MONAI bundle). The same app runs as two servers with different settings.

## Architecture block

AI inference (VLAN 30) and AI research (VLAN 40). Design: [D11](https://jikei25.github.io/ich-architecture/decisions.html#d11), [two servers](https://jikei25.github.io/ich-architecture/slicer.html#servers).

| | Inference server | Research server |
|---|---|---|
| Called by | AI worker only | 3D Slicer with the MONAILabel extension |
| Data | Identified volumes, during inference only | De-identified copies only |
| Datastore (`--studies`) | Empty temporary folder | Gateway DICOMweb, de-identified copies |
| Models | `hemorrhage` | `hemorrhage` plus interactive tools (SAM, scribbles) |
| Trainers, active learning | Off | On |
| Model version | Approved bundle from the registry | Latest bundle, for drafts |

## Interfaces

- `POST /infer/hemorrhage`: takes `file` (uploaded volume) or `image` (datastore ID), plus `params` (JSON) and `output` (`image`, `json`, `dicom_seg` or multipart by default). Returns a label map: 0 background, 1–5 hemorrhage subtypes.
- `POST /train/hemorrhage` (research server only).
- Model handoff: versioned bundles in the registry, with metrics, dataset version and approval status.

## Status

Not started. The interaction diagram the team received runs the app with `trainers = {}`, so training is not available yet.

## Next steps

- Get the bundle and the label table (classes 1–5) from the AI team.
- Add a trainer for `hemorrhage`.
- Check that the returned mask keeps the input grid (no resampling or reorientation).
