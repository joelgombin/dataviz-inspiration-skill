## Decision: one normalized catalog over several galleries (dataviz-inspiration.com + Dataviz Index), each read live from its public endpoint; method references as a static markdown file

## Context: the skill was meant from the start to combine several sources (Yan Holtz's gallery, Dataviz Index, and the method references collected for André: data-to-viz, Insee, icem7, ggplot2). v0.1 only covered Yan's.

## Alternatives considered:
- Crawl Dataviz Index pages + screenshots and write our own descriptions with a vision model (initial plan): costly, and redundant once we found that /api/blocks lists all entries and each entry page carries WeDoData's own comment.
- Copy Dataviz Index into the repo: no licence on their content — not an option.
- Separate scripts per source: the agent would have to merge results itself.

## Reasoning: a common schema (uid, source, lang, families, chartTypes, labels, themes, description…) lets one query span both galleries; families are mapped from each source's native types. Dataviz Index's list API has no descriptions, so they are fetched on demand for displayed results only (≤ limit requests, cached). One failing source degrades gracefully.

## Trade-offs accepted: /api/blocks is an undocumented internal endpoint (may change; tell WeDoData); the Dataviz Index → family mapping is our interpretation; bilingual keyword search instead of semantic search.
