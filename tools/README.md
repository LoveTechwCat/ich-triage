# Tools

## Purpose

Simulators and data loaders for testing without hospital systems:

| Tool | Stands in for | What it does |
|---|---|---|
| HIS simulator | HIS/RIS | Sends HL7 ORM orders to the PACS worklist |
| Scanner simulator | CT scanner | Queries the worklist (C-FIND), then sends a study (C-STORE) |
| Synthetic CT | Patient data | Generates head CTs, with or without a 72 HU lesion |
| NIfTI loader | Public datasets | Loads CT-ICH (PhysioNet) volumes into the PACS as DICOM |
| Mock AI | MONAI server | Returns the ground-truth mask of a known volume, to check geometry end to end |

## Status

PoC versions in ich-architecture:
- `poc/viewer/py/his.py`, `scanner.py`, `synthetic_ct.py`;
- `deploy/staging/tools/load_nifti.py`, `mock_ai.py`.

## Next steps

- Move them here as one Python package with a small CLI.
- Make the mock AI speak the MONAI Label `/infer` interface, so the AI worker can switch between them with one setting.
