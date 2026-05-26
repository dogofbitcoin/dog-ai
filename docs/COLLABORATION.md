# COLLABORATION

How the two Claude sessions (and any future contributors) divide work on Dog of Bitcoin.

## The split

| Session | Lives on | Can see | Cannot see | Primary job |
|---|---|---|---|---|
| Desktop Claude | maintainer laptop | screenshots, design files, the live dashboard in a browser | the AWS server filesystem directly | own `docs/UI_SPEC.md`, design decisions, visual reviews |
| AWS Claude | self hosted server | the repo on the server, running services, logs, terminal output | screenshots, the live rendered UI | implement to spec, run services, debug backend, write tests |

The split is not about capability, it is about ground truth. Whoever has the most direct view of a given artifact owns changes to that artifact.

## File ownership

| Path | Owner | Notes |
|---|---|---|
| `docs/UI_SPEC.md` | desktop Claude | only this session edits visual decisions |
| `docs/reference/*.png` | humans (drop) + desktop Claude (review) | AWS Claude does not open these |
| `frontend/src/**` | AWS Claude (impl) + desktop Claude (review) | impl must follow `UI_SPEC.md` |
| `backend/**` | AWS Claude | spec free, normal contribution rules |
| `docs/PROVIDERS.md`, `docs/INDICATORS.md` | either | technical contracts, not visual |
| `CLAUDE.md` | maintainer | rarely changes |

## Branch model (existing, see `CLAUDE.md`)

- `main` protected, released
- `develop` integration, default target
- `claude-aws` for autonomous AWS Claude commits, bot identity `dog-of-bitcoin-bot <bot@dogofbitcoin.com>`
- `feature/<name>` for human work

Desktop Claude pushes spec updates directly to `develop` (or via PR if a reviewer is preferred). AWS Claude commits implementation work to `claude-aws`, maintainer merges into `develop`.

## Working loop

1. Maintainer captures a screenshot of the current dashboard, drops in `docs/reference/` with the scene tag format defined in `docs/UI_SPEC.md` section 5.
2. Maintainer opens desktop Claude with the screenshot and the spec. Desktop Claude updates the spec to capture intended changes.
3. Maintainer commits spec changes to `develop`, pushes.
4. AWS Claude pulls `develop`, reads the spec, ships the implementation on `claude-aws`.
5. Maintainer reviews the diff, merges `claude-aws` into `develop`.
6. Take a new screenshot. If the result matches the spec, done. If not, loop back to step 2.

## Anti patterns

- AWS Claude trying to infer visual decisions from CSS alone. The spec is the source.
- Desktop Claude editing component JSX. That is implementation, not spec.
- Either session pushing to `main` directly. Always `develop` first.
- Spec updates that reference a screenshot not committed to `docs/reference/`. The image must be in the repo for the spec to be reproducible.

## What about sessions on other devices

Any new Claude session (mobile, second laptop, another server) joins as either an implementer or a spec author, depending on what it can see. The same ownership rules apply. Identity in commits should match the role: implementation work uses the bot identity if autonomous, the human's identity if interactive.
