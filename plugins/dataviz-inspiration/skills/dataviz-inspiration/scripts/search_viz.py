#!/usr/bin/env python3
"""Search the dataviz-inspiration.com catalog (Yan Holtz) from the command line.

Standard library only. The catalog is fetched from the official JSON endpoint
and cached locally (24 h by default); a stale cache is used when offline.

Catalog data: dataviz-inspiration.com by Yan Holtz, CC BY 4.0.
Images belong to their authors and are NOT covered by that licence.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Optional

CATALOG_URL = "https://www.dataviz-inspiration.com/viz-list.json"
DEFAULT_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "dataviz-inspiration" / "viz-list.json"
DEFAULT_ATTRIBUTION = "Data from dataviz-inspiration.com by Yan Holtz, licensed under CC BY 4.0"
UNKNOWN_DATE_PREFIX = "1000"  # the catalog's sentinel for "date unknown"

# Chart families, as defined in the site's source (util/sectionDescription.tsx, MIT).
FAMILIES: dict[str, list[str]] = {
    "distribution": ["violin", "density", "histogram", "boxplot", "ridgeline"],
    "correlation": ["scatter", "heatmap", "correlogram", "bubble", "connectedScatter", "density2d"],
    "ranking": ["barplot", "radar", "wordcloud", "parallel", "lollipop", "circularBarplot"],
    "partOfAWhole": ["treemap", "venn", "donut", "pie", "dendrogram", "circularPacking"],
    "evolution": ["line", "area", "stackedArea", "stream"],
    "map": ["map", "choropleth", "hexbin", "cartogram", "connection", "bubbleMap"],
    "flow": ["chordDiagram", "network", "sankey", "arc", "edgeBundling"],
}

# Field weights for free-text ranking.
WEIGHTS = {"title": 3, "chartTypes": 2, "labels": 2, "chartDescription": 2, "author": 1, "contextDescription": 1}


# --- loading ---------------------------------------------------------------

def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "dataviz-inspiration-skill"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def load_catalog(cache_path: Path = DEFAULT_CACHE, ttl_hours: float = 24, url: str = CATALOG_URL) -> dict[str, Any]:
    """Return the catalog, from a fresh cache, the network, or a stale cache (in that order)."""
    cache_path = Path(cache_path)
    if cache_path.exists() and time.time() - cache_path.stat().st_mtime < ttl_hours * 3600:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    try:
        raw = _download(url)
        data = json.loads(raw)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".tmp")
        tmp.write_bytes(raw)
        tmp.replace(cache_path)
        return data
    except (OSError, ValueError) as exc:
        if cache_path.exists():
            print(f"warning: could not refresh catalog ({exc}); using cached copy", file=sys.stderr)
            return json.loads(cache_path.read_text(encoding="utf-8"))
        raise RuntimeError(f"cannot fetch {url} and no cached copy at {cache_path}: {exc}") from exc


# --- filtering -------------------------------------------------------------

def _tool_names(item: dict[str, Any]) -> list[str]:
    return [(t["name"] if isinstance(t, dict) else t).lower() for t in item.get("tools") or []]


def filter_items(
    items: Iterable[dict[str, Any]],
    types: Optional[list[str]] = None,
    family: Optional[str] = None,
    labels: Optional[list[str]] = None,
    tools: Optional[list[str]] = None,
    interactive: Optional[bool] = None,
    luminosity: Optional[str] = None,
    since: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Types and family match ANY chart type; labels and tools must ALL be present."""
    wanted_types = set(types or [])
    if family:
        if family not in FAMILIES:
            raise ValueError(f"unknown family {family!r}; choose from {', '.join(FAMILIES)}")
        wanted_types |= set(FAMILIES[family])
    wanted_tools = {t.lower() for t in tools or []}

    out = []
    for it in items:
        if wanted_types and not wanted_types & set(it.get("chartTypes") or []):
            continue
        if labels and not set(labels) <= set(it.get("labels") or []):
            continue
        if wanted_tools and not wanted_tools <= set(_tool_names(it)):
            continue
        if interactive is not None and bool(it.get("interactive")) != interactive:
            continue
        if luminosity and luminosity not in (it.get("luminosity") or []):
            continue
        if since:
            date = it.get("date") or ""
            if date.startswith(UNKNOWN_DATE_PREFIX) or date < since:
                continue
        out.append(it)
    return out


# --- ranking ---------------------------------------------------------------

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("’", "'"))
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _tokens(text: str) -> list[str]:
    return [t.rstrip("s") if len(t) > 3 else t for t in re.findall(r"[a-z0-9]+", _normalize(text))]


