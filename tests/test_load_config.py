import json
import os
import pathlib

from action_tool.load_config import load_config
from action_tool.monorepos import check_monorepo_labels
from action_tool.utils import deserialize_str, get_output


def test_basic_load_config(tmp_dir, proj_mono_1):
    cfg_file = proj_mono_1 / "action_config.toml"
    os.environ["CONFIG_TOML_FILE"] = cfg_file.as_posix()

    action_context = load_config()

    output_vars = pathlib.Path(os.getenv('GITHUB_OUTPUT')).read_text()
    data = dict(line.strip().split('=') for line in output_vars.splitlines() if line and not line.startswith('#'))
    toml_data = json.loads(deserialize_str(data["toml_data"]))
    mono_repos_data = toml_data["tool"]["mono_repo"]["project"]

    assert len(mono_repos_data) == 2

    mono_repo = mono_repos_data[0]
    assert mono_repo["name"] == action_context.mono_repo_project[0].name

    mono_repo = mono_repos_data[1]
    assert mono_repo["name"] == action_context.mono_repo_project[1].name


def test_mono_config_file(tmp_dir, proj_mono_1):
    cfg_file = proj_mono_1 / "action_config.toml"

    os.environ["CONFIG_TOML_FILE"] = cfg_file.as_posix()
    os.environ["LABELS"] = '["a-sample-project"]'

    check_monorepo_labels()

    output = get_output()

    assert output["MONO_CONFIG_FILE"] == "src/packages/a_sample_project/.semver.toml"
