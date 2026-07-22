---
name: hermes-credential-discovery
description: "Discover credentials in external .env files and merge them into Hermes profiles so tools stop reporting setup_needed when the token already exists elsewhere."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, credentials, env, troubleshooting]
---

# Hermes Credential Discovery

When a skill reports `setup_needed` because a required env var (e.g. `NOTION_API_KEY`) is missing, but the token actually exists — just under a different name or in a different file. This skill covers the discovery and merging workflow.

## Trigger

- A skill reports `missing_required_environment_variables: [SOME_VAR]`
- You know or suspect the token exists in a project-level `.env.local` or similar
- The user says "isn't the token in .env.local?"

## Workflow

### Step 1 — Search for the token

```bash
# Search common locations
find /d/develop -name ".env*" -maxdepth 3 2>/dev/null
find /c/Users -name ".env*" -maxdepth 2 2>/dev/null

# Grep for the token by related name
grep -ri "NOTION\|JIRA\|GITHUB" /d/develop/e2e/.env.local 2>/dev/null
```

### Step 2 — Check token name mismatch

Skills declare their required env var names in `prerequisites.env_vars`. If the token is stored under a different name (e.g. `NOTION_TOKEN` vs `NOTION_API_KEY`), map it:

```bash
source /path/to/.env.local && export NOTION_API_KEY="$NOTION_TOKEN"
```

### Step 3 — Test with the mapped name

```bash
source /path/to/.env.local && export NOTION_API_KEY="$NOTION_TOKEN" && \
  curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Step 4 — Make it permanent (merge into Hermes .env)

If the token works, merge it into the Hermes profile's `.env` so future sessions pick it up automatically:

```bash
# Discover the profile's .env path
hermes config env-path

# Merge .env.local contents
echo "" >> <profile-env-path>
echo "# === Auto-merged from /path/to/.env.local ===" >> <profile-env-path>
cat /path/to/.env.local >> <profile-env-path>

# Add alias for mismatched names
echo "NOTION_API_KEY=\$NOTION_TOKEN" >> <profile-env-path>
```

## Pitfalls

- **Variable expansion may not work**: `NOTION_API_KEY=$NOTION_TOKEN` in `.env` depends on Hermes' dotenv parser supporting variable references. If it doesn't expand, replace `$NOTION_TOKEN` with the actual value.
- **`.env.local` changes won't sync**: The merge is a one-time copy. If `.env.local` is updated later, the Hermes `.env` must be re-merged manually.
- **404 ≠ bad token**: If the token works but returns 404, the page likely isn't shared with the integration. Check Notion: `···` → `Connections` → `Connect to` → integration name.
- **Don't merge into the wrong profile**: Use `hermes config env-path` to confirm you're editing the right profile's `.env`.