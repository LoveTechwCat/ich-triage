# ich-triage

- This repo is the implementation of the ICH AI triage system. The design lives in https://github.com/jikei25/ich-architecture (site: https://jikei25.github.io/ich-architecture/). Read the relevant design section before changing a component, and say in the PR which section or decision it implements.
- Do not write design documents here. If a change alters the design, say so and point to ich-architecture.
- Write everything in English: code, comments, READMEs, commits, PRs.
- Each component has its own folder under `services/`, `deploy/` or `tools/`. Its README states its purpose, interfaces and status; keep that README in step with the code.
- Never commit secrets (`.env`, `secrets.env`), patient data or model weights.
- Commits follow Conventional Commits (see `CONTRIBUTING.md`).
