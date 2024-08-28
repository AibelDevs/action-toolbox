import os

import pytest
from action_tool.pr_version_calc import add_commit_for_semantic_release_calculation, get_latest_release_tag, \
    check_calculated_version

@pytest.mark.skip(reason="Not working yet")
def test_version_calc():
    repo_path = ""
    add_commit_for_semantic_release_calculation(repo_path, os.getenv('PR_TITLE'))
    latest_tag = get_latest_release_tag(repo_path)
    check_calculated_version(["release-auto"], "path/to/config.toml", latest_tag)