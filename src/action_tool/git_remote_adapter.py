import abc
import json
import os
import pathlib
from abc import abstractmethod
from typing import Literal

import requests
from github import Github

from action_tool.config import logger
from action_tool.gitea_tools import get_gitea_labels, comment_on_gitea_pr, create_gitea_label, merge_gitea_pr
from action_tool.github_tools import comment_on_pr, check_silence_bot_label, create_or_update_github_repo_label
from action_tool.load_config import load_config, MonoRepo
from action_tool.pr_version_calc import calculate_version_w_semantic_release, run_semantic_release
from action_tool.utils import set_output, set_env, get_env


class PRNoReleaseLabels(Exception):
    pass


class PRMultipleReleaseLabels(Exception):
    pass


class PRNoMonoRepoLabel(Exception):
    pass


class PRTooManyMonoRepoLabel(Exception):
    pass


class GitRemoteRepo(abc.ABC):
    release_label_map = {
        "release-skip": None,
        "release-auto": None,
        "release-patch": "--patch",
        "release-minor": "--minor",
        "release-major": "--major",
    }
    rel_labels_with_color = {
        'release-skip': 'b3b3b3',  # Gray
        'release-auto': 'ffff00',  # Yellow
        'release-patch': '00ff00',  # Green
        'release-minor': '0000ff',  # Blue
        'release-major': 'ff0000',  # Red

    }
    bot_labels = {
        'silence-bot': '000000'  # Black
    }

    def __init__(self, config_toml_file=None):
        self.config = load_config(config_file=config_toml_file)

    def get_pr_release_label(self):
        rel_labels = set(self.rel_labels_with_color.keys())
        pr_labels = self.get_pr_labels()
        intersection = rel_labels.intersection(set(pr_labels))
        if len(intersection) == 0:
            raise PRNoReleaseLabels(f"Unable to find release labels: {pr_labels=}, {rel_labels=}")
        elif len(intersection) > 1:
            raise PRMultipleReleaseLabels(
                f"❌ Multiple labels found {intersection}. You can only assing 1 release label at the time.")
        rel_label = list(intersection)[0]
        return rel_label

    def get_custom_pr_labels(self) -> set[str]:
        rel_labels = set(list(self.rel_labels_with_color.keys()) + list(self.bot_labels.keys()))
        pr_labels = set(self.get_pr_labels())
        difference = pr_labels - rel_labels

        return difference

    def get_current_pr_mono_repo(self) -> MonoRepo | None:
        if self.config.mono_repo_enabled:
            release_mono_label = get_env("RELEASE_MONO_LABEL")
            if release_mono_label is not None:
                return release_mono_label

            custom_labels = self.get_custom_pr_labels()
            md = {m.name: m for m in self.config.mono_repo_project}
            md_set = set(md.keys())
            intersect = md_set.intersection(custom_labels)
            if len(intersect) == 0:
                raise PRNoMonoRepoLabel(
                    f"❌ Monorepo label is not set. Please use one of the following labels: {md_set}")
            elif len(intersect) > 1:
                raise PRTooManyMonoRepoLabel(
                    f"❌ Too many monorepo labels are set. Please use only 1 of the following labels: {md_set}")
            return md.get(intersect.pop())

        return None

    def get_release_override(self) -> None | Literal["--patch", "--minor", "--major"]:
        rel_label = self.get_pr_release_label()
        if rel_label == 'release-skip':
            return None

        pr_title = self.get_pr_title()
        if "!:" in pr_title:
            return "--major"

        if self.config.mono_repo_enabled:
            mono_repo = self.get_current_pr_mono_repo()
            raw_config = mono_repo.raw_config
        else:
            raw_config = self.config.raw_config

        allowed_tags = set(raw_config.commit_parser_options.get("allowed_tags"))
        minor_tags = raw_config.commit_parser_options.get("minor_tags")
        patch_tags = raw_config.commit_parser_options.get("patch_tags")

        non_version_tags = allowed_tags - set(minor_tags) - set(patch_tags)

        for minor_tag in minor_tags:
            if pr_title.startswith(minor_tag):
                return "--minor"

        for patch_tag in patch_tags:
            if pr_title.startswith(patch_tag):
                return "--patch"

        for non_version_tag in non_version_tags:
            if pr_title.startswith(non_version_tag):
                return None

        logger.error(f"An illegal PR title detected: '{pr_title}'. It must start with one of '{allowed_tags}'")
        return None

    def should_release(self) -> bool:
        rel_label = self.get_pr_release_label()
        if rel_label == 'release-skip':
            return False

        if self.get_release_override() is None:
            return False

        return True

    def prepare_release(self):
        if self.should_release():
            set_output("should_make_release", "true")
            set_output("release_override", self.get_release_override())
            toml_config = load_config()
            if toml_config.mono_repo_enabled:
                mono_repo = self.get_current_pr_mono_repo()
                set_env("CONFIG_TOML_FILE", mono_repo.config_file.as_posix())
                set_output("release_mono_label", mono_repo.name)
        else:
            set_output("should_make_release", "false")

    def get_config_and_gir_dir(self):
        if self.config.mono_repo_enabled:
            mono_repo = self.get_current_pr_mono_repo()
            config_file = mono_repo.config_file
        else:
            config_file = self.config.config_toml_file

        git_dir = pathlib.Path(os.getcwd())
        action_main_src = get_env("SRC_MAIN_BRANCH_DIR")
        if action_main_src is not None:
            logger.info("Will use main branch for calculating next version")
            action_main_src = pathlib.Path(action_main_src).resolve().absolute()
            if not config_file.relative_to(action_main_src):
                toml_rel = config_file.relative_to(git_dir)
                config_file = git_dir / toml_rel
            git_dir = action_main_src

        return config_file, git_dir

    def calculate_next_version(self):
        config_file, git_dir = self.get_config_and_gir_dir()
        return calculate_version_w_semantic_release(config_file, self.get_release_override(), git_dir)

    def make_new_release(self):
        config_file, git_dir = self.get_config_and_gir_dir()
        release_override = get_env("RELEASE_OVERRIDE", self.get_release_override())
        return run_semantic_release(config_file, release_override, git_dir)

    @abc.abstractmethod
    def get_pr_number(self):
        pass

    @abc.abstractmethod
    def get_repo_labels(self):
        pass

    @abc.abstractmethod
    def get_pr_labels(self):
        pass

    @abc.abstractmethod
    def add_comment_on_pr(self, comment_body):
        pass

    @abc.abstractmethod
    def check_if_secret_exists(self, secret: str):
        pass

    @abstractmethod
    def get_pr_title(self):
        pass

    @abstractmethod
    def add_missing_repo_labels(self):
        pass

    @abstractmethod
    def set_pr_label(self, lbl_name: str):
        pass

    @abstractmethod
    def clear_all_previous_pr_bot_comments(self):
        pass

    @abstractmethod
    def auto_merge_pr(self, wait_for_checks=True):
        pass


