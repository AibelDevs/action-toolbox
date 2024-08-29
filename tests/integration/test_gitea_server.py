import os

import requests

from action_tool.git_helper import GitHelper
from action_tool.git_remote_adapter import get_git_remote_adapter, GiteaRemoteRepo
from action_tool.gitea_tools import create_gitea_pull_request, create_gitea_label, \
    create_gitea_release_labels_if_not_exists, add_secret_to_gitea, merge_gitea_pr


def test_gitea_setup(gitea_container, gitea_url, create_dummy_user, create_fake_repository):
    assert gitea_container.status == "created"
    assert requests.get(gitea_url).status_code == 200
    print("Gitea setup and tests passed successfully.")


def test_pr_review(gitea_container, gitea_url, create_dummy_user, create_fake_repository, created_token,
                   act_runner_container, mock_proj_a, action_toolbox_proj, ssh_deploy_key):
    git_local_helper = GitHelper(mock_proj_a)
    git_local_helper.create_branch("feat/new-stuff", push=True)

    # Add a new file and commit+push
    with open(mock_proj_a / "src/packages/a_sample_project/new_file.txt", "w") as f:
        f.write("This is a new file.")

    git_local_helper.commit("I'm adding a new file.")
    git_local_helper.push()

    username = create_dummy_user["username"]
    repo_name = create_fake_repository["name"]

    add_secret_to_gitea(
        gitea_url=gitea_url,
        token=created_token,
        repo_owner=create_dummy_user["username"],
        repo_name=create_fake_repository["name"],
        secret_name="SOURCE_KEY",
        secret_value=ssh_deploy_key["encoded_private_key"]
    )

    create_gitea_release_labels_if_not_exists(gitea_url, username, repo_name, created_token)
    create_gitea_label("a-sample-project", gitea_url, username, repo_name, created_token)

    # make a PR
    create_gitea_pull_request(gitea_url, username, repo_name, created_token, "feat: new-stuff", "feat/new-stuff",
                              "main")

    # Using a while loop and check if either a PR comment is made by bot or all checks are complete
    ...

    # get the PR review comment and evaluate its contents
    # Todo: add tests to check that the PR bot has created the correct message
    print("Gitea PR review passed successfully.")


def test_on_pr_merge(gitea_container, gitea_url, create_dummy_user, create_fake_repository, created_token,
                     act_runner_container, mock_proj_a, action_toolbox_proj, ssh_deploy_key):
    git_local_helper = GitHelper(mock_proj_a)
    git_local_helper.create_branch("feat/new-stuff", push=True)

    # Add a new file and commit+push
    with open(mock_proj_a / "src/packages/a_sample_project/new_file.txt", "w") as f:
        f.write("This is a new file.")

    git_local_helper.commit("I'm adding a new file.")
    git_local_helper.push()

    username = create_dummy_user["username"]
    repo_name = create_fake_repository["name"]

    add_secret_to_gitea(
        gitea_url=gitea_url,
        token=created_token,
        repo_owner=create_dummy_user["username"],
        repo_name=create_fake_repository["name"],
        secret_name="SOURCE_KEY",
        secret_value=ssh_deploy_key["encoded_private_key"]
    )

    create_gitea_release_labels_if_not_exists(gitea_url, username, repo_name, created_token)

    create_gitea_label("a-sample-project", gitea_url, username, repo_name, created_token)

    # make a PR
    create_gitea_pull_request(gitea_url, username, repo_name, created_token, "feat: new-stuff", "feat/new-stuff",
                              "main")
    os.environ["PR_NUMBER"] = "1"

    git_remote_adapter = GiteaRemoteRepo(token=created_token, url=gitea_url, repo_owner=username, repo_name=repo_name)
    git_remote_adapter.set_pr_label('release-minor')
    git_remote_adapter.set_pr_label('a-sample-project')

    git_remote_adapter.merge_pr()

    # get the PR review comment and evaluate its contents
    # Todo: add tests to check that the PR bot has created the correct message
    print("Gitea on PR merge step passed successfully.")
