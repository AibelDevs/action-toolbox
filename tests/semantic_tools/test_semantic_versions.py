from action_tool.git_helper import GitHelper
from action_tool.load_config import load_config
from action_tool.pr_version_calc import calculate_version, run_semantic_release


def append_a_new_line_to_file(mock_proj_a):
    # Add a new file and commit+push
    with open(mock_proj_a / "src/packages/a_sample_project/new_file.txt", "a") as f:
        f.write("This is a new line.")

def test_semantic_versions_a(mock_local_proj_a):
    git_local = GitHelper(mock_local_proj_a)
    config_file = mock_local_proj_a / "action_config.toml"
    changelog_file = mock_local_proj_a / "CHANGELOG.md"

    config_toml = load_config(config_file)
    if config_toml.mono_repo_enabled:
        config_file = mock_local_proj_a / config_toml.mono_repo_project[0].config_file

    assert not changelog_file.exists()

    rel_label = "release-auto"
    next_version = calculate_version(rel_label, config_file, mock_local_proj_a)

    assert next_version == "v0.1.0"
    run_semantic_release(config_file, git_dir=mock_local_proj_a)

    assert changelog_file.exists()

    append_a_new_line_to_file(mock_local_proj_a)
    git_local.commit("fix: something")
    git_local.push()

    next_version = calculate_version(rel_label, config_file, mock_local_proj_a)

    assert next_version == "v0.1.1"
    print(next_version)