import abc
import os

from github import Github

from action_tool.config import logger
from action_tool.gitea_tools import get_gitea_labels, comment_on_gitea_pr
from action_tool.github_tools import comment_on_pr, check_silence_bot_label
from action_tool.utils import set_output


class GitRemoteRepo(abc.ABC):
    def __init__(self):
        ...

    @abc.abstractmethod
    def get_labels(self):
        pass

    @abc.abstractmethod
    def comment_on_pr(self, comment_body, pr_index):
        pass


def is_in_github_action():
    actions = os.getenv('GITHUB_ACTIONS') == "true"
    git_remote_url = os.getenv('GITHUB_URL')
    logger.info(f"{git_remote_url=}")
    return actions and 'github' in git_remote_url


def is_in_gitea_action():
    actions = os.getenv('GITEA_ACTIONS') == "true"
    git_remote_url = os.getenv('GITHUB_URL')
    logger.info(f"{git_remote_url=}")
    return actions and 'github' not in git_remote_url


def get_git_remote_adapter() -> GitRemoteRepo:
    if is_in_github_action():
        logger.info("Is a Github Actions Runner")
        return GithubRemoteRepo()
    elif is_in_gitea_action():
        logger.info("Is a Gitea Actions Runner")
        return GiteaRemoteRepo()
    else:
        raise ValueError('Not a GitHub action')


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

    def comment_on_pr(self, comment_body, pr_index):
        pull_request = self.repo.get_pull(int(pr_index))
        silence_bot = check_silence_bot_label(pull_request)

        if silence_bot:
            print("Silence bot label found, skipping comment.")
            set_output('silence_bot', str(silence_bot).lower())
        else:
            comment_on_pr(self.repo, pull_request, comment_body)


class GiteaRemoteRepo(GitRemoteRepo):
    def __init__(self):
        super().__init__()
        self.token = os.getenv('GITHUB_TOKEN')
        repo_full_name = os.getenv('GITHUB_REPOSITORY')  # This is in the form 'owner/repo'
        owner, repo = repo_full_name.split('/')
        self.url = os.getenv('GITHUB_URL')
        logger.info(f"Using {owner}/{repo}")
        self.owner = owner
        self.repo = repo

    def get_labels(self):
        raw_labels = get_gitea_labels(self.url, self.owner, self.repo, self.token)
        labels = [lbl["name"] for lbl in raw_labels]
        return labels

    def comment_on_pr(self, comment_body, pr_index):
        comment_on_gitea_pr(comment_body, pr_index, self.url, self.owner, self.repo, self.token)
