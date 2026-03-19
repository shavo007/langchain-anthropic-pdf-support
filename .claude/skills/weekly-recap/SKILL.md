---
name: weekly-recap
description: This skill should be used when the user asks to "generate a weekly recap", "write a weekly summary", "summarize merged PRs", "create a weekly engineering update", "draft a weekly report", "what shipped this week", or "recap this week's PRs". Fetches merged pull requests from GitHub and formats them into a structured, human-readable recap post.
version: 0.1.0
---

# Weekly Recap

Fetch merged pull requests from GitHub and produce a formatted weekly recap post suitable for Slack, email, or a team wiki.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Run from within a GitHub-backed git repository, or provide `--repo owner/repo`

## Workflow

### Step 1: Fetch merged PRs

Run the bundled fetch script to get PRs merged in the last 7 days (default):

```bash
bash ${CLAUDE_SKILL_ROOT}/scripts/fetch_merged_prs.sh
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--days N` | `7` | Look back N days |
| `--repo owner/repo` | current repo | Target a specific repo |

Examples:

```bash
# Last 14 days
bash ${CLAUDE_SKILL_ROOT}/scripts/fetch_merged_prs.sh --days 14

# Different repo
bash ${CLAUDE_SKILL_ROOT}/scripts/fetch_merged_prs.sh --repo anthropics/anthropic-sdk-python

# Both
bash ${CLAUDE_SKILL_ROOT}/scripts/fetch_merged_prs.sh --days 7 --repo myorg/myrepo
```

The script outputs a JSON array. Each element contains:
- `number` — PR number
- `title` — PR title
- `author.login` — GitHub username
- `mergedAt` — ISO timestamp
- `url` — link to the PR
- `labels` — array of label objects (`{ name }`)
- `body` — PR description (may be empty)

### Step 2: Categorize the PRs

Group PRs by their GitHub labels using this priority order:

1. `feat` / `feature` / `enhancement` → **Features**
2. `fix` / `bug` / `bugfix` → **Bug Fixes**
3. `chore` / `ci` / `build` / `deps` / `dependencies` → **Maintenance**
4. `docs` / `documentation` → **Documentation**
5. `refactor` / `perf` / `performance` → **Refactoring & Performance**
6. Unlabeled → **Other**

A PR belongs to the first matching category. If a repo doesn't use labels, infer categories from PR title prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).

### Step 3: Write the recap post

Produce a Markdown recap using this structure:

```
## Weekly Engineering Recap — Week of <Mon DD, YYYY>

<1–2 sentence narrative summary of the week's theme or highlights>

### Features
- **PR Title** ([#N](url)) — _@author_ — one-line description

### Bug Fixes
- ...

### Maintenance
- ...

### Documentation
- ...

---
**<N> PRs merged** | <date range>
```

**Writing guidelines:**

- Keep each bullet to one line. Pull the description from the PR title; only use the PR body if the title is too terse to be self-explanatory.
- Strip conventional-commit prefixes from titles (`feat:`, `fix:`, `chore:`, etc.) before displaying.
- Format authors as `@username` links when the output target supports it (e.g., Slack, GitHub), or plain `@username` for plain text.
- Omit empty sections entirely.
- For the opening narrative, note any high-signal themes (e.g., "This week focused on improving PDF pipeline reliability and adding structured output support").

### Step 4: Adapt tone and format to the target

Ask the user (or infer from context) where the recap will be posted:

| Target | Adjustments |
|--------|-------------|
| **Slack** | Use `*bold*`, bullet `•`, keep it concise |
| **Email** | Formal opening, HTML-safe, no bare URLs |
| **GitHub / Wiki** | Full Markdown, include PR links as `[#N](url)` |
| **Linear / Notion** | Markdown, section headers, use `[ ]` checkboxes if needed |

Default to GitHub-flavored Markdown.

## Quick Example

```
## Weekly Engineering Recap — Week of Mar 17, 2025

A productive week with a major feature landing alongside several reliability fixes.

### Features
- **Add structured response output to PDF agent** ([#49](https://github.com/…/pull/49)) — _@shanelee_

### Bug Fixes
- **Evaluate metrics individually to prevent Haiku JSON truncation** ([#48](https://github.com/…/pull/48)) — _@shanelee_

### Maintenance
- **Bump ruff pre-commit hook** ([#52](https://github.com/…/pull/52)) — _@dependabot_
- **Add Dependabot pre-commit hook support** ([#50](https://github.com/…/pull/50)) — _@shanelee_

---
**4 PRs merged** | Mar 11–17, 2025
```

## Troubleshooting

**`gh: command not found`** — Install with `brew install gh` or see [cli.github.com](https://cli.github.com).

**`gh auth` error** — Run `gh auth login` and follow the prompts.

**Empty results** — The date window may not overlap with any merges. Try `--days 14`.

**Wrong repo** — Run from inside the target repo, or pass `--repo owner/repo` explicitly.
