from action_tool.load_config import load_config
from dotenv import load_dotenv

load_dotenv()

from github import Github
from github.GithubException import GithubException
import os

# GitHub repository information
token = os.getenv('GITHUB_TOKEN')
owner = os.getenv('GITHUB_REPOSITORY_OWNER')
repo_name = os.getenv('GITHUB_REPOSITORY')


def get_labels():
    load_config()
    # Define your labels with associated colors
    labels_with_colors = {
        'ai-gene-standalone': 'ffff00',  # Yellow
    }


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


# Main logic
def run():
    # Authenticate to GitHub
    g = Github(token)
    repo = g.get_repo(f"{owner}/{repo_name}")

    existing_labels = get_all_labels_with_colors(repo)

    for label_name, color in labels_with_colors.items():
        if label_name not in existing_labels or existing_labels[label_name] != color:
            create_or_update_label(repo, label_name, color)


if __name__ == "__main__":
    run()
