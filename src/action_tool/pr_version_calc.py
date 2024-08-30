import os
import pathlib
import subprocess
from typing import Literal

import git

from action_tool.config import logger


class FailedSemantics(Exception):
    pass


def check_git_dir(git_dir, toml_file):
    if git_dir is None:
        git_dir = os.getcwd()

    if isinstance(git_dir, str):
        git_dir = pathlib.Path(git_dir).resolve().absolute()

    if isinstance(toml_file, str):
        toml_file = pathlib.Path(toml_file).resolve().absolute()

    source_main = os.getenv('SRC_MAIN_BRANCH_DIR')
    if source_main is not None:
        source_main = pathlib.Path(source_main)
        if not toml_file.is_relative_to(source_main):
            toml_file_rel = toml_file.relative_to(git_dir)
            toml_file = source_main / toml_file_rel
        git_dir = source_main

    return git_dir, toml_file


def calculate_version_w_semantic_release(toml_file,
                                         release_override: Literal["--patch", "--minor", "--major", None] = None,
                                         git_dir=None, debug_mode=False):
    print("Checking calculated version from semantic release")

    return run_semantic_release(toml_file=toml_file, release_override=release_override, git_dir=git_dir,
                                vcs_release=False, debug_mode=debug_mode,
                                calculate_only=True)


def run_semantic_release(toml_file, release_override: Literal["--patch", "--minor", "--major", None] = None,
                         git_dir=None, vcs_release=True, debug_mode=False, calculate_only=False):
    if git_dir is None:
        git_dir = os.getcwd()

    if isinstance(git_dir, str):
        git_dir = pathlib.Path(git_dir).resolve().absolute()

    if isinstance(toml_file, str):
        toml_file = pathlib.Path(toml_file).resolve().absolute()

    git_repo = git.Repo(git_dir)
    git_repo.git.config("user.email", "dummy@user.com")
    git_repo.git.config("user.name", "dummy_user")


    command = ["semantic-release", "--config", str(toml_file)]

    if debug_mode:
        command.append("-vv")

    if calculate_only:
        command.append("--noop")

    command.append("version")

    if calculate_only is False:
        command.append("--changelog")

    if release_override is not None:
        command.append(release_override)

    if vcs_release:
        command.append("--vcs-release")

    logger.info(f"Running command: {' '.join(command)} in '{git_dir}'")
    result = subprocess.run(command, capture_output=True, text=True, cwd=git_dir, encoding="utf-8")

    output = result.stdout.strip()

    if result.stderr:
        logger.error(result.stderr)
        if output == "":
            raise FailedSemantics(result.stderr)

    return output
