# Publishing Dog of Bitcoin

The exact steps to flip the repo from private to public under the **Dog of Bitcoin** GitHub organization when v0.1 is ready to ship.

Read this whole doc once before doing any of it. The flip itself takes 5 minutes. The pre-flip checklist is what protects you from publishing something you regret.

---

## What "ready to ship" means

Before flipping, all of these must be true:

- [ ] `main` builds clean from a fresh clone, following only what's in `docs/RUNNING.md`
- [ ] `pytest` passes from the backend, `npm test` passes from the frontend
- [ ] `/health/providers` returns `ok: true` for every registered provider
- [ ] The dashboard renders end-to-end with live data on the AWS box for at least 30 minutes without a panel going dark
- [ ] `CHANGELOG.md` has a real `0.1.0` entry with a date
- [ ] `VERSION` reads `0.1.0`
- [ ] `LICENSE` is in the repo root and reads MIT
- [ ] `README.md` opens with a one-line description anyone can understand in 5 seconds

If any of those is false, do not publish. Fix it, then come back.

---

## Pre-flip security sweep

Public means public. Once the repo is open, every prior commit on every branch is open too. Run this sweep first.

### 1. Scrub secrets from history

Any API key, password, or token that ever appeared in any file in any commit must be rotated and removed from history.

```bash
# From repo root, on a fresh clone
git log --all --full-history -p | grep -iE "(api[_-]?key|secret|password|token|bearer)" | head -50
```

Anything that hits, treat as compromised. The cleanest path:

```bash
# Install git-filter-repo if not already
pip install git-filter-repo

# Remove a file from all history (example: an accidentally committed .env)
git filter-repo --path .env --invert-paths

# Or replace a specific string everywhere
echo "OLD_SECRET==>REDACTED" > replacements.txt
git filter-repo --replace-text replacements.txt
```

After filter-repo you will need to force-push. Do that **while the repo is still private**.

Then rotate every key that was ever in history. Assume it leaked.

### 2. Confirm `.env` is in `.gitignore` and not tracked

```bash
git ls-files | grep -E "^\.env$"
# should return nothing

cat .gitignore | grep -E "^\.env$"
# should return .env
```

### 3. Check every branch, not just `main`

```bash
git branch -a
```

The `claude-aws` branch in particular has autonomous commit history. Skim it for anything you don't want public. If there's working-in-progress that shouldn't ship with v0.1:

- Option A (clean): delete the branch before going public. `git push origin --delete claude-aws`. Recreate it after publishing if you want the bot to keep working.
- Option B (keep history): leave it; everything on `claude-aws` becomes public too.

Recommend Option A for the v0.1 flip. The bot history is operational, not part of the v0.1 story.

### 4. Squash, tag, and freeze `main`

The version of `main` at the moment of going public is the version the world sees first. Make it a single clean line.

```bash
git checkout main
git pull
git tag -a v0.1.0 -m "v0.1.0 — public release"
git push origin v0.1.0
```

---

## Pre-flip content sweep

These are content cleanups, not security. Do them in the same pass.

- [ ] **README.md:** opens with a plain description. No internal references, no contest framing, no audience-specific language. Someone landing cold should understand what this is in 30 seconds.
- [ ] **Doc comments:** no references to specific people, conversations, or strategic context. The code should read like a project, not a transcript.
- [ ] **Commit messages on `main`:** skim the last 20 with `git log --oneline -20`. Any messages that read like internal chatter? Squash or rewrite before tagging.
- [ ] **`CLAUDE.md`:** stays in the repo. It's project conventions. But re-read it once and confirm it has nothing that reads as internal back-and-forth.
- [ ] **Issues and PRs:** any open issues with private discussion get closed or rewritten before flipping. Once public, every old issue is public.
- [ ] **Project boards and wikis:** check if any are attached. They become public on flip.

---

## The flip — step by step

You need **Owner** permission on the Dog of Bitcoin organization to do this. If the repo currently lives on a personal account, transfer it first (see Appendix A).

### Step 1 — Confirm the repo is under the org

In a browser, go to:

```
https://github.com/dog-of-bitcoin/dog-of-bitcoin
```

