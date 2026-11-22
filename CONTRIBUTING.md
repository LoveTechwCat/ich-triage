# Contributing

## Where things go

- **Code, configs, PoCs:** this repo.
- **Design, decisions, ideas, PoC results:** [ich-architecture](https://github.com/jikei25/ich-architecture). If your change alters the design, update ich-architecture first, then link that change from your PR here.
- **Language:** English everywhere (code, comments, docs, commits, PRs).

## Branches and commits

- One branch per change, with a name that says what it does, for example `feat/monai-infer-endpoint` or `fix/gateway-seg-geometry`. No direct commits to `main`.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`. Add a scope when it helps, for example `feat(ai-worker): ...`. The body says what changed and why.

## Pull requests

Use the PR template. Each PR says:

- what changed;
- how it was tested (commands and results);
- which design section or decision it implements;
- what is not verified yet.

## Secrets and data

- Never commit `.env`, `secrets.env`, passwords or keys. The `.gitignore` blocks the usual names; check `git status` anyway.
- Never commit patient data. Test data is synthetic or comes from public datasets, and is referenced by path, not committed.
- Model weights stay out of git. The model registry holds them.
