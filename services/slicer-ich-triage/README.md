# 3D Slicer module: ICH Triage

## Purpose

A Python scripted module for 3D Slicer, the radiologists' reading workstation. The target: it shows the priority worklist, opens a study from the PACS, keeps the AI overlay off by default, shows the AI state and volume, lets the radiologist confirm or reject, loads a mask that arrives after the study is open, and saves a corrected mask as a new SEG.

This first version is the skeleton: it stores two server settings and checks the connection to a MONAI Label server. It is the base for the viewer and annotation work that follows.

Slicer is an installed application. This folder holds only our module, which Slicer loads from the repository; no Slicer source is copied or added as a submodule.

## Architecture block

Clinical layer, radiologist viewer. Design (on the `docs/slicer-monai-architecture` branch of ich-architecture, [PR #11](https://github.com/jikei25/ich-architecture/pull/11), not merged yet): [slicer.html](https://github.com/jikei25/ich-architecture/blob/docs/slicer-monai-architecture/slicer.html) sections 6 "What we build: the ICH Triage module" and 7 "Reading the Slicer ↔ MONAI Label diagram"; [decisions.html](https://github.com/jikei25/ich-architecture/blob/docs/slicer-monai-architecture/decisions.html) D10 and D11.

**Deviation from the design.** In D10/D11 this module talks to the PACS and the AI results service, and MONAI Label belongs to the research side (Flow 3; the MONAILabel extension is not installed on clinical reading workstations). The "Check connection" button to MONAI Label is a development and annotation check only, not a clinical feature. ich-architecture needs to record this, or the check moves to a separate annotation module later.

## Interfaces

Implemented now:

| Direction | Protocol | Content |
|---|---|---|
| MONAI Label server | `GET /info/` (HTTP, no auth, no proxy, 5 s timeout) | App name, version, models, trainers, strategies, datastore counts |
| Application settings | `QSettings` keys `ICHTriage/MonaiLabelServerUrl` (default `http://localhost:8000`) and `ICHTriage/PacsDicomWebUrl` (default empty) | Server URLs, kept between Slicer sessions |

The `/info/` response format was checked against the MONAI Label source at tag [`0.8.6`](https://github.com/Project-MONAI/MONAILabel/tree/0.8.6) (`monailabel/endpoints/info.py`, `MONAILabelApp.info()` in `monailabel/interfaces/app.py`). A server started with `MONAI_LABEL_AUTH_ENABLE` answers 401; the module reports this, since it sends no credentials yet.

Planned:

| Direction | Protocol | Content |
|---|---|---|
| PACS | DICOMweb QIDO-RS, WADO-RS; STOW-RS for corrected SEG | Studies, AI SEG and SR |
| Triage API | REST + Server-Sent Events | Worklist, AI state, review, live events |
| Keycloak | OIDC Authorization Code + PKCE through the system browser | Token for every request |

Qt widgets are updated only from the main thread: a background thread reads SSE into a queue, and a `qt.QTimer` drains it. Today "Check connection" is a synchronous call with a 5 s timeout, so the panel is blocked for at most 5 s.

## 3D Slicer version

**3D Slicer 5.12.4** (stable, revision 34645, built 2026-09-09), checked on <https://download.slicer.org/> on 2026-11-22. The preview release (5.13.x) is not used. The version is pinned in [`scripts/run-slicer-dev.ps1`](scripts/run-slicer-dev.ps1); change both places together.

## Install on Windows

1. Open <https://download.slicer.org/> and download the **Stable Release** for Windows (`Slicer-5.12.4-win-amd64.exe`, about 270 MB).
2. Check the file against the SHA512 listed on the download page:
   ```powershell
   (Get-FileHash .\Slicer-5.12.4-win-amd64.exe -Algorithm SHA512).Hash.ToLower()
   ```
   For 5.12.4 Windows it is `5ba320cb67f0acdaacf0a31380e9cf3b9f46d05f57a53da7e04ebcd9490251ecbe998bfefdbdab1f747e038653177868cdb0ad30986473b9d68efba0f4c6045c`.
3. Run the installer and keep the default per-user location, `%LOCALAPPDATA%\slicer.org\3D Slicer 5.12.4`. No administrator rights are needed. For an unattended install, run the installer with `/S`.

   Command-line alternative from the Slicer project, which downloads the latest stable release, checks its SHA512 and installs it silently: `powershell -c "irm https://download.slicer.org/install.ps1 | iex"`. Read the script first. By default it installs the newest stable release; set `$env:SLICER_VERSION = '5.12.4'` in the same PowerShell session first to get the pinned version.

### MONAILabel extension (annotation machines only)

1. In Slicer, open **View → Extensions Manager**.
2. On the **Install Extensions** tab, search for `MONAILabel` (category "Active Learning") and click **Install**.
3. Click **Restart** when asked. The module appears under **Active Learning → MONAI Label**.

The Extensions Manager builds MONAILabel from the `main` branch of Project-MONAI/MONAILabel for each Slicer release, so its version is not pinned. Run a MONAI Label server of a matching version. Do not install the extension on clinical reading workstations (D11).

## Run in development

From the repository root:

```powershell
.\services\slicer-ich-triage\scripts\run-slicer-dev.ps1
```

The script starts Slicer with `--additional-module-paths services/slicer-ich-triage/ICHTriage`, so nothing is installed into Slicer. Open the module from the module list: **ICH → ICH Triage**. After editing the code, click **Reload** in the module's "Reloading & Testing" section (shown when Developer mode is on in Edit → Application Settings → Developer), or restart Slicer.

Slicer is found at `-SlicerExe <path>`, then `$env:SLICER_EXE`, then the default per-user install path above. If PowerShell refuses to run scripts, use `powershell -ExecutionPolicy Bypass -File .\services\slicer-ich-triage\scripts\run-slicer-dev.ps1`.

## Tests

Unit tests for the Slicer-independent part (`ICHTriageLib/monai_label.py`: URL checks, `/info/` parsing, HTTP errors), with plain Python 3.10 or later and pytest:

```powershell
cd services\slicer-ich-triage
python -m pytest
```

The fixtures in [`tests/fixtures`](tests/fixtures) are built from the MONAI Label 0.8.6 source, not captured from a running server; their README lists the source of each field.

Slicer self-test (module registration in category "ICH", settings, Check connection against a local fake server and with no server), headless:

```powershell
.\services\slicer-ich-triage\scripts\run-slicer-dev.ps1 -SelfTest
```

It runs Slicer with `--no-splash --testing --no-main-window` and exits with 0 when all tests pass. `--testing` uses temporary settings, so your saved URLs are not touched. In the Slicer window, the same tests run from **Reload and Test** in the module panel (Developer mode).

## Layout

```
CMakeLists.txt                 Extension (SlicerICHTriage), for packaging later
ICHTriage/                     Scripted module, as created by the Extension Wizard
  CMakeLists.txt
  ICHTriage.py                 Module, Widget, Logic, Test
  ICHTriageLib/monai_label.py  MONAI Label client, standard library only
  Resources/UI/ICHTriage.ui
  Resources/Icons/ICHTriage.png
  Resources/requirements.txt
  Testing/
scripts/run-slicer-dev.ps1     Start Slicer with this module, or run the self-test
tests/                         pytest suite and /info/ fixtures
pyproject.toml                 pytest settings
```

The module has no parameter node: its settings are application-wide (`QSettings`), not part of the scene.

## Status

Skeleton. Settings and the MONAI Label connection check work; pytest and the Slicer self-test pass on Windows with Slicer 5.12.4. Nothing talks to the PACS or the triage API yet, and the extension has not been built with CMake.

## Next steps

- Follow the six-step PoC plan for D10: open a study, load SEG + SR, minimal module, late mask, save a corrected mask, AI down and back up.
- Measure the time from "open" to the first image on the LAN.
- Move "Check connection" to a background thread with the `qt.QTimer` queue once the module makes longer calls.
- Send a token when the MONAI Label server runs with authentication.
