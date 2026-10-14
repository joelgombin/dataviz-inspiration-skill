#!/usr/bin/env python3
"""PreToolUse hook: ask the agent to load the dataviz-inspiration skill before writing chart code.

Skills are chosen from their description, and agents busy fetching data tend to go straight to
plotting code without loading any skill. This hook spots chart/map-drawing code in Write, Edit,
NotebookEdit and Bash calls and, if the skill has not been loaded in the session, denies the call
ONCE with a reason telling the agent to load it first. A retry goes through, so the hook can
never lock anyone out.

Opt out with DATAVIZ_INSPIRATION_HOOK=off. Never fails closed: any error means "allow".
Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SKILL = "dataviz-inspiration"

# Chart/map-drawing code, across the usual languages and libraries.
PLOT_PATTERN = re.compile(
    r"""
    matplotlib | pyplot | \bplt\.\w+\( | \bsns\.\w+\( | seaborn
    | plotly | \bpx\.\w+\( | \bgo\.Figure | altair | \balt\.Chart | bokeh | folium | plotnine | pygal
    | \.plot\( | \.hist\( | \.choropleth\(
    | \bggplot\( | \bgeom_\w+\( | \btm_shape\( | \bleaflet\(
    | \bd3\.(select|scale|geo|axis|line|area|arc|pie|stack|forceSimulation)
    | \bvega | \bPlot\.plot\( | @observablehq/plot | new\s+Chart\( | echarts | recharts | @nivo/ | @visx/
    | maplibre | mapbox-gl | deck\.gl | kepler\.gl
    """,
    re.IGNORECASE | re.VERBOSE,
)

REASON = (
    "dataviz-inspiration: this call writes chart/map-drawing code, and the dataviz-inspiration "
    "skill has not been loaded in this session. Load it now with the Skill tool "
    "(skill: \"dataviz-inspiration\"), find 3-5 published references, look at them, then write "
    "this code borrowing their ideas and cite them with their links. If this call is not about "
    "designing a visualization (fixing a test, a small tweak to an existing chart the user "
    "already approved…), just retry the same call: this check fires only once per session."
)


def _text_of(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "Bash":
        return tool_input.get("command") or ""
    parts = [tool_input.get(k) or "" for k in ("content", "new_string", "new_source")]
    parts += [e.get("new_string") or "" for e in tool_input.get("edits") or [] if isinstance(e, dict)]
    return "\n".join(parts)


def _skill_loaded(transcript_path: str) -> bool:
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if SKILL not in line:
                    continue
                if re.search(r'"skill"\s*:\s*"(?:[\w.-]+:)?' + SKILL + r'"', line):
                    return True  # invoked by the agent through the Skill tool
                if re.search(r"Base directory for this skill: \S*/" + SKILL + r"\b", line):
                    return True  # typed by the user as /dataviz-inspiration
    except OSError:
        pass
    return False


def _marker(session_id: str) -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or str(Path.home() / ".cache" / SKILL)
    safe = re.sub(r"[^\w.-]", "_", session_id) or "unknown"
    return Path(base) / "hook-sessions" / safe


def main() -> int:
    if os.environ.get("DATAVIZ_INSPIRATION_HOOK", "").lower() in {"off", "0", "false", "no"}:
        return 0
    try:
        event = json.load(sys.stdin)
        tool_name = event.get("tool_name") or ""
        tool_input = event.get("tool_input") or {}
        if not PLOT_PATTERN.search(_text_of(tool_name, tool_input)):
            return 0
        if _skill_loaded(event.get("transcript_path") or ""):
            return 0
        marker = _marker(str(event.get("session_id") or ""))
        if marker.exists():
            return 0  # already nudged in this session: let the agent decide
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    except Exception:  # never block because of a bug in this hook
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
