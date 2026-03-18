# CONTEXT_SPEC — CLAUDE.md Frontmatter Standard

Every `CLAUDE.md` file in this repository **must** begin with a YAML frontmatter block.
This spec is the single source of truth for the schema, rules, and tooling.

---

## Why Frontmatter?

An AI agent (or a script) should be able to:

1. **Scan frontmatter only** to know what a file covers, what it depends on, and where sections live — without reading the full body.
2. **Jump directly to a section** via the `toc` anchors.
3. **Do programmatic / fuzzy-match lookup** across all `CLAUDE.md` files using `scripts/update_frontmatter.py`.

Keeping frontmatter machine-readable saves tokens and prevents the agent from having to ingest every document before deciding which ones are relevant.

---

## Schema Reference

```yaml
---
id: <slug>           # unique snake_case identifier for this file, e.g. root, src_ingest
title: <string>      # one-line human title
version: "YYYY-MM-DD"   # date of last meaningful body edit
scope: <repo|cowork|src|track|scripts|tests>
tags: [keyword, ...]    # free-form keywords for fuzzy lookup

cross_dependencies:
  reads:    [relative/path/to/file, ...]   # files this context says you WILL read
  writes:   [relative/path/to/file, ...]   # files this context says you WILL write
  siblings: [other_claude_id, ...]         # CLAUDE.md ids to co-load with this one

toc:
  - section: "Section Title"
    anchor: "#section-title"   # lowercase, spaces → hyphens
  # ... one entry per H2 (##) heading in the body
---
```

### Field Rules

| Field | Required | Notes |
|---|---|---|
| `id` | ✅ | Must be unique across the repo. Use `update_frontmatter.py --list` to check duplicates. |
| `title` | ✅ | Should match the first H1 heading in the body. |
| `version` | ✅ | Bump whenever the body changes. Use `update_frontmatter.py --bump <file>` to update in place. |
| `scope` | ✅ | Must be one of: `repo`, `cowork`, `src`, `track`, `scripts`, `tests` |
| `tags` | ✅ | At least 2 tags. Drives fuzzy-match lookup. |
| `cross_dependencies.reads` | ✅ | List every file the body instructs a reader to open. Paths relative to repo root. |
| `cross_dependencies.writes` | ✅ | List every output location mentioned in the body. Use `[]` if none. |
| `cross_dependencies.siblings` | ✅ | Other CLAUDE.md `id` values to co-load. Use `[]` if none. |
| `toc` | ✅ | One entry per `##` section. Anchors must match the rendered heading. |

---

## File Hierarchy and Load Order

When an agent starts a task, it should load CLAUDE.md files **from outermost to innermost**:

```
CLAUDE.md                              ← always load first (repo scope)
  └─ src/CLAUDE.md                     ← if working in src/
       └─ src/ingest/CLAUDE.md         ← if working on ingestion
       └─ src/validate/CLAUDE.md       ← if working on validation
       └─ src/curate/CLAUDE.md         ← if working on curation
       └─ src/eda/CLAUDE.md            ← if working on any EDA
            └─ src/eda/track_a/CLAUDE.md
            └─ src/eda/track_b/CLAUDE.md
  └─ CoWork Planning/CLAUDE.md         ← if working in planning docs
       └─ CoWork Planning/yelp_project/track_a/CLAUDE.md
       └─ CoWork Planning/yelp_project/track_b/CLAUDE.md
       └─ CoWork Planning/yelp_project/track_c/CLAUDE.md
       └─ CoWork Planning/yelp_project/track_d/CLAUDE.md
       └─ CoWork Planning/yelp_project/track_e/CLAUDE.md
       └─ CoWork Planning/yelp_project/docs_agent/CLAUDE.md
  └─ scripts/CLAUDE.md
  └─ tests/CLAUDE.md
```

**Rule:** Only load the siblings listed in the current file's `cross_dependencies.siblings`. Do not speculatively load unrelated branches.

---

## Keeping Frontmatter in Sync

### Manual

Whenever you edit the body of a `CLAUDE.md`:

1. Update `version` to today's date.
2. Update `toc` if you added or renamed `##` sections.
3. Update `cross_dependencies` if file I/O references changed.

### Programmatic

```bash
# Validate all CLAUDE.md files against this spec
python scripts/update_frontmatter.py --check

# List all files with id, scope, version
python scripts/update_frontmatter.py --list

# Bump version date in one file
python scripts/update_frontmatter.py --bump src/ingest/CLAUDE.md

# Print sibling dependency graph
python scripts/update_frontmatter.py --graph
```

The `--check` command is also wired into the `.githooks/pre-commit` hook so frontmatter drift is caught automatically before each commit.

---

## Frontmatter Anti-Patterns

| ❌ Don't | ✅ Do |
|---|---|
| Omit frontmatter from any CLAUDE.md | Always include the full block |
| Use absolute paths in `cross_dependencies` | Always use repo-relative paths |
| List files that don't exist yet | Only list paths actually described in the body |
| Forget to bump `version` after editing body | Use `--bump` or update manually |
| Duplicate `id` values | Run `--list` to audit before adding a new file |
| Put `toc` entries for `###` sub-sections | Only include `##` headings |