class GithubRemoteRepo(GitRemoteRepo):
    def __init__(self):
        super().__init__()
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_full_name = os.getenv('GITHUB_REPOSITORY')  # This is in the form 'owner/repo'
        # Authenticate to GitHub
        g = Github(self.token)
        self.repo = g.get_repo(self.repo_full_name)
        self.bot_username = "github-actions[bot]"
        self.pull_request = None
        try:
            pr_number = self.get_pr_number()
            self.pull_request = self.repo.get_pull(int(pr_number))
        except BaseException as e:
            logger.warning(e)

    def get_pr_number(self) -> int:
        pr_number = os.getenv('PR_NUMBER')
        if pr_number is None:
            raise ValueError("PR number is not found. Please set the PR_NUMBER environment variable.")
        return int(pr_number)

    def get_repo_labels(self):
        return {label.name: label.color for label in self.repo.get_labels()}

    def get_pr_labels(self):
        self.get_pr_number()
        try:
            labels = [label.name for label in self.pull_request.get_labels()]
            return labels
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def add_comment_on_pr(self, comment_body):
        self.get_pr_number()

        silence_bot = check_silence_bot_label(self.pull_request)

        if silence_bot:
            print("Silence bot label found, skipping comment.")
            set_output('silence_bot', str(silence_bot).lower())
        else:
            comment_on_pr(self.repo, self.pull_request, comment_body)

    def check_if_secret_exists(self, secret: str) -> bool:
        try:
            secrets = self.repo.get_secrets()
            return secret in [s.name for s in secrets]
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_pr_title(self):
        self.get_pr_number()
        return self.pull_request.title

    def add_missing_repo_labels(self):
        for rel_lbl, color in self.rel_labels_with_color.items():
            create_or_update_github_repo_label(self.repo, rel_lbl, color)

        for rel_lbl, color in self.bot_labels.items():
            create_or_update_github_repo_label(self.repo, rel_lbl, color)

    def set_pr_label(self, lbl_name: str):
        pr_number = self.get_pr_number()
        try:
            pr = self.repo.get_pull(int(pr_number))
            pr.add_to_labels(lbl_name)
            print(f"Label '{lbl_name}' added to PR #{pr_number}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def clear_all_previous_pr_bot_comments(self):
        try:
            pr = self.repo.get_pull(int(self.get_pr_number()))
            comments = pr.get_issue_comments()

            bot_comments = [comment for comment in comments if comment.user.login == self.bot_username]

            if len(bot_comments) > 1:
                for comment in bot_comments[:-1]:  # Keep only the last comment
                    comment.delete()
                    print(f"Deleted comment: {comment.id}")

            print("Cleared all but the last bot comment.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def auto_merge_pr(self, wait_for_checks=True):
        pr_number = self.get_pr_number()
        try:
            pr = self.repo.get_pull(pr_number)
            if pr.is_merged():
                print(f"PR #{pr_number} is already merged.")
                return
            pr.merge()
            print(f"PR #{pr_number} has been merged successfully.")
        except Exception as e:
            print(f"An error occurred while merging PR #{pr_number}: {e}")


class GiteaRemoteRepo(GitRemoteRepo):
    def __init__(self, token=None, url=None, repo_owner=None, repo_name=None):
        super().__init__()
        self.token = os.getenv('GITHUB_TOKEN', token)
        self.url = os.getenv('GITHUB_URL', url)
        self.bot_username = "gitea-actions[bot]"

        owner = None
        repo = None
        repo_full_name = os.getenv('GITHUB_REPOSITORY')  # This is in the form 'owner/repo'
        if repo_full_name is not None:
            try:
                owner, repo = repo_full_name.split('/')
                logger.info(f"Using {owner}/{repo}")
            except ValueError as e:
                logger.error(f"Failed to load GITHUB_REPOSITORY={repo_full_name}: {e}")

        self.owner = owner if repo_owner is None else repo_owner
        self.repo = repo if repo_name is None else repo_name

        try:
            self.get_pr_number()
        except ValueError as e:
            logger.warning(e)

    def get_pr_number(self) -> str:
        pr_number = os.getenv('PR_NUMBER')
        if pr_number is None:
            raise ValueError("PR number is not found. Please set the PR_NUMBER environment variable.")
        return pr_number

    def get_repo_labels(self):
        raw_labels = get_gitea_labels(self.url, self.owner, self.repo, self.token)
        labels = [lbl["name"] for lbl in raw_labels]
        return labels

    def get_pr_labels(self) -> list[str]:
        try:
            pr = self._self_get_pr()
        except requests.exceptions.RequestException as e:
            return []

        return [x['name'] for x in pr.get('labels', [])]

    def add_comment_on_pr(self, comment_body):
        comment_on_gitea_pr(comment_body, self.get_pr_number(), self.url, self.owner, self.repo, self.token)

    def check_if_secret_exists(self, secret: str) -> bool:
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        url = f"{self.url}/api/v1/repos/{self.owner}/{self.repo}/actions/secrets"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            secrets = response.json()
            return any(s['name'] == secret for s in secrets)
        else:
            raise ValueError(f"Failed to get secrets: {response.status_code} - {response.text}")

    def _self_get_pr(self):
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
        pr_number = self.get_pr_number()
        url = f"{self.url}/api/v1/repos/{self.owner}/{self.repo}/pulls/{pr_number}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pr = response.json()
        return pr

    def get_pr_title(self):
        try:
            pr = self._self_get_pr()
        except requests.exceptions.RequestException as e:
            return ""

        return pr.get("title", "")

    def add_missing_repo_labels(self):
        valid_labels = set(self.rel_labels_with_color.keys())
        existing_labels = set(self.get_repo_labels())
        missing_labels = valid_labels - existing_labels
        for label in missing_labels:
            lbl_with_color = self.rel_labels_with_color[label]
            create_gitea_label(label, self.url, self.owner, self.repo, self.token, color=lbl_with_color)

    def set_pr_label(self, lbl_name: str):
        pr_number = self.get_pr_number()

        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
        url = f"{self.url}/api/v1/repos/{self.owner}/{self.repo}/issues/{self.get_pr_number()}/labels"

        payload = {
            "labels": [lbl_name]
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"Label '{lbl_name}' added to PR #{pr_number}.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def clear_all_previous_pr_bot_comments(self):
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }
        url = f"{self.url}/api/v1/repos/{self.repo}/issues/{self.get_pr_number()}/comments"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            comments = response.json()

            bot_comments = [comment for comment in comments if comment['user']['login'] == self.bot_username]

            if len(bot_comments) > 1:
                for comment in bot_comments[:-1]:  # Keep only the last comment
                    delete_url = f"{self.url}/api/v1/repos/{self.repo}/issues/comments/{comment['id']}"
                    delete_response = requests.delete(delete_url, headers=headers)
                    delete_response.raise_for_status()
                    print(f"Deleted comment: {comment['id']}")

            print("Cleared all but the last bot comment.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def auto_merge_pr(self, wait_for_checks=True):
        merge_gitea_pr(self.get_pr_number(), self.url, self.owner, self.repo, self.token, wait_for_checks)


class LocalGitRemoteRepo(GitRemoteRepo):

    def __init__(self):
        super().__init__()

    def get_pr_number(self):
        return os.environ["PR_NUMBER"]

    def get_pr_labels(self):
        return json.loads(os.environ["PR_LABELS"])

    def get_repo_labels(self):
        return json.loads(os.environ["REPO_LABELS"])

    def add_comment_on_pr(self, comment_body):
        print(comment_body)

    def check_if_secret_exists(self, secret: str) -> bool:
        return json.loads(os.environ["SECRETS"])

    def get_pr_title(self):
        return os.environ["PR_TITLE"]

    def add_missing_repo_labels(self):
        ...

    def set_pr_label(self, lbl_name: str):
        ...

    def clear_all_previous_pr_bot_comments(self):
        pass

    def auto_merge_pr(self, wait_for_checks=True):
        pass


def is_in_github_action():
    actions = os.getenv('GITHUB_ACTIONS') == "true"
    git_remote_url = os.getenv('GITHUB_URL')
    if git_remote_url is None:
        return
    logger.info(f"{git_remote_url=}")
    return actions and 'github' in git_remote_url


def is_in_gitea_action():
    actions = os.getenv('GITEA_ACTIONS') == "true"
    git_remote_url = os.getenv('GITHUB_URL')
    if git_remote_url is None:
        return
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
        logger.info("running locally")
        return LocalGitRemoteRepo()
