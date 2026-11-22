# Triage API (AI results service)

## Purpose

Serves the radiologist's worklist with AI state: the PACS study list merged with AI results, ordered so that unconfirmed positive studies come first. Records the radiologist's confirm or reject decision and pushes live events to the viewer.

## Architecture block

AI results database and priority flag, used by the clinical viewer (3D Slicer with the ICH Triage module). Design: [Flow 2](https://jikei25.github.io/ich-architecture/index.html#flow-triage), viewer requirements in D10 ([decisions.html](https://github.com/jikei25/ich-architecture/blob/docs/slicer-monai-architecture/decisions.html) on the `docs/slicer-monai-architecture` branch, [PR #11](https://github.com/jikei25/ich-architecture/pull/11), not merged yet).

## Interfaces

To be designed. The API must cover:

- the study list with AI state and priority;
- one study: AI state, volume, model version;
- the radiologist's decision: confirmed or rejected;
- live events to the viewer: a new AI result, AI service status.

AI states: not run, running, done and awaiting confirmation, no result. None of them may look like a negative study.

## Status

Not started, API to be designed.

## Next steps

- Design the API (endpoints, event stream, error cases) and record it in ich-architecture.
- Implement it here with tests.
- Store results in PostgreSQL.
- Check the OIDC token on every request.
