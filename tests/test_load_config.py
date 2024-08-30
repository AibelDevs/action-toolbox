import json
import os
import pathlib

from action_tool.load_config import load_config
from action_tool.utils import deserialize_str


def test_basic_load_config(mock_local_proj_a_main):
    action_context = load_config()
    action_context.set_outputs()

    output_vars = pathlib.Path(os.getenv('GITHUB_OUTPUT')).read_text()
    data = dict(line.strip().split('=') for line in output_vars.splitlines() if line and not line.startswith('#'))
    toml_data = json.loads(deserialize_str(data["toml_data"]))
    mono_repos_data = toml_data["tool"]["mono_repo"]["project"]

    assert len(mono_repos_data) == 2

    mono_repo = mono_repos_data[0]
    assert mono_repo["name"] == action_context.mono_repo_project[0].name

    mono_repo = mono_repos_data[1]
    assert mono_repo["name"] == action_context.mono_repo_project[1].name
