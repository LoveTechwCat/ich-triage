# 3D Slicer module: ICH Triage

## Purpose

A Python scripted module for 3D Slicer, the radiologists' reading workstation. It shows the priority worklist, opens a study from the PACS, keeps the AI overlay off by default, shows the AI state and volume, lets the radiologist confirm or reject, loads a mask that arrives after the study is open, and saves a corrected mask as a new SEG.

## Architecture block

Clinical layer, radiologist viewer. Design: [D10](https://jikei25.github.io/ich-architecture/decisions.html#d10), [module design](https://jikei25.github.io/ich-architecture/slicer.html#module).

## Interfaces

| Direction | Protocol | Content |
|---|---|---|
| PACS | DICOMweb QIDO-RS, WADO-RS; STOW-RS for corrected SEG | Studies, AI SEG and SR |
| Triage API | REST + Server-Sent Events | Worklist, AI state, review, live events |
| Keycloak | OIDC Authorization Code + PKCE through the system browser | Token for every request |

Qt widgets are updated only from the main thread: a background thread reads SSE into a queue, and a `qt.QTimer` drains it.

## Status

Not started. A sketch of the core is on the design page.

## Next steps

- Follow the six-step PoC plan for D10: open a study, load SEG + SR, minimal module, late mask, save a corrected mask, AI down and back up.
- Measure the time from "open" to the first image on the LAN.
