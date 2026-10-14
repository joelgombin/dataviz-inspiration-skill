## Decision: ship a Claude skill (SKILL.md + stdlib Python CLI) that reads the dataviz-inspiration.com catalog live, rather than an MCP server or a copied dataset

## Context: give coding agents a visual culture before they design charts. Yan Holtz opened his catalog (CC BY 4.0) and published viz-list.json + llms.txt on 2026-10-14.

## Alternatives considered:
- MCP server exposing search_viz(): works in any client, but needs hosting and maintenance.
- Copying/enriching the catalog in this repo: offline-friendly, but forks Yan's curation and goes stale.
- Pure SKILL.md telling the agent to WebFetch the JSON: no code, but a 600 KB JSON in context is wasteful and filtering by hand is error-prone.

## Reasoning: the official JSON endpoint already exists; a tiny stdlib script filters and ranks it, so only 3-8 relevant entries reach the agent's context. Zero infra, single source of truth stays with Yan, installable as a Claude Code plugin marketplace.

## Trade-offs accepted: Claude-centric packaging (other agents must copy the folder); needs network on first use (24 h cache, stale fallback); keyword ranking is naive (no embeddings) — English queries only.
