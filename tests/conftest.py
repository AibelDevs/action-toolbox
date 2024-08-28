import os
import pathlib
import shutil
import tempfile

import pytest

ROOT_DIR = pathlib.Path(__file__).parent.parent.absolute()


@pytest.fixture(scope="session")
def proj_mono_1() -> pathlib.Path:
    proj1 = ROOT_DIR / "tests/files/proj_mono_1"
    return proj1


@pytest.fixture(scope="session")
def workflows_dir() -> pathlib.Path:
    proj1 = ROOT_DIR / ".github/workflows"
    return proj1


@pytest.fixture(scope="session")
def root_dir() -> pathlib.Path:
    return ROOT_DIR


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
