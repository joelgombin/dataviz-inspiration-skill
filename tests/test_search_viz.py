import json
import os
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/dataviz-inspiration/skills/dataviz-inspiration/scripts"
sys.path.insert(0, str(SCRIPTS))

import search_viz as sv  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "catalog.json"


@pytest.fixture
def catalog():
    return json.loads(FIXTURE.read_text())


@pytest.fixture
def items(catalog):
    return catalog["items"]


def ids(results):
    return [r["id"] for r in results]


# --- filtering -------------------------------------------------------------

def test_filter_by_type_matches_any_listed_type(items):
    assert ids(sv.filter_items(items, types=["sankey", "lollipop"])) == [3, 4]


def test_filter_by_family_expands_to_chart_types(items):
    # map family = choropleth, map, hexbin… -> items 2 and 4
    assert ids(sv.filter_items(items, family="map")) == [2, 4]
    # evolution family = line, area, stackedArea, stream
    assert ids(sv.filter_items(items, family="evolution")) == [1]


def test_unknown_family_raises(items):
    with pytest.raises(ValueError):
        sv.filter_items(items, family="nope")


def test_labels_are_combined_with_and(items):
    assert ids(sv.filter_items(items, labels=["annotation"])) == [1, 2, 4, 5]
    assert ids(sv.filter_items(items, labels=["annotation", "color palette"])) == [2]


def test_filter_by_tool_is_case_insensitive(items):
    assert ids(sv.filter_items(items, tools=["r"])) == [3]
    assert ids(sv.filter_items(items, tools=["D3.js"])) == [2]


def test_filter_interactive_and_luminosity(items):
    assert ids(sv.filter_items(items, interactive=True)) == [2]
    assert ids(sv.filter_items(items, luminosity="dark")) == [3]


def test_filter_since_ignores_unknown_dates(items):
    # "1000-01" is the catalog's sentinel for an unknown date
    assert ids(sv.filter_items(items, since="2022")) == [1, 4]


# --- free-text ranking -----------------------------------------------------

def test_query_is_accent_and_case_insensitive(items):
    results = sv.rank(items, "ELECTIONS municipales")
    assert ids(results)[0] == 2


def test_query_ranks_title_hits_above_description_hits(items):
    # "map" appears in descriptions of 2 and 4, never in a title;
    # "gas" is in the title of 4 -> 4 first
    assert ids(sv.rank(items, "gas map"))[0] == 4


def test_query_drops_items_without_any_hit(items):
    assert ids(sv.rank(items, "lollipop")) == [3]


def test_no_query_sorts_favorites_then_most_recent(items):
    assert ids(sv.rank(items, None)) == [2, 4, 1, 3, 5]


# --- catalog loading & cache ----------------------------------------------

def test_load_uses_fresh_cache_without_network(tmp_path, catalog, monkeypatch):
    cache = tmp_path / "viz-list.json"
    cache.write_text(json.dumps(catalog))

    def boom(*a, **k):
        raise AssertionError("network should not be called")

    monkeypatch.setattr(sv, "_download", boom)
    assert sv.load_catalog(cache_path=cache, ttl_hours=24)["count"] == 5


def test_load_refreshes_stale_cache(tmp_path, catalog, monkeypatch):
    cache = tmp_path / "viz-list.json"
    cache.write_text(json.dumps({"count": 0, "items": []}))
    old = time.time() - 48 * 3600
    os.utime(cache, (old, old))
    monkeypatch.setattr(sv, "_download", lambda url: json.dumps(catalog).encode())
    assert sv.load_catalog(cache_path=cache, ttl_hours=24)["count"] == 5
    assert json.loads(cache.read_text())["count"] == 5


def test_load_falls_back_to_stale_cache_when_offline(tmp_path, catalog, monkeypatch):
    cache = tmp_path / "viz-list.json"
    cache.write_text(json.dumps(catalog))
    old = time.time() - 48 * 3600
    os.utime(cache, (old, old))

    def offline(url):
        raise OSError("no network")

    monkeypatch.setattr(sv, "_download", offline)
    assert sv.load_catalog(cache_path=cache, ttl_hours=24)["count"] == 5


def test_load_without_cache_and_offline_raises(tmp_path, monkeypatch):
    def offline(url):
        raise OSError("no network")

    monkeypatch.setattr(sv, "_download", offline)
    with pytest.raises(RuntimeError):
        sv.load_catalog(cache_path=tmp_path / "missing.json", ttl_hours=24)


# --- rendering -------------------------------------------------------------

def test_markdown_output_carries_attribution_and_links(catalog):
    out = sv.render_markdown(catalog["items"][:1], catalog, total=1)
    assert "Here’s When We Expect Omicron to Peak" in out
    assert "https://www.nytimes.com/omicron" in out
    assert "omicron-zoom.webp" in out
    assert "CC BY 4.0" in out


def test_unknown_date_is_rendered_as_unknown(catalog):
    out = sv.render_markdown([catalog["items"][4]], catalog, total=1)
    assert "1000" not in out
    assert "date unknown" in out


# --- CLI -------------------------------------------------------------------

def test_cli_json_output(tmp_path, catalog, monkeypatch, capsys):
    cache = tmp_path / "viz-list.json"
    cache.write_text(json.dumps(catalog))
    monkeypatch.setattr(sv, "_download", lambda url: (_ for _ in ()).throw(OSError()))
    code = sv.main(["--cache", str(cache), "--family", "map", "--format", "json", "--limit", "1"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 2
    assert [r["id"] for r in payload["results"]] == [2]
    assert "CC BY 4.0" in payload["attribution"]


def test_cli_vocab_lists_types_by_family_with_counts(tmp_path, catalog, capsys):
    cache = tmp_path / "viz-list.json"
    cache.write_text(json.dumps(catalog))
    assert sv.main(["--cache", str(cache), "--vocab"]) == 0
    out = capsys.readouterr().out
    assert "map" in out and "choropleth (2)" in out
    assert "annotation (4)" in out


def test_empty_chart_description_line_is_omitted(catalog):
    item = dict(catalog["items"][0], chartDescription="")
    out = sv.render_markdown([item], catalog, total=1)
    assert "What the chart does" not in out


def test_download_thumbnails_writes_one_file_per_result(tmp_path, items, monkeypatch):
    monkeypatch.setattr(sv, "_download", lambda url: b"img:" + url.encode())
    paths = sv.download_thumbnails(items[:2], tmp_path)
    assert [p.name for p in paths] == ["1-omicron-zoom.webp", "2-mun-zoom.webp"]
    assert paths[0].read_bytes() == b"img:https://example.org/omicron-zoom.webp"


def test_download_thumbnails_skips_failures(tmp_path, items, monkeypatch):
    def flaky(url):
        if "omicron" in url:
            raise OSError("404")
        return b"ok"

    monkeypatch.setattr(sv, "_download", flaky)
    assert [p.name for p in sv.download_thumbnails(items[:2], tmp_path)] == ["2-mun-zoom.webp"]
