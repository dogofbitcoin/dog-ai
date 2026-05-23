# Agents

One line summary of each agent in v0.1.

| Name | Inputs | Stances | What it speaks to |
|---|---|---|---|
| `alpha` | `signal_quality` | confident, tentative, blind | How much to trust the rest of the dashboard right now. |
| `general` | `onchain_heat`, `spread` | bullish, neutral, bearish | Directional bias on the $DOG rune based on on chain activity, fading wide spreads. |

Add a new agent by creating `backend/agents/<name>.py`, subclassing `Agent`, and calling `register()` at the bottom of the file. Add a row to this table.

## Optional LLM narration

Agent stance and confidence are always rule based and deterministic. If `ANTHROPIC_API_KEY` is set in the env, the reasoning string is rewritten by `narrate.maybe_narrate` so the dashboard surfaces a more readable line. If the call fails or the key is absent, the base reasoning is used and behaviour is unchanged.

Override the model with `DOB_NARRATION_MODEL` and the timeout with `DOB_NARRATION_TIMEOUT`. See `narrate.py`.
