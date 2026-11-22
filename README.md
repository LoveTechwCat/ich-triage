# ich-triage

Implementation of the ICH (intracerebral hemorrhage) AI triage system. When a head CT reaches the PACS, an AI model looks for hemorrhage, the suspected cases move to the top of the radiologist's worklist, and the radiologist reads, confirms or corrects the AI mask in 3D Slicer.

This repo holds code, deployment configs and runnable PoCs. The design (architecture, decisions, ideas) lives in [ich-architecture](https://github.com/jikei25/ich-architecture), published at <https://jikei25.github.io/ich-architecture/>. If a change alters the design, update ich-architecture first and link it from the PR here.

## Components

| Folder | What it is | Architecture block | Status |
|---|---|---|---|
| [`services/gateway`](services/gateway) | Orthanc gateway between the PACS and the AI side | AI inference (VLAN 30) | Code still in ich-architecture |
| [`services/ai-worker`](services/ai-worker) | AI worker: jobs, DICOM to NIfTI, MONAI call, SEG/SR, priority flag | AI inference (VLAN 30) | Runs as an Orthanc plugin in staging |
| [`services/monai-app`](services/monai-app) | MONAI Label app with the `hemorrhage` model | AI inference + research | Not started |
| [`services/triage-api`](services/triage-api) | AI results service: study list, review, live events | AI results / priority | PoC version in ich-architecture |
| [`services/slicer-ich-triage`](services/slicer-ich-triage) | 3D Slicer module "ICH Triage" for radiologists | Clinical viewer | Not started |
| [`deploy/staging`](deploy/staging) | Four-server Docker Compose staging | All layers | Code still in ich-architecture |
| [`deploy/local`](deploy/local) | One-machine dev stack | Dev | Not started |
| [`tools`](tools) | Simulators and data loaders (HIS, scanner, synthetic CT, mock AI) | Test support | PoC versions in ich-architecture |

## Design references

- Architecture, scenario 1: <https://jikei25.github.io/ich-architecture/index.html>
- Decisions, including D10 (viewer: 3D Slicer) and D11 (AI blocks: MONAI): <https://jikei25.github.io/ich-architecture/decisions.html>
- 3D Slicer + MONAI assessment and proposal: <https://jikei25.github.io/ich-architecture/slicer.html>

## Code still in ich-architecture

These parts will move here later. Until then, change them in ich-architecture:

- `deploy/staging/`: staging compose for PACS, gateway, database and storage, plus the gateway plugins `ai_bridge.py` and `nifti_bridge.py`.
- `poc/viewer/`: OHIF + dcm4chee + simulated AI PoC (`triage_api.py`, `ai_worker.py`, `his.py`, `scanner.py`).

## Not set up yet

- **Licence.** Public without a licence means all rights reserved; the team decides later.
- **CI.** Added with the first code.
