import os

from action_tool.config import logger
from action_tool.git_remote_adapter import get_git_remote_adapter, PRNoReleaseLabels, PRMultipleReleaseLabels
from action_tool.load_config import load_config
from action_tool.pr_version_calc import calculate_version_w_semantic_release
from action_tool.utils import deserialize_str, set_output


def check_pr_title(title: str):
    valid_pr_title = ['fix: ', 'fix!: ', 'feat: ', 'feat!: ', 'chore: ']
    return title.startswith(tuple(valid_pr_title))


def review_pr():
    git_remote = get_git_remote_adapter()
    git_remote.add_missing_repo_labels()

    pr_is_ok = True
    header = "\n# PR Review:\n\n"
    body_review_str = ""

    # Check presence of SOURCE_KEY
    source_key_exists = os.getenv('HAS_SOURCE_KEY') == "true"
    if not source_key_exists:
        body_review_str += "\n * ❌ You need to add SOURCE_KEY as a secret to your repo if you want semantic-release to work"
        pr_is_ok = False
    else:
        body_review_str += "\n * ✅ SOURCE_KEY is set as a secret"

    # Check PR title
    title = git_remote.get_pr_title()
    if check_pr_title(title):
        body_review_str += "\n * ✅ PR title is OK"
    else:
        body_review_str += "\n * ❌ You need to start PR title with fix: feat: fix!: feat!: chore:"

    # Check if a release label is set
    rel_label = None
    try:
        rel_label = git_remote.get_pr_release_label()
        body_review_str += f"\n * ✅ Release label is OK"
    except PRNoReleaseLabels:
        logger.info("No release label assigned. Applying default PR label 'release-skip'")
        rel_label = 'release-skip'
        git_remote.set_pr_label(rel_label)
        body_review_str += "\n * ✅ Release label is OK"
    except PRMultipleReleaseLabels as e:
        pr_is_ok = False
        body_review_str += f"\n * {e}"

    if pr_is_ok:
        header += "I found no pr-related issues.\n"
    else:
        header += "I found some pr-related issues:\n\n"

    config_toml = load_config()

    # Check if monorepo
    if config_toml.mono_repo_enabled:
        custom_labels = git_remote.get_custom_labels()
        mono_repos_dict = {x.name: x for x in config_toml.mono_repo_project}
        mono_repos_set = set(mono_repos_dict.keys())
        mono_proj_intersection = custom_labels.intersection(mono_repos_set)
        if len(mono_proj_intersection) == 0:
            body_review_str += f"\n * ❌ Monorepo label is not set. Please use one of the following labels: {mono_repos_set}"
            pr_is_ok = False
        elif len(mono_proj_intersection) > 1:
            body_review_str += f"\n * ❌ Multiple monorepo labels are set. Please use only one of the following labels: {mono_repos_set}"
            pr_is_ok = False
        else:
            body_review_str += f"\n * ✅ Monorepo label is OK"
            mono_project = mono_repos_dict[mono_proj_intersection.pop()]
            mono_config = load_config(mono_project.config_file)
            mono_config_file = mono_config.config_toml_file
            set_output("MONO_CONFIG_FILE", mono_config_file.as_posix())

            # Calculate semantic version
            if rel_label is not None:
                next_version = calculate_version_w_semantic_release(rel_label, title, mono_config_file, debug_mode=True)
                if next_version == "":
                    body_review_str += f"\n * ❌ Unable to calculate version based on config file {mono_config_file}"
                    pr_is_ok = False
                else:
                    body_review_str += f"\n * ✅ Next version is '{next_version}'"
    else:
        # Calculate semantic version
        if rel_label is not None:
            next_version = calculate_version_w_semantic_release(rel_label, title, config_toml.config_toml_file)
            if next_version == "":
                body_review_str += f"\n * ❌ Unable to calculate version based on config file"
                pr_is_ok = False
            body_review_str += f"\n * ✅ Next version is '{next_version}'"

    pr_review_str = header + body_review_str

    set_output('pr_review_ok', str(pr_is_ok).lower())
    set_output('pr_review_str', pr_review_str, True)

    return pr_is_ok, pr_review_str


def perform_pr_final_review():
    all_checks = []
    review_str = ''

    # PR
    review_str += deserialize_str(os.getenv('PR_REVIEW_STR', ''))
    all_checks.append(os.getenv('PR_REVIEW_OK', 'false') == 'true')

    # Python
    if os.getenv('PYTHON_ENABLED', 'false') == 'true':
        review_str += deserialize_str(os.getenv('PYTHON_REVIEW_STR', ''))
        all_checks.append(os.getenv('PYTHON_REVIEW_OK', 'false') == 'true')

    # Docker
    if os.getenv('DOCKER_ENABLED', 'false') == 'true':
        review_str += deserialize_str(os.getenv('DOCKER_REVIEW_STR', ''))
        all_checks.append(os.getenv('DOCKER_REVIEW_OK', 'false') == 'true')

    # GitOps
    if os.getenv('GITOPS_ENABLED', 'false') == 'true':
        review_str += deserialize_str(os.getenv('GITOPS_REVIEW_STR', ''))
        all_checks.append(os.getenv('GITOPS_REVIEW_OK', 'false') == 'true')

    # check if all_checks are true
    if all(all_checks):
        header = "👋 Hi there! I have checked your PR and found no issues. Thanks for your contribution!\n"
        set_output('review_ok', 'true')
    else:
        header = "👋 Hi there! I have checked your PR and found the following:\n\n"
        set_output('review_ok', 'false')

    if os.getenv('EXTRA_REVIEW_STR', ''):
        review_str += deserialize_str(os.getenv('EXTRA_REVIEW_STR', ''))

    body = header + review_str

    # Set the output
    set_output('body', body, True)

    git_remote_adapter = get_git_remote_adapter()
    git_remote_adapter.add_comment_on_pr(body)
    git_remote_adapter.clear_all_previous_pr_bot_comments()
