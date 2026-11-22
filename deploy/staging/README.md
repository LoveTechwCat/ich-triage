# Staging deployment

## Purpose

Four servers, one Docker Compose project each, for testing the whole path without high availability, Keycloak, cloud backup or a GPU.

| Server | Services | Published ports |
|---|---|---|
| PACS | dcm4chee-arc-light 5.35.2, OpenLDAP, viewer | 80 (HTTP), 11112 (DICOM), 2575 (HL7), 11113 (AI results) |
| Gateway | Orthanc 26.9.1 (PostgreSQL index, S3 storage, DICOMweb) | 4242 (DICOM), 8042 (HTTP) |
| Database | PostgreSQL 17 (`pacsdb`, `orthanc`) | 5432 |
| Storage | SeaweedFS 4.47 (buckets `pacs`, `orthanc`, `research`) | 8333 (S3) |

## Status

Code still in `ich-architecture/deploy/staging/`, with its own README (first installation, re-running, data directories, AI bridge, local test on one machine).

## Next steps

- Move the staging configs here, then delete them from ich-architecture.
- Add the MONAI Label inference server once [`services/monai-app`](../../services/monai-app) exists.
