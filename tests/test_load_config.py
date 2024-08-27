import json
import os
import pathlib
import shutil

import pytest
import tempfile
from action_tool.load_config import load_config
from action_tool.monorepos import get_monorepo_config_file
from action_tool.utils import deserialize_str, get_output


@pytest.fixture
def tmp_dir() -> pathlib.Path:
    # Make a temp directory.
    local_dir = pathlib.Path(__file__).parent.absolute() / "temp"
    local_dir.mkdir(exist_ok=True)
    temp_dir = pathlib.Path(tempfile.mkdtemp(dir=local_dir))
    output_file = temp_dir / "output.txt"
    env_file = temp_dir / "env.txt"
    output_file.touch()
    env_file.touch()
    os.environ["GITHUB_OUTPUT"] = output_file.as_posix()
    os.environ["GITHUB_ENV"] = env_file.as_posix()

    yield temp_dir

    shutil.rmtree(temp_dir)


def test_basic_load_config(tmp_dir):
    cfg_file = pathlib.Path(__file__).parent.absolute() / "files/monorepo1.toml"
    os.environ["CONFIG_TOML_FILE"] = cfg_file.as_posix()
    load_config()

    output_vars = pathlib.Path(os.getenv('GITHUB_OUTPUT')).read_text()
    data = dict(line.strip().split('=') for line in output_vars.splitlines() if line and not line.startswith('#'))
    toml_data = json.loads(deserialize_str(data["toml_data"]))
    mono_repos_data = toml_data["tool"]["mono_repo"]

    assert len(mono_repos_data) == 1
    mono_repo = mono_repos_data[0]
    assert mono_repo["name"] == 'a-sample-project'


def test_mono_config_file(tmp_dir):
    cfg_file = pathlib.Path(__file__).parent.absolute() / "files/monorepo1.toml"

    os.environ["CONFIG_TOML_FILE"] = cfg_file.as_posix()
    os.environ["STARTSWITH"] = "a-sample"
    os.environ["LABELS"] = "a-sample-project"

    get_monorepo_config_file()

    output = get_output()

    assert output["MONO_CONFIG_FILE"] == "src/packages/A.Sample.Project/.semver.toml"