def _field_text(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    if isinstance(value, list):
        return " ".join(value)
    return value or ""


def _recency_key(item: dict[str, Any]) -> str:
    date = item.get("date") or ""
    return "" if date.startswith(UNKNOWN_DATE_PREFIX) else date


def score(item: dict[str, Any], query_tokens: list[str]) -> int:
    total = 0
    for field, weight in WEIGHTS.items():
        field_tokens = set(_tokens(_field_text(item, field)))
        total += weight * sum(1 for q in query_tokens if q in field_tokens)
    return total


def rank(items: Iterable[dict[str, Any]], query: Optional[str]) -> list[dict[str, Any]]:
    """Rank by query score; without a query, favorites first then most recent."""
    items = list(items)
    if not query:
        return sorted(items, key=lambda it: (bool(it.get("favorite")), _recency_key(it)), reverse=True)
    q = _tokens(query)
    scored = [(score(it, q), it) for it in items]
    scored = [(s, it) for s, it in scored if s > 0]
    scored.sort(key=lambda p: (p[0], bool(p[1].get("favorite")), _recency_key(p[1])), reverse=True)
    return [it for _, it in scored]


# --- thumbnails ------------------------------------------------------------

def download_thumbnails(results: list[dict[str, Any]], dest: Path) -> list[Path]:
    """Save each result's thumbnail as <id>-<name> in dest, for viewing only. Failures are skipped."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for it in results:
        url = (it.get("images") or {}).get("thumbnail")
        if not url:
            continue
        try:
            data = _download(url)
        except OSError as exc:
            print(f"warning: thumbnail of [{it['id']}] unavailable ({exc})", file=sys.stderr)
            continue
        path = dest / f"{it['id']}-{url.rsplit('/', 1)[-1]}"
        path.write_bytes(data)
        paths.append(path)
    return paths


# --- rendering -------------------------------------------------------------

def _date_label(item: dict[str, Any]) -> str:
    date = item.get("date") or ""
    return "date unknown" if not date or date.startswith(UNKNOWN_DATE_PREFIX) else date


def render_markdown(results: list[dict[str, Any]], catalog: dict[str, Any], total: int) -> str:
    lines = [f"{total} matching visualizations, showing {len(results)}.", ""]
    for it in results:
        tools = ", ".join(t["name"] if isinstance(t, dict) else t for t in it.get("tools") or [])
        lines.append(f"## [{it['id']}] {it['title']} — {it.get('author', '?')} ({_date_label(it)})")
        lines.append(f"- Original: {it['url']}")
        meta = f"- Chart types: {', '.join(it.get('chartTypes') or [])} | Labels: {', '.join(it.get('labels') or [])}"
        if tools:
            meta += f" | Tools: {tools}"
        meta += f" | {'interactive' if it.get('interactive') else 'static'}, {'/'.join(it.get('luminosity') or [])}"
        lines.append(meta)
        chart_desc = (it.get("chartDescription") or "").strip()
        if chart_desc:
            lines.append(f"- What the chart does: {chart_desc}")
        lines.append(f"- Context: {(it.get('contextDescription') or '').strip()}")
        thumb = (it.get("images") or {}).get("thumbnail")
        if thumb:
            lines.append(f"- Thumbnail (look only, do not reuse): {thumb}")
        lines.append("")
    lines.append(f"_{catalog.get('attribution', DEFAULT_ATTRIBUTION)}. Images © their respective authors._")
    return "\n".join(lines)


def render_vocab(items: list[dict[str, Any]]) -> str:
    type_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    for it in items:
        for t in it.get("chartTypes") or []:
            type_counts[t] = type_counts.get(t, 0) + 1
        for lab in it.get("labels") or []:
            label_counts[lab] = label_counts.get(lab, 0) + 1
    lines = ["Chart types by family (--family / --type):"]
    for fam, types in FAMILIES.items():
        lines.append(f"- {fam}: " + ", ".join(f"{t} ({type_counts.get(t, 0)})" for t in types))
    lines.append("")
    lines.append("Labels (--label, combined with AND):")
    lines.append(", ".join(f"{lab} ({n})" for lab, n in sorted(label_counts.items(), key=lambda p: -p[1])))
    return "\n".join(lines)


# --- CLI -------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Search the dataviz-inspiration.com catalog.")
    p.add_argument("query", nargs="?", help="free-text query (English works best), e.g. 'election turnout'")
    p.add_argument("--type", action="append", dest="types", help="chart type, repeatable (OR)")
    p.add_argument("--family", choices=list(FAMILIES), help="chart family")
    p.add_argument("--label", action="append", dest="labels", help="design technique, repeatable (AND)")
    p.add_argument("--tool", action="append", dest="tools", help="tool used (R, python, d3.js…), repeatable (AND)")
    p.add_argument("--interactive", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--luminosity", choices=["light", "dark"])
    p.add_argument("--since", help="only entries from this date on (YYYY or YYYY-MM)")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p.add_argument("--vocab", action="store_true", help="list chart types and labels with counts, then exit")
    p.add_argument("--thumbs", type=Path, metavar="DIR", help="also download the results' thumbnails into DIR (to look at, never to reuse)")
    p.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--ttl-hours", type=float, default=24)
    args = p.parse_args(argv)

    try:
        catalog = load_catalog(cache_path=args.cache, ttl_hours=args.ttl_hours)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    items = catalog.get("items") or []

    if args.vocab:
        print(render_vocab(items))
        return 0

    try:
        filtered = filter_items(
            items, types=args.types, family=args.family, labels=args.labels, tools=args.tools,
            interactive=args.interactive, luminosity=args.luminosity, since=args.since,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    ranked = rank(filtered, args.query)
    results = ranked[: args.limit]

    if args.format == "json":
        print(json.dumps({
            "total": len(ranked),
            "attribution": catalog.get("attribution", DEFAULT_ATTRIBUTION),
            "imagesNotice": catalog.get("imagesNotice"),
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(results, catalog, total=len(ranked)))
    if args.thumbs:
        for path in download_thumbnails(results, args.thumbs):
            print(f"thumbnail: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
