from action_tool.git_helper import GitHelper
from action_tool.load_config import load_config
from action_tool.pr_version_calc import calculate_version_w_semantic_release, run_semantic_release


def append_a_new_line_to_file(mock_proj_a):
    # Add a new file and commit+push
    with open(mock_proj_a / "src/packages/a_sample_project/new_file.txt", "a") as f:
        f.write("This is a new line.")


def test_semantic_versions_a(mock_local_proj_a):
    git_local = GitHelper(mock_local_proj_a)
    config_file = mock_local_proj_a / "action_config.toml"
    changelog_file = mock_local_proj_a / "src/packages/a_sample_project/CHANGELOG.md"

    config_toml = load_config(config_file)
    if config_toml.mono_repo_enabled:
        config_file = mock_local_proj_a / config_toml.mono_repo_project[0].config_file

    assert not changelog_file.exists()

    rel_label = "release-auto"
    pr_title = "fix: something"
    next_version = calculate_version_w_semantic_release(rel_label, pr_title, config_file, mock_local_proj_a)

    assert next_version == "0.1.0"
    actual_version = run_semantic_release(config_file, pr_title, git_dir=mock_local_proj_a, vcs_release=False)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.0"
    assert changelog_file.exists()

    # Add a fix
    append_a_new_line_to_file(mock_local_proj_a)
    git_local.commit("fix: something")
    git_local.push()

    next_version = calculate_version_w_semantic_release(rel_label, pr_title, config_file, mock_local_proj_a)

    assert next_version == "0.1.1"
    actual_version = run_semantic_release(config_file, pr_title, git_dir=mock_local_proj_a, vcs_release=False)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.1"

    # Add a feature
    append_a_new_line_to_file(mock_local_proj_a)
    git_local.commit("feat: Hey, a new feature!")
    git_local.push()

    next_version = calculate_version_w_semantic_release(rel_label, pr_title, config_file, mock_local_proj_a)

    assert next_version == "0.2.0"
    actual_version = run_semantic_release(config_file, pr_title, git_dir=mock_local_proj_a, vcs_release=False)
    assert actual_version == next_version

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.2.0"


def test_semantic_versions_branch(mock_local_proj_a_branch):
    print(f'Working on branch: {mock_local_proj_a_branch}')
    mock_local_branch_dir, mock_local_main_dir = mock_local_proj_a_branch

    git_local_main = GitHelper(mock_local_main_dir)
    git_local_branch = GitHelper(mock_local_branch_dir)

    config_file = mock_local_branch_dir / "action_config.toml"
    changelog_file = mock_local_branch_dir / "src/packages/a_sample_project/CHANGELOG.md"

    config_toml = load_config(config_file)
    if config_toml.mono_repo_enabled:
        config_file = mock_local_branch_dir / config_toml.mono_repo_project[0].config_file

    assert not changelog_file.exists()

    rel_label = "release-auto"
    pr_title = "feat: new-stuff"
    calculated_next_version = calculate_version_w_semantic_release(rel_label, pr_title, config_file,
                                                                   mock_local_branch_dir)

    assert calculated_next_version == "0.1.0"
    actual_next_version = run_semantic_release(config_file, pr_title, git_dir=mock_local_branch_dir, vcs_release=True)
    assert calculated_next_version == actual_next_version

    # Sync local main with remote main
    git_local_main.pull()

    # Create a new branch from main
    git_local_branch.create_branch("feat/more-new-stuff", push=True,
                                   from_branch=git_local_main.git_repo.active_branch.name)

    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.0"
    assert changelog_file.exists()

    append_a_new_line_to_file(mock_local_branch_dir)
    pr_title = "fix: more-stuff"
    git_local_branch.commit(pr_title)
    # git_local_branch.push()

    calculated_next_version = calculate_version_w_semantic_release(rel_label, pr_title, config_file,
                                                                   mock_local_branch_dir)

    assert calculated_next_version == "0.1.1"
    actual_next_version = run_semantic_release(config_file, pr_title, git_dir=mock_local_branch_dir, vcs_release=True)
    assert calculated_next_version == actual_next_version

    # Create a new branch from main
    git_local_branch.create_branch("feat/and-more-stuff", push=True,
                                   from_branch=git_local_main.git_repo.active_branch.name)
    updated_config_toml = load_config(config_file)
    assert updated_config_toml.config_toml_data["tool"]["action"]["version"] == "0.1.1"
