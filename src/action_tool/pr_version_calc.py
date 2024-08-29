import os
import pathlib
import subprocess
from typing import Literal

from action_tool.config import logger
from action_tool.git_remote_adapter import GitRemoteRepo

def check_git_dir(git_dir, toml_file):
    if git_dir is None:
        git_dir = os.getcwd()
    if isinstance(git_dir, str):
        git_dir = pathlib.Path(git_dir)

    source_main = os.getenv('SRC_MAIN_BRANCH_DIR')
    if source_main is not None:
        source_main = pathlib.Path(source_main)
        toml_file_rel = toml_file.relative_to(git_dir)
        git_dir = source_main
        toml_file = source_main / toml_file_rel

    return git_dir, toml_file


def calculate_version(release_label, toml_file, git_dir=None):
    git_dir, toml_file = check_git_dir(git_dir, toml_file)
    print("Checking calculated version from semantic release")
    release_label_map = GitRemoteRepo.release_label_map

    forced_release = release_label_map[release_label]

    if release_label == "release-skip":
        return

    command = ["semantic-release", "--config", str(toml_file), "--noop", "version"]
    if forced_release:
        command.append(forced_release)

    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, cwd=git_dir)

    if result.stderr:
        logger.error(result.stderr)

    output = result.stdout.strip()
    print(f'Captured Version Name: "{output}"')

    return output


def run_semantic_release(toml_file, release_override: Literal["--patch", "--minor", "--major", None] = None,
                         git_dir=None, vcs_release=True):
    git_dir, toml_file = check_git_dir(git_dir, toml_file)

    command = ["semantic-release", "--config", str(toml_file), "version", "--changelog"]

    if vcs_release:
        command.append("--vcs-release")

    if release_override is not None:
        command.append(release_override)

    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, cwd=git_dir)

    if result.stderr:
        print(result.stderr)

    output = result.stdout.strip()
    return output
