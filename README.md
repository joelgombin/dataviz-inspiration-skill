# dataviz-inspiration — a skill for coding agents

Ask an agent for a chart and you get something correct but generic: it has no visual culture.
This skill gives it one. Before designing a visualization, the agent searches curated galleries of
published visualizations as a single catalog, looks at the best matches, and tells you which idea it
borrows from which reference:

- [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by Yan Holtz — 450+ projects tagged
  by chart type and design technique, each with a short critique (English, CC BY 4.0);
- [Dataviz Index](https://datavizindex.fr) by WeDoData — 300 picks from the *Buena Vista Data Club*
  newsletter, tagged by type, theme and format (French);
- plus method references to choose and check the form: From Data to Viz, the Data Visualisation
  Catalogue, Insee's guidance and Éric Mauvière's (icem7) redesigns.

## Install

In Claude Code:

```
/plugin marketplace add joelgombin/dataviz-inspiration-skill
/plugin install dataviz-inspiration@dataviz-inspiration
```

Or copy `plugins/dataviz-inspiration/skills/dataviz-inspiration/` into `~/.claude/skills/`
(or into any agent that reads `SKILL.md` folders).

### Why a hook

Skills are picked from their description, and an agent busy fetching data tends to jump straight
to plotting code without loading any skill. So the plugin ships a `PreToolUse` hook: when the agent
is about to write chart/map-drawing code (matplotlib, geopandas, plotly, ggplot2, d3, Vega…) and
has not loaded the skill in the session, the call is denied **once**, with a reason asking it to
load `dataviz-inspiration` first. A retry goes through, so it never locks anyone out. Opt out with
`DATAVIZ_INSPIRATION_HOOK=off`. The hook only comes with the plugin install, not with a bare copy
of the skill folder.

Requirements: Python 3.9+, standard library only, and network access to the galleries
(cached for 24 h in `~/.cache/dataviz-inspiration/`; a stale cache is used offline).

## Use

Nothing to call: the skill triggers when the agent is about to design a non-trivial chart, or when
you ask for ideas or references. You can also query the catalog yourself:

```bash
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py "election élection turnout participation" --family map
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --family evolution --label annotation
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --vocab
```

## Credits and licences

- [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by Yan Holtz: catalog data
  licensed under [CC BY 4.0](https://github.com/holtzy/dataviz-inspiration/blob/main/LICENSE).
- [Dataviz Index](https://datavizindex.fr) by WeDoData: selection and editorial comments © WeDoData.
  The agent reads them like a visitor would, links to them and paraphrases; it does not republish them.
- Both galleries are read live from their public endpoints, never copied into this repository.
- Chart families come from dataviz-inspiration's source code (MIT); their mapping onto Dataviz
  Index types is ours.
- Images are screenshots of work by their respective authors and are covered by neither: the
  skill only lets the agent look at them, never reuse them.
- This repository: MIT.

## Development

```bash
python3 -m pytest
```
