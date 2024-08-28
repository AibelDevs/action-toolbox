import re
import subprocess

from action_tool.utils import set_env, set_output
from git import Repo


def add_commit_for_semantic_release_calculation(repo_path, title):
    print(f"Adding commit with title: {title}")
    repo = Repo(repo_path)
    repo.config_writer().set_value("user", "email", "dummy@dummy.com").release()
    repo.config_writer().set_value("user", "name", "dummy").release()
    repo.index.commit(title, allow_empty=True)


def get_latest_release_tag(repo_path):
    print("Getting latest release tag")
    repo = Repo(repo_path)
    all_tags = repo.tags
    semver_tags = [tag.name for tag in all_tags if re.match(r'^v\d+\.\d+\.\d+$', tag.name)]
    latest_semver_tag = semver_tags[-1] if semver_tags else 'v0.0.0'
    set_env("LATEST_RELEASE_TAG", latest_semver_tag)
    return latest_semver_tag


def check_calculated_version(labels, toml_file, latest_release_tag):
    print("Checking calculated version from semantic release")
    rel_labels = {l for l in labels if l.startswith("release-")}
    if len(rel_labels) == 0:
        rel_labels.add("release-auto")

    release_label_map = {
        "release-skip": "",
        "release-auto": "",
        "release-patch": "--patch",
        "release-minor": "--minor",
        "release-major": "--major",
    }

    valid_labels = set(release_label_map.keys())
    release_labels = valid_labels.intersection(rel_labels)
    if len(release_labels) != 1:
        set_output("issue_str", "Multiple release labels found, please only use one release label")
        return

    release_label = list(rel_labels)[0]
    forced_release = release_label_map[release_label]

    if release_label == "release-skip":
        return

    command = ["semantic-release", "--config", toml_file, "--noop", "version"]
    if forced_release:
        command.append(forced_release)

    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.stderr:
        print(result.stderr)

    output = result.stdout.strip()
    print(f'Captured Version Name: "{output}"')

    new_version = f"v{output}"

    if latest_release_tag != new_version:
        set_output("new_version", output)
        set_output("release_override_found", forced_release)
        set_output("is_release", "true")
