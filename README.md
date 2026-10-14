# dataviz-inspiration — a skill for coding agents

Ask an agent for a chart and you get something correct but generic: it has no visual culture.
This skill gives it one. Before designing a visualization, the agent searches the curated catalog
of [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by Yan Holtz — 450+ published
visualizations tagged by chart type and design technique, each with a short critique — looks at the
best matches, and tells you which idea it borrows from which reference.

## Install

In Claude Code:

```
/plugin marketplace add joelgombin/dataviz-inspiration-skill
/plugin install dataviz-inspiration@dataviz-inspiration
```

Or copy `plugins/dataviz-inspiration/skills/dataviz-inspiration/` into `~/.claude/skills/`
(or into any agent that reads `SKILL.md` folders).

Requirements: Python 3.9+, standard library only, and network access to dataviz-inspiration.com
(the catalog is cached for 24 h in `~/.cache/dataviz-inspiration/`).

## Use

Nothing to call: the skill triggers when the agent is about to design a non-trivial chart, or when
you ask for ideas or references. You can also query the catalog yourself:

```bash
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py "election" --family map
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --family evolution --label annotation
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --vocab
```

## Credits and licences

- Catalog data: [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by Yan Holtz,
  licensed under [CC BY 4.0](https://github.com/holtzy/dataviz-inspiration/blob/main/LICENSE).
  It is read live from the official endpoint, never copied into this repository.
- Images are screenshots of work by their respective authors and are **not** covered by that
  licence: the skill only lets the agent look at them, never reuse them.
- Chart families come from the site's source code (MIT).
- This repository: MIT.

## Development

```bash
python3 -m pytest
```
