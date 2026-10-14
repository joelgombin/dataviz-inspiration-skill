---
name: dataviz-inspiration
description: Find real-world, curated data visualizations to draw inspiration from before designing a chart, map or dashboard. Searches the dataviz-inspiration.com catalog (Yan Holtz, 450+ projects tagged by chart type and design technique, each with a short critique) and returns references with what makes them work. Use whenever you are about to design or redesign a non-trivial visualization (a chart for a report, an article, a dashboard, a map, a poster), when the user asks for ideas, examples, references or "how would the best newsrooms show this", or when a first chart looks generic and needs a better idea. Skip it for quick throwaway exploratory plots.
---

# Dataviz inspiration

Agents draw correct but generic charts: they have no visual culture. This skill gives you one —
the catalog of [dataviz-inspiration.com](https://www.dataviz-inspiration.com), curated by Yan Holtz:
450+ published visualizations (NYT, Le Monde, Bloomberg, independent designers…), each tagged with
chart types and design techniques, and described in plain text ("what the chart does", "context").

The catalog is fetched live from `https://www.dataviz-inspiration.com/viz-list.json` and cached
for 24 h. Never copy it into a project.

## Workflow

### 1. Frame the question before searching

Work out what the reader must see. That decides the **family**:

| The reader must see…                  | `--family`     |
|---------------------------------------|----------------|
| how values are spread                 | `distribution` |
| a relationship between variables      | `correlation`  |
| an order, a comparison of quantities  | `ranking`      |
| shares of a whole, hierarchy          | `partOfAWhole` |
| change over time                      | `evolution`    |
| where (geography)                     | `map`          |
| flows, connections, networks          | `flow`         |

Also note the techniques you may need (annotation, small multiples, direct labeling, highlight,
bivariate coloring, uncertainty, scrollytelling…) and the medium (static or interactive, light or dark).

### 2. Search

```bash
python3 scripts/search_viz.py "<topic keywords in English>" --family <family> [options]
```

`scripts/` is relative to this skill's directory. Python 3.9+, standard library only.

| Option | Meaning |
|---|---|
| `"query"` | free text over title, descriptions, author, types, labels (accents and case ignored). **The catalog is in English: translate the topic first.** |
| `--family F` / `--type T` | chart family, or exact chart types (repeatable, OR) |
| `--label L` | design technique (repeatable, **AND**) |
| `--tool T` | R, python, d3.js, tableau, illustrator… (repeatable, AND) |
| `--interactive` / `--no-interactive`, `--luminosity light\|dark`, `--since 2022` | narrow down |
| `--limit N` | default 8 |
| `--format json` | full records, for further processing |
| `--thumbs DIR` | also download the results' thumbnails into `DIR`, to look at them |
| `--vocab` | list every chart type and label with counts — run it when unsure of the exact names |

Search tactics:
- Start broad (family + one or two keywords), then add `--label` to target a technique.
- No hit on the topic? Drop the query and search by family + technique: the *form* matters more
  than the subject. A good migration chart can inspire an election chart.
- Without a query, results come favorites first, then most recent.

### 3. Look before you borrow

Pick the 3–5 most relevant results. Download their thumbnails with `--thumbs <scratch dir>` and
**view them** (they are WebP images you can read). The text says what the designer did; the
image shows how dense, how annotated, how colored it really is.

### 4. Present the references, then design

For each reference you keep, give the user:
- title, author, link to the original;
- **the specific idea to borrow** (e.g. "annotations placed directly on the peaks instead of a
  legend", "bivariate palette with a 3×3 key", "small multiples sorted by slope");
- why it fits this data and this audience.

Then propose the design, saying which idea comes from which reference. Adapt the ideas — never
present a copy of someone else's chart as original work.

End with the credit line:

> References from dataviz-inspiration.com by Yan Holtz (CC BY 4.0).

## Rules

- **Images are not reusable.** Thumbnails are screenshots of work by their authors, outside the
  CC BY 4.0 licence. Look at them; never embed, ship or redistribute them.
- **Credit** the catalog whenever you surface its content, and link to the original projects.
- If the catalog cannot be fetched and no cache exists, say so and carry on with your own
  judgment — do not invent references.
- Some entries have an empty "what the chart does": rely on the context and the thumbnail.
