# /info/ fixtures

Sample `GET /info/` responses of a MONAI Label server. They were not captured from a running server: each one is built from the MONAI Label source at tag [`0.8.6`](https://github.com/Project-MONAI/MONAILabel/tree/0.8.6), field by field:

| Part | Source |
|---|---|
| Top-level keys | `monailabel/interfaces/app.py`, `MONAILabelApp.info()` |
| `name`, `description`, `version` | `sample-apps/radiology/main.py` |
| `models.segmentation_spleen` | `sample-apps/radiology/lib/infers/segmentation_spleen.py`, `lib/configs/segmentation_spleen.py`, `monailabel/tasks/infer/basic_infer.py` (`info()`, `config` with `device`) |
| `models.Histogram+GraphCut` | `monailabel/scribbles/infer.py` |
| `trainers.*` | `monailabel/interfaces/tasks/train.py` (`info()`), `monailabel/tasks/train/basic_train.py` (default `config`) |
| `strategies.*` | `monailabel/tasks/activelearning/random.py`, `first.py` |
| `datastore` | `monailabel/datastore/local.py`, `LocalDatastore.status()` |

- `info_radiology_no_trainers.json`: the case in the team's diagram, `trainers = {}`.
- `info_radiology_with_trainer.json`: the same app with the spleen trainer.

Replace them with real captures once a team server runs (no patient data in them: `/info/` holds no images).
