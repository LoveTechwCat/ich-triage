# Triage API (AI results service)

## Purpose

Serves the radiologist's worklist with AI state: the PACS study list merged with AI results, ordered so that unconfirmed positive studies come first. Records the radiologist's confirm or reject decision and pushes live events to the viewer.

## Architecture block

AI results database and priority flag, used by the clinical viewer. Design: [Flow 2](https://jikei25.github.io/ich-architecture/index.html#flow-triage), [viewer requirements (D10)](https://jikei25.github.io/ich-architecture/decisions.html#d10).

## Interfaces

| Endpoint | Content |
|---|---|
| `GET /triage/api/studies` | Study list with AI state and priority |
| `GET /triage/api/studies/{uid}` | One study: AI state, volume, model version |
| `POST /triage/api/studies/{uid}/review` | `{"decision": "CONFIRMED" \| "REJECTED"}` |
| `GET /triage/api/events` | Server-Sent Events: `result`, `ai_status` |

AI states: not run, running, done and awaiting confirmation, no result. None of them may look like a negative study.

## Status

PoC version in `ich-architecture/poc/viewer/py/triage_api.py`, used by both the OHIF panel and the planned 3D Slicer module.

## Next steps

- Move the PoC service here and give it tests.
- Store results in PostgreSQL instead of PoC memory.
- Check the OIDC token on every request.
