from action_tool.load_config import load_config
from dotenv import load_dotenv

from action_tool.utils import set_output

load_dotenv()

import github.Repository
from github import Github
from github.GithubException import GithubException
import os


def is_in_github_action():
    return os.getenv('GITHUB_ACTIONS') == "true"


def get_repo() -> github.Repository.Repository:
    if is_in_github_action():
        # In GitHub Actions, these environment variables should already be set.
        token = os.getenv('GITHUB_TOKEN')
        repo_full_name = os.getenv('GITHUB_REPOSITORY')  # This is in the form 'owner/repo'
    else:
        # Local environment or other CI environments
        token = os.getenv('GITHUB_TOKEN')
        owner = os.getenv('GITHUB_REPOSITORY_OWNER')
        repo_name = os.getenv('GITHUB_REPOSITORY_NAME')
        repo_full_name = f"{owner}/{repo_name}"

    if not token or not repo_full_name:
        raise ValueError("GitHub token or repository information is missing!")

    # Authenticate to GitHub
    g = Github(token)
    repo = g.get_repo(repo_full_name)

    return repo


def rainbow_colors_generator():
    """Once exhausted, this generator will start from the beginning."""
    rainbow_colors = [
        "FF0000",  # Red
        "FF7F00",  # Orange
        "FFFF00",  # Yellow
        "00FF00",  # Green
        "0000FF",  # Blue
        "4B0082",  # Indigo
        "9400D3",  # Violet
    ]
    while True:
        for color in rainbow_colors:
            yield color


def set_labels_if_not_already_created(label_names: list[str]):
    # Define your labels with colors. Use rainbow colors for now.
    repo = get_repo()
    labels_with_colors = {}
    for label_name in label_names:
        color = rainbow_colors_generator()
        labels_with_colors[label_name] = next(color)

    existing_labels = get_all_labels_with_colors(repo)

    for label_name, color in labels_with_colors.items():
        if label_name not in existing_labels or existing_labels[label_name] != color:
            create_or_update_label(repo, label_name, color)


# Function to get all labels in the repository with their colors
def get_all_labels_with_colors(repo):
    return {label.name: label.color for label in repo.get_labels()}


# Function to create or update a label in the repository
def create_or_update_label(repo, label_name, color):
    try:
        label = repo.get_label(label_name)
        if label.color != color:
            label.edit(name=label_name, color=color)
            print(f"Updated label: {label_name} to color: {color}")
    except GithubException as e:
        if e.status == 404:
            repo.create_label(name=label_name, color=color)
            print(f"Created label: {label_name} with color: {color}")
        else:
            raise e


def check_silence_bot_label(pull_request):
    """
    Check if the label 'silence-bot' is added to the pull request.

    :param pull_request: Pull request object from PyGithub.
    :return: Boolean indicating if 'silence-bot' label is present.
    """
    labels = [label.name for label in pull_request.get_labels()]
    return 'silence-bot' in labels


def delete_previous_bot_comment(repo, pull_request):
    """
    Delete the last comment made by the bot on the pull request.

    :param repo: Repository object from PyGithub.
    :param pull_request: Pull request object from PyGithub.
    """
    comments = pull_request.get_issue_comments()
    bot_comment = None

    for comment in reversed(list(comments)):
        if comment.user.login == 'github-actions[bot]':
            bot_comment = comment
            break

    if bot_comment:
        bot_comment.delete()


def comment_on_pr(repo, pull_request, body):
    """
    Comment on the pull request.

    :param repo: Repository object from PyGithub.
    :param pull_request: Pull request object from PyGithub.
    :param body: The comment body as a string.
    """
    pull_request.create_issue_comment(body)


def finalize_pr_review(body: str):
    repo = get_repo()
    pull_request = repo.get_pull(int(os.getenv('PR_NUMBER')))

    silence_bot = check_silence_bot_label(pull_request)
    set_output('silence_bot', str(silence_bot).lower())

    if silence_bot:
        print("Silence bot label found, skipping comment.")
    else:
        delete_previous_bot_comment(repo, pull_request)

        comment_on_pr(repo, pull_request, body)
