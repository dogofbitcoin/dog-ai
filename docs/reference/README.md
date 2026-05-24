# docs/reference

Screenshots that ground `docs/UI_SPEC.md` in visual reality.

## Who reads what

- **Desktop Claude** (laptop session with screenshot vision): reads images here, updates `UI_SPEC.md` to match what is shown.
- **AWS Claude** (server session): does not open images here. Reads `UI_SPEC.md` and implements to spec.
- **Humans**: ground truth for design reviews, PR discussion, change proposals.

## Naming convention

```
dashboard-<version>-<scene>-<state>.png
```

| Part | Meaning |
|---|---|
| `version` | `v1`, `v2`, etc. Bump when a major redesign lands. |
| `scene` | What region or interaction is shown: `baseline`, `trader-tab-portfolio`, `character-strip-idle`, `kraken-skill-rotation`, etc. |
| `state` | The data or interaction state: `trading`, `idle`, `halted`, `empty`, `loading`, `error`. |

Examples:
- `dashboard-v1-baseline-trading.png`
- `dashboard-v1-character-strip-trading.png`
- `dashboard-v1-trader-tab-log.png`
- `dashboard-v1-empty-state.png`

## How drift gets fixed

1. Someone takes a screenshot of the current dashboard.
2. Drop it here with a scene-tagged filename.
3. Open it in a session that has vision (desktop Claude).
4. Compare to `UI_SPEC.md`. Update the spec if the new state is the intended direction; otherwise flag it as a regression.
5. Commit spec changes on `develop`.
6. Implementation sessions (AWS Claude) read the updated spec and ship the changes.

## Out of scope

- Marketing assets, social images, hero renders. Those live in `docs/brand/` (TBD).
- Character art source files. Those live in `frontend/src/assets/characters/`.
