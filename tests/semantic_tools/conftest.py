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


@pytest.fixture(scope="session")
def mock_local_proj_a_branch(proj_mono_1) -> pathlib.Path:
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
            remote_git_path = pathlib.Path(remote_temp_dir) / "remote_repo.git"
            remote_repo = git.Repo.init(remote_git_path, bare=True)

            # Create a temporary directory for the local repository
            with tempfile.TemporaryDirectory() as local_main_branch_temp_dir:
                local_main_branch_temp_dir = pathlib.Path(local_main_branch_temp_dir)

                # Create a Git repository in the temporary directory
                local_main_repo = git.Repo.clone_from(remote_repo.git_dir, str(local_main_branch_temp_dir))

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

                # Create a temporary directory for the local repository
                with tempfile.TemporaryDirectory() as local_branch_temp_dir:
                    local_branch_temp_dir = pathlib.Path(local_branch_temp_dir)
                    # Create a Git repository in the temporary directory
                    local_branch_repo = git.Repo.clone_from(remote_repo.git_dir, str(local_branch_temp_dir))

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

                    yield local_branch_temp_dir, local_main_branch_temp_dir