If that loads (even as private, you'll see it when signed in), the repo is in the org. If it returns 404, do Appendix A first.

### Step 2 — Open the visibility setting

1. Repo page → **Settings** (gear icon, top right of the repo nav).
2. Scroll to the bottom: **Danger Zone**.
3. Find **Change repository visibility**.
4. Click **Change visibility**.

### Step 3 — Confirm public

GitHub will pop a modal and warn you:

- The repo will be visible to anyone on the internet.
- Forks become possible.
- Stars, watchers, and traffic become public.

Select **Make public**. Type the repo name (`dog-of-bitcoin/dog-of-bitcoin`) to confirm. Click the red button.

You are now public.

### Step 4 — Verify

Open the repo URL in a private browser window with no GitHub session. You should see the README. If you see a 404, the flip didn't go through; retry.

### Step 5 — Create the v0.1.0 release

The tag exists from the pre-flip step. Now make it a release with notes.

1. Repo page → **Releases** (right sidebar) → **Draft a new release**.
2. **Choose a tag:** `v0.1.0`
3. **Release title:** `v0.1.0`
4. **Description:** paste the `0.1.0` section from `CHANGELOG.md`. Keep it factual: what's in, what's not, what's planned.
5. **Set as latest release:** checked.
6. Publish.

The release shows on the right sidebar of the repo, on the org page, and in everyone's GitHub feed who follows the org.

---

## Immediately after going public

### 1. Re-enable branch protection on `main`

Going public sometimes resets some protection rules. Confirm:

- Settings → Branches → Branch protection rules → `main`
- Require a pull request before merging: ON
- Require approvals: 1 (or more, your call)
- Dismiss stale approvals: ON
- Require status checks: ON (if CI is wired up)
- Restrict who can push: maintainers only
- Allow force pushes: OFF
- Allow deletions: OFF

Same rules for `develop`, slightly looser if you want.

### 2. Set the repo description and topics

Repo page → gear icon next to **About** (right sidebar).

- **Description:** the one-liner from the top of the README.
- **Website:** `https://dogofbitcoin.com` (or wherever it should point).
- **Topics:** add tags so the repo is discoverable. Suggestions: `bitcoin`, `ordinals`, `runes`, `dotswap`, `kraken`, `dashboard`, `agents`, `python`, `react`.

### 3. Add a CODE_OF_CONDUCT.md and SECURITY.md (optional but good)

GitHub has templates under Insights → Community Standards. They take 2 minutes each and tick the community checklist.

### 4. Pin the repo on the org page

Org page → **Customize your pins** → pin `dog-of-bitcoin`. Makes it the first thing visitors see on the org landing.

### 5. Announce

Post once, somewhere central (the project's main channel — X account, Discord, whatever the front door is). Keep it factual:

> Dog of Bitcoin v0.1 is public. [link]

You don't need a launch thread. The repo speaks for itself.

---

## Appendix A — Transferring the repo to the Dog of Bitcoin org

If the repo currently lives on a personal account:

1. From the personal account: repo → Settings → scroll to **Danger Zone** → **Transfer ownership**.
2. **New owner:** type the org name `dog-of-bitcoin`.
3. Type the repo name to confirm.
4. Click **I understand, transfer this repository**.

The receiving org owner must accept the transfer (GitHub emails them).

Once accepted:

- All issues, PRs, stars, and watchers move with it.
- The old URL redirects to the new one for a while, but update any external links.
- Local clones need their remote updated:
  ```bash
  git remote set-url origin git@github.com:dog-of-bitcoin/dog-of-bitcoin.git
  ```
- Any deploy keys, secrets, or workflow tokens scoped to the old location need to be re-added on the new repo.

Do the transfer **before** the flip-to-public. Transferring a public repo is harder to clean up if something goes wrong.

---

## Appendix B — If something goes wrong after going public

You cannot "un-public" cleanly. You can flip it back to private (Settings → Danger Zone → Change visibility → Make private), and from that moment new visitors get a 404. But:

- Anyone who already cloned, forked, or cached the repo still has it.
- Search engines may have indexed it.
- Anything sensitive that leaked is leaked. Rotate keys, don't try to hide.

If you flip back to private:

1. Do it immediately. Every minute it's public is more exposure.
2. Identify what specifically is wrong. Fix it on a branch.
3. Re-run the pre-flip checklist top to bottom.
4. Flip public again only when clean.

If a secret leaked, the priority order is: rotate keys, then patch the repo, then decide whether to flip back to private. Rotation is what actually protects you. Hiding the repo does not.

---

## Appendix C — Roles needed for each step

| Step | Role needed |
|---|---|
| Pre-flip sweep | Repo write |
| Tag and push v0.1.0 | Repo write |
| Transfer repo to org | Owner of source account + Owner of receiving org |
| Flip to public | Org Owner, or Repo Admin with org policy allowing public repos |
| Set branch protection | Repo Admin |
| Pin on org page | Org Owner |

If the person doing the flip doesn't have Org Owner, get one on standby before starting. The flip step itself will hard-stop if the role is wrong.

---

## Quick reference — the 5-minute version

For the next time, when you've done it once and just need the checklist:

```
[ ] /health/providers green for 30 min on AWS
[ ] pytest + npm test pass
[ ] VERSION, CHANGELOG, LICENSE, README all clean
[ ] git log --all -p | grep secrets — nothing
[ ] .env not tracked
[ ] claude-aws branch decided (keep or delete)
[ ] git tag v0.x.y && git push origin v0.x.y
[ ] Settings → Danger Zone → Make public
[ ] Releases → Draft → v0.x.y → publish
[ ] Branch protection re-confirmed on main
[ ] Description, topics, website set
[ ] Pinned on org page
```

That's it. Ship it when it's ready.
