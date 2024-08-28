import os
import subprocess
from typing import Literal

from action_tool.config import logger
from action_tool.git_remote_adapter import GitRemoteRepo


def calculate_version(release_label, toml_file, git_dir=None):
    if git_dir is None:
        git_dir = os.getcwd()

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

    new_version = f"v{output}"
    return new_version


def run_semantic_release(toml_file, release_override: Literal["--patch", "--minor", "--major", None] = None,
                         git_dir=None):
    if git_dir is None:
        git_dir = os.getcwd()
    command = ["semantic-release", "--config", str(toml_file), "version", "--changelog", "--vcs-release"]
    if release_override is not None:
        command.append(release_override)

    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, cwd=git_dir)

    if result.stderr:
        print(result.stderr)

    output = result.stdout.strip()
    return output
