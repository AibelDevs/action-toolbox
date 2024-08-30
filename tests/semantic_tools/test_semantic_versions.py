import os

from action_tool.git_helper import GitHelper
from action_tool.git_remote_adapter import get_git_remote_adapter
from action_tool.load_config import load_config
from action_tool.pr_version_calc import calculate_version_w_semantic_release, run_semantic_release


def append_a_new_line_to_file(mock_proj_a):
    # Add a new file and commit+push
    with open(mock_proj_a / "src/packages/a_sample_project/new_file.txt", "a") as f:
        f.write("This is a new line.")


def test_semantic_versions_a(mock_local_proj_a_main):
    """Testing semantic versioning on main branch only"""
    git_local = GitHelper(mock_local_proj_a_main)

    changelog_file = mock_local_proj_a_main / "src/packages/a_sample_project/CHANGELOG.md"
    assert not changelog_file.exists()

    os.environ["PR_TITLE"] = "feat: something"
    os.environ["PR_LABELS"] = '["a-sample-project", "release-auto"]'

    git_adapter = get_git_remote_adapter()
    if git_adapter.config.mono_repo_enabled:
        config_file = git_adapter.get_current_pr_mono_repo().config_file
    else:
        config_file = git_adapter.config.config_file

    release_override = git_adapter.get_release_override()

    next_version = calculate_version_w_semantic_release(config_file, release_override, mock_local_proj_a_main)
    assert next_version == "0.1.0"

    actual_version = run_semantic_release(config_file, release_override, mock_local_proj_a_main)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.0"
    assert changelog_file.exists()

    # Add a fix
    append_a_new_line_to_file(mock_local_proj_a_main)
    git_local.commit("fix: something")
    git_local.push()

    os.environ["PR_TITLE"] = "fix: something"
    os.environ["PR_LABELS"] = '["a-sample-project", "release-auto"]'
    release_override = git_adapter.get_release_override()

    next_version = calculate_version_w_semantic_release(config_file, release_override, mock_local_proj_a_main)

    assert next_version == "0.1.1"
    actual_version = run_semantic_release(config_file, release_override, mock_local_proj_a_main)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.1"

    # Add a feature
    append_a_new_line_to_file(mock_local_proj_a_main)
    git_local.commit("feat: Hey, a new feature!")
    git_local.push()

    os.environ["PR_TITLE"] = "feat: something"
    os.environ["PR_LABELS"] = '["a-sample-project", "release-auto"]'
    release_override = git_adapter.get_release_override()

    next_version = calculate_version_w_semantic_release(config_file, release_override, mock_local_proj_a_main)

    assert next_version == "0.2.0"
    actual_version = run_semantic_release(config_file, release_override, mock_local_proj_a_main)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.2.0"


def test_semantic_versions_branch(mock_local_proj_a_branch):
    """A test for checking the synchronization between branches and main"""

    print(f'Working on branch: {mock_local_proj_a_branch}')
    mock_local_branch_dir, mock_local_main_dir = mock_local_proj_a_branch

    git_local_main = GitHelper(mock_local_main_dir)
    git_local_branch = GitHelper(mock_local_branch_dir)

    changelog_file = mock_local_branch_dir / "src/packages/a_sample_project/CHANGELOG.md"
    assert not changelog_file.exists()

    # Initial Commit with semantic versioning
    os.environ["PR_TITLE"] = "feat: something"
    os.environ["PR_LABELS"] = '["a-sample-project", "release-auto"]'

    git_adapter = get_git_remote_adapter()
    if git_adapter.config.mono_repo_enabled:
        main_config_file = git_adapter.get_current_pr_mono_repo().config_file
    else:
        main_config_file = git_adapter.config.config_file

    release_override = git_adapter.get_release_override()

    calculated_next_version = calculate_version_w_semantic_release(main_config_file, release_override, mock_local_main_dir)

    assert calculated_next_version == "0.1.0"
    actual_next_version = run_semantic_release(main_config_file, release_override, mock_local_main_dir)
    assert calculated_next_version == actual_next_version

    # Create a new branch from main where you fix something
    git_local_branch.create_branch("feat/more-new-stuff", push=True,
                                   from_branch=git_local_main.git_repo.active_branch.name)

    config_rel_path = main_config_file.relative_to(mock_local_main_dir)
    branch_config_file = mock_local_branch_dir / config_rel_path
    # You make sure that the previous generated semantic versioning data is updated in your branch
    updated_config_toml = load_config(branch_config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.0"
    assert changelog_file.exists()


    pr_title = "fix: something"
    append_a_new_line_to_file(mock_local_branch_dir)
    git_local_branch.commit(pr_title)
    git_local_branch.push()

    os.environ["PR_TITLE"] = pr_title
    os.environ["PR_LABELS"] = '["a-sample-project", "release-auto"]'
    # Now you make a PR and merge the fix back into main
    git_local_main.pull(git_local_branch.git_repo.active_branch.name)

    release_override = git_adapter.get_release_override()

    calculated_next_version = calculate_version_w_semantic_release(main_config_file, release_override, mock_local_main_dir)

    assert calculated_next_version == "0.1.1"
    actual_next_version = run_semantic_release(main_config_file, release_override, mock_local_main_dir)
    assert calculated_next_version == actual_next_version

    # Create a new branch from main
    git_local_branch.create_branch("feat/and-more-stuff", push=True,
                                   from_branch=git_local_main.git_repo.active_branch.name)

    updated_config_toml = load_config(branch_config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.1"
