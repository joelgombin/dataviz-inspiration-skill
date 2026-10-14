import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "plugins/dataviz-inspiration/hooks/require_inspiration.py"

PLOT_CODE = "import geopandas as gpd\nimport matplotlib.pyplot as plt\ngdf.plot(column='abst', ax=ax)\nplt.savefig('carte.png')\n"


def run(payload, data_dir, env_extra=None):
    env = dict(os.environ, CLAUDE_PLUGIN_DATA=str(data_dir))
    env.pop("DATAVIZ_INSPIRATION_HOOK", None)
    env.update(env_extra or {})
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=10
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def payload(tool_name, tool_input, transcript, session="s1"):
    return {
        "session_id": session,
        "transcript_path": str(transcript),
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


@pytest.fixture
def transcript(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"message": {"role": "user", "content": "fais-moi une carte"}}) + "\n")
    return t


def is_deny(out):
    return out is not None and out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_denies_plot_code_when_skill_not_loaded(tmp_path, transcript):
    out = run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript), tmp_path / "data")
    assert is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "dataviz-inspiration" in reason and "Skill" in reason


def test_denies_only_once_per_session(tmp_path, transcript):
    data = tmp_path / "data"
    p = payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript)
    assert is_deny(run(p, data))
    assert run(p, data) is None
    # another session is nudged again
    assert is_deny(run(payload("Write", {"file_path": "/x/c.py", "content": PLOT_CODE}, transcript, session="s2"), data))


def test_allows_when_skill_already_loaded(tmp_path, transcript):
    with transcript.open("a") as f:
        f.write(json.dumps({"message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "dataviz-inspiration", "args": "carte"}}]}}) + "\n")
    assert run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript), tmp_path / "data") is None


def test_allows_when_skill_loaded_under_plugin_namespace(tmp_path, transcript):
    with transcript.open("a") as f:
        f.write(json.dumps({"message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "dataviz-inspiration:dataviz-inspiration"}}]}}) + "\n")
    assert run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript), tmp_path / "data") is None


def test_allows_when_skill_typed_as_slash_command(tmp_path, transcript):
    with transcript.open("a") as f:
        f.write(json.dumps({"message": {"role": "user", "content": [
            {"type": "text", "text": "Base directory for this skill: /Users/x/.claude/skills/dataviz-inspiration\n\n# Dataviz inspiration"}]}}) + "\n")
    assert run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript), tmp_path / "data") is None


def test_ignores_code_without_plotting(tmp_path, transcript):
    code = "import pandas as pd\ndf = pd.read_csv('x.csv')\nprint(df.describe())\n"
    assert run(payload("Write", {"file_path": "/x/a.py", "content": code}, transcript), tmp_path / "data") is None


def test_detects_plotting_in_edit_bash_and_notebook(tmp_path, transcript):
    data = tmp_path / "data"
    assert is_deny(run(payload("Edit", {"file_path": "/x/a.py", "old_string": "x", "new_string": "fig = px.choropleth(df)"}, transcript, "e"), data))
    assert is_deny(run(payload("Bash", {"command": "python3 - <<'EOF'\nimport matplotlib.pyplot as plt\nEOF"}, transcript, "b"), data))
    assert is_deny(run(payload("NotebookEdit", {"notebook_path": "/x/n.ipynb", "new_source": "ggplot(df, aes(x, y)) + geom_line()"}, transcript, "n"), data))
    assert is_deny(run(payload("Write", {"file_path": "/x/index.html", "content": "<script>d3.select('#map').append('svg')</script>"}, transcript, "w"), data))


def test_bash_running_an_existing_script_is_not_blocked(tmp_path, transcript):
    # running `python3 carte.py` contains no plotting code itself
    assert run(payload("Bash", {"command": "python3 carte.py"}, transcript), tmp_path / "data") is None


def test_opt_out_env_var(tmp_path, transcript):
    out = run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, transcript), tmp_path / "data",
              {"DATAVIZ_INSPIRATION_HOOK": "off"})
    assert out is None


def test_missing_transcript_still_works(tmp_path):
    out = run(payload("Write", {"file_path": "/x/carte.py", "content": PLOT_CODE}, tmp_path / "nope.jsonl"), tmp_path / "data")
    assert is_deny(out)


def test_garbage_stdin_never_blocks(tmp_path):
    proc = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PLUGIN_DATA=str(tmp_path)), timeout=10)
    assert proc.returncode == 0 and proc.stdout.strip() == ""
