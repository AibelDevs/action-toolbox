import os
import pathlib
import shutil
import tempfile

import git
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def mock_env() -> pathlib.Path:
    with tempfile.TemporaryDirectory(prefix="00_env_") as temp_dir:
        temp_dir = pathlib.Path(temp_dir)
        output_file = temp_dir / "output.txt"
        env_file = temp_dir / "env.txt"
        output_file.touch()
        env_file.touch()
        os.environ["GITHUB_OUTPUT"] = output_file.as_posix()
        os.environ["GITHUB_ENV"] = env_file.as_posix()

        yield temp_dir


@pytest.fixture(scope="function")
def mock_remote() -> pathlib.Path:
    # Create a temporary directory for the remote repository
    with tempfile.TemporaryDirectory(prefix="00_remote_") as remote_temp_dir:
        # Initialize the remote repository
        remote_git_path = pathlib.Path(remote_temp_dir) / "remote_repo.git"
        remote_repo = git.Repo.init(remote_git_path, bare=True)
        yield pathlib.Path(remote_repo.git_dir)


@pytest.fixture(scope="function")
def mock_local_proj_a_main(proj_mono_1, mock_remote, mock_env) -> pathlib.Path:
    # Create a temporary directory for the local repository
    with tempfile.TemporaryDirectory(prefix="00_main_") as local_main_branch_temp_dir:
        local_main_branch_temp_dir = pathlib.Path(local_main_branch_temp_dir)

        # Create a Git repository in the temporary directory
        local_main_repo = git.Repo.clone_from(mock_remote, str(local_main_branch_temp_dir))

        # Copy the contents of the mono-repo to the temporary directory
        shutil.copytree(str(proj_mono_1), local_main_branch_temp_dir, dirs_exist_ok=True)

        # Add the username and email
        local_main_repo.git.config("user.email", "dummy_user@dummymail.com")
        local_main_repo.git.config("user.name", "dummy_user")

        # Perform any Git-related operations here, e.g., adding and committing files
        local_main_repo.git.add(".")
        local_main_repo.git.execute(["git", "commit", "-am", "feat: Initial Commit"])
        local_main_repo.git.push("origin", local_main_repo.active_branch.name, set_upstream=True)

        os.environ["SRC_MAIN_BRANCH_DIR"] = local_main_branch_temp_dir.as_posix()

        config_file = local_main_branch_temp_dir / "action_config.toml"
        os.environ["CONFIG_TOML_FILE"] = config_file.as_posix()

        yield local_main_branch_temp_dir


@pytest.fixture(scope="function")
def mock_local_proj_a_branch(proj_mono_1, mock_remote, mock_env, mock_local_proj_a_main) -> pathlib.Path:
    # Create a temporary directory for the local repository
    with tempfile.TemporaryDirectory(prefix="00_branch_") as local_branch_temp_dir:
        local_branch_temp_dir = pathlib.Path(local_branch_temp_dir)
        # Create a Git repository in the temporary directory
        local_branch_repo = git.Repo.clone_from(mock_remote, str(local_branch_temp_dir))

        # Add the username and email
        local_branch_repo.git.config("user.email", "dummy_user@dummymail.com")
        local_branch_repo.git.config("user.name", "dummy_user")

        # Perform any Git-related operations here, e.g., adding and committing files
        local_branch_repo.git.checkout("-b", "feat/new-stuff")
        with open(local_branch_temp_dir / "src/packages/a_sample_project/new_file.txt", "w") as f:
            f.write("This is a new file.")

        local_branch_repo.git.add(".")
        local_branch_repo.git.execute(["git", "commit", "-am", "feat: Another Commit"])
        local_branch_repo.git.push("origin", local_branch_repo.active_branch.name, set_upstream=True)

        yield local_branch_temp_dir, mock_local_proj_a_main
