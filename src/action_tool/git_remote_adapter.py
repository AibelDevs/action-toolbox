import abc
import os

from github import Github

from action_tool.gitea_tools import get_gitea_labels


def is_in_github_action():
    return os.getenv('GITHUB_ACTIONS') == "true"


def is_in_gitea_action():
    return os.getenv('GITEA_INSTANCE_URL') is not None


class GitRemoteRepo(abc.ABC):
    def __init__(self):
        ...

    @abc.abstractmethod
    def get_labels(self):
        pass


class GithubRemoteRepo(GitRemoteRepo):
    def __init__(self):
        super().__init__()
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_full_name = os.getenv('GITHUB_REPOSITORY')  # This is in the form 'owner/repo'
        # Authenticate to GitHub
        g = Github(self.token)
        self.repo = g.get_repo(self.repo_full_name)

    def get_labels(self):
        return {label.name: label.color for label in self.repo.get_labels()}


class GiteaRemoteRepo(GitRemoteRepo):
    def __init__(self, url, owner, repo, token):
        super().__init__()
        self.url = url
        self.owner = owner
        self.repo = repo
        self.token = token

    def get_labels(self):
        return get_gitea_labels(self.url, self.owner, self.repo, self.token)


def get_labels():
    if is_in_github_action():
        ...
    elif is_in_gitea_action():
        ...
    else:
        return os.getenv("LABELS")
