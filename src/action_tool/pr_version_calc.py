import os
import pathlib
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Literal

import git
from action_tool.config import logger
from action_tool.git_remote_adapter import GitRemoteRepo, is_in_gitea_action, is_in_github_action


def check_git_dir(git_dir, toml_file):
    if git_dir is None:
        git_dir = os.getcwd()

    if isinstance(git_dir, str):
        git_dir = pathlib.Path(git_dir).resolve().absolute()

    source_main = os.getenv('SRC_MAIN_BRANCH_DIR')
    if source_main is not None:
        source_main = pathlib.Path(source_main)
        toml_file_rel = toml_file.relative_to(git_dir)
        git_dir = source_main
        toml_file = source_main / toml_file_rel

    return git_dir, toml_file


@contextmanager
def run_with_dummy_pr_commit(pr_title, git_dir=None):
    if is_in_gitea_action() or is_in_github_action():
        # Perform any Git-related operations here, e.g., adding and committing files
        # with open(git_dir / "new_file.txt", "w") as f:
        #     f.write("This is a new file.")
        temp_git_repo = git.Repo(git_dir)
        temp_git_repo.git.config("user.email", "dummy@user.com")
        temp_git_repo.git.config("user.name", "dummy_user")
        # temp_git_repo.git.add(".")
        temp_git_repo.git.execute(["git", "commit","--allow-empty", "-m", pr_title])
        yield git_dir
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = pathlib.Path(temp_dir)

            # Copy the contents of the git directory to the temporary directory
            shutil.copytree(git_dir, temp_dir, dirs_exist_ok=True)

            # Add the username and email
            temp_git_repo = git.Repo(temp_dir)
            temp_git_repo.git.config("user.email", "dummy@user.com")
            temp_git_repo.git.config("user.name", "dummy_user")

            # Perform any Git-related operations here, e.g., adding and committing files
            with open(temp_dir / "new_file.txt", "w") as f:
                f.write("This is a new file.")

            temp_git_repo.git.add(".")
            temp_git_repo.git.execute(["git", "commit", "-am", pr_title])
            yield temp_dir


def get_override_from_version_diff(old_version, new_version):
    old_tuple = tuple(int(x) for x in old_version.split('.'))
    new_tuple = tuple(int(x) for x in new_version.split('.'))
    # diff = new_tuple - old_tuple
    # result = old.compare(new)
    #
    # print(result)


def calculate_version_w_semantic_release(release_label, pr_title, toml_file, git_dir=None, debug_mode=False):
    print("Checking calculated version from semantic release")
    if release_label == "release-skip":
        return

    git_dir, toml_file = check_git_dir(git_dir, toml_file)
    forced_release = GitRemoteRepo.release_label_map[release_label]

    with run_with_dummy_pr_commit(pr_title, git_dir) as temp_dir:
        toml_file_rel = toml_file.relative_to(git_dir)
        toml_file_dummy = temp_dir / toml_file_rel
        command = ["semantic-release", "--config", str(toml_file_dummy), "--noop"]

        if debug_mode:
            command.append("-v")

        command.append("version")

        if forced_release:
            command.append(forced_release)

        print(f"Running command: {' '.join(command)} using {temp_dir=}, {toml_file_dummy=}")
        result = subprocess.run(command, capture_output=True, text=True, cwd=temp_dir)

        if result.stderr:
            logger.error(result.stderr)
            for fp in temp_dir.iterdir():
                logger.error(f"{fp}")

    output = result.stdout.strip()
    print(f'Captured Version Name: "{output}"')

    return output


def run_semantic_release(toml_file, pr_title, release_override: Literal["--patch", "--minor", "--major", None] = None,
                         git_dir=None, vcs_release=True, debug_mode=False):
    git_dir, toml_file = check_git_dir(git_dir, toml_file)

    with run_with_dummy_pr_commit(pr_title, git_dir) as temp_dir:
        toml_file_rel = toml_file.relative_to(git_dir)
        toml_file_dummy = temp_dir / toml_file_rel
        command = ["semantic-release", "--config", str(toml_file_dummy), "version", "--changelog"]

        if release_override is not None:
            command.append(release_override)

        if vcs_release:
            command.append("--vcs-release")

        if debug_mode:
            command.append("--log-level=DEBUG")

        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, cwd=git_dir)

    if result.stderr:
        logger.error(result.stderr)

    output = result.stdout.strip()
    return output
