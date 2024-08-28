import os
import pathlib
import shutil
import tempfile

import git
import pytest


@pytest.fixture(scope="session")
def mock_local_proj_a(proj_mono_1) -> pathlib.Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = pathlib.Path(temp_dir)
        output_file = temp_dir / "output.txt"
        env_file = temp_dir / "env.txt"
        output_file.touch()
        env_file.touch()
        os.environ["GITHUB_OUTPUT"] = output_file.as_posix()
        os.environ["GITHUB_ENV"] = env_file.as_posix()

        # Create a temporary directory for the remote repository
        with tempfile.TemporaryDirectory() as remote_temp_dir:

            # Initialize the remote repository
            remote_repo = git.Repo.init(pathlib.Path(remote_temp_dir) / "remote_repo.git", bare=True)

            # Create a temporary directory for the local repository
            with tempfile.TemporaryDirectory() as local_temp_dir:
                # Copy the contents of the mono-repo to the temporary directory
                shutil.copytree(str(proj_mono_1), local_temp_dir, dirs_exist_ok=True)

                # Create a Git repository in the temporary directory
                local_repo = git.Repo.init(str(local_temp_dir))

                # Add the remote repository
                local_repo.create_remote("origin", url=remote_repo.git_dir)

                # Add the username and email
                local_repo.git.config("user.email", "dummy_user@dummymail.com")
                local_repo.git.config("user.name", "dummy_user")

                # Perform any Git-related operations here, e.g., adding and committing files
                local_repo.git.add(".")
                local_repo.git.execute(["git", "commit", "-am", "feat: Initial Commit"])
                local_repo.git.push("origin", local_repo.active_branch.name, set_upstream=True)
                yield pathlib.Path(local_temp_dir)
