# dataviz-inspiration — a skill for coding agents

By [Joël Gombin](https://github.com/joelgombin) and [Yan Holtz](https://www.yan-holtz.com).

Ask an agent for a chart and you get something correct but generic: it has no visual culture.
This skill gives it one. Before designing a visualization, the agent searches curated galleries of
published visualizations as a single catalog, looks at the best matches, and tells you which idea it
borrows from which reference:

- [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by [Yan Holtz](https://www.yan-holtz.com)
  — 450+ projects tagged by chart type and design technique, each with a short critique
  (English, CC BY 4.0);
- [Dataviz Index](https://datavizindex.fr) by [WeDoData](https://wedodata.fr) — 300 picks from the
  [*Buena Vista Data Club*](https://wedodata.beehiiv.com) newsletter, tagged by type, theme and
  format (French);
- plus [method references](#method-references) to choose and check the form.

## Method references

When the right form is not obvious, the skill points the agent to:

- [From Data to Viz](https://www.data-to-viz.com) ([Yan Holtz](https://www.yan-holtz.com) & Conor Healy) — decision tree from
  the shape of the data to chart types, and its [catalogue of caveats](https://www.data-to-viz.com/caveats.html);
- [The Data Visualisation Catalogue](https://datavizcatalogue.com) (Severino Ribecca) — chart types
  searchable by function;
- Insee, [« Comment présenter nos données pour mieux communiquer ? »](https://www.insee.fr/fr/information/7722079),
  *Courrier des statistiques* n° 10 (2023) — graphic semiology and rigour for official statistics;
- Éric Mauvière ([icem7](https://www.icem7.fr)), [« La dataviz pour donner du sens aux données et communiquer un message »](https://minio.lab.sspcloud.fr/lgaliana/ssphub/replay/20240229-dataviz-mauviere/conf_ssphub_icem7.pdf)
  (2024) — step-by-step redesigns of real charts;
- [R Graph Gallery](https://r-graph-gallery.com) and [Python Graph Gallery](https://python-graph-gallery.com)
  ([Yan Holtz](https://www.yan-holtz.com)) — charts with their code;
- [*ggplot2: Elegant Graphics for Data Analysis*](https://ggplot2-book.org) (3rd ed.).

The full notes live in [`references/method.md`](plugins/dataviz-inspiration/skills/dataviz-inspiration/references/method.md).

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

Nothing to call: the skill triggers when the agent is about to draw a chart or a map (helped by
the hook), or when you ask for ideas or references.

To call it explicitly, type the slash command followed by what you want to show:

```
/dataviz-inspiration:dataviz-inspiration a map of turnout by municipality, with many small rural towns
```

The name is namespaced (`plugin:skill`) when installed as a plugin; with a bare copy of the skill
folder in `~/.claude/skills/`, it is simply `/dataviz-inspiration`. You can also just ask in plain
words: "use dataviz-inspiration to find references for this chart".

You can also query the catalog yourself:

```bash
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py "election élection turnout participation" --family map
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --family evolution --label annotation
python3 plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts/search_viz.py --vocab
```

## Authors

- [Joël Gombin](https://github.com/joelgombin) — the skill, the multi-source search and the hook.
- [Yan Holtz](https://www.yan-holtz.com) — co-author; curator of
  [dataviz-inspiration.com](https://www.dataviz-inspiration.com), whose open catalog
  ([`viz-list.json`](https://www.dataviz-inspiration.com/viz-list.json),
  [`llms.txt`](https://www.dataviz-inspiration.com/llms.txt)) is the backbone of the skill, and
  author of [From Data to Viz](https://www.data-to-viz.com) and the
  [R](https://r-graph-gallery.com) and [Python](https://python-graph-gallery.com) Graph Galleries.

Contributions welcome: issues and pull requests on this repository.

## Credits and licences

- [dataviz-inspiration.com](https://www.dataviz-inspiration.com) by [Yan Holtz](https://www.yan-holtz.com): catalog data
  licensed under [CC BY 4.0](https://github.com/holtzy/dataviz-inspiration/blob/main/LICENSE).
- [Dataviz Index](https://datavizindex.fr) by [WeDoData](https://wedodata.fr): selection and editorial comments © WeDoData.
  The agent reads them like a visitor would, links to them and paraphrases; it does not republish them.
- Both galleries are read live from their public endpoints, never copied into this repository.
- Chart families come from [dataviz-inspiration's source code](https://github.com/holtzy/dataviz-inspiration) (MIT); their mapping onto Dataviz
  Index types is ours.
- Images are screenshots of work by their respective authors and are covered by neither: the
  skill only lets the agent look at them, never reuse them.
- This repository: MIT.

## Development

```bash
python3 -m pytest
```
