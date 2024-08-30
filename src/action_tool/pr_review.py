from action_tool.config import logger
from action_tool.git_remote_adapter import get_git_remote_adapter, PRNoReleaseLabels, PRMultipleReleaseLabels, \
    PRNoMonoRepoLabel, PRTooManyMonoRepoLabel, GitRemoteRepo
from action_tool.pr_version_calc import calculate_version_w_semantic_release, FailedSemantics
from action_tool.utils import deserialize_str, set_output, get_env


def check_pr_title(title: str):
    valid_pr_title = ['fix: ', 'fix!: ', 'feat: ', 'feat!: ', 'chore: ']
    return title.startswith(tuple(valid_pr_title))


def review_pr() -> GitRemoteRepo:
    git_remote = get_git_remote_adapter()
    git_remote.add_missing_repo_labels()

    pr_is_ok = True
    header = "\n# PR Review:\n\n"
    body_review_str = ""

    # Check presence of SOURCE_KEY
    source_key_exists = get_env('HAS_SOURCE_KEY') == "true"
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
    try:
        git_remote.get_pr_release_label()
        body_review_str += f"\n * ✅ Release label is OK"
    except PRNoReleaseLabels:
        logger.info("No release label assigned. Applying default PR label 'release-skip'")
        rel_label = 'release-skip'
        git_remote.set_pr_label(rel_label)
        body_review_str += "\n * ✅ Release label is OK"
    except PRMultipleReleaseLabels as e:
        pr_is_ok = False
        body_review_str += f"\n * {e}"

    # Check if monorepo
    if git_remote.config.mono_repo_enabled:
        try:
            mono_project = git_remote.get_current_pr_mono_repo()
            body_review_str += f"\n * ✅ Monorepo label is OK"
            mono_config_file = mono_project.config_file
            set_output("MONO_CONFIG_FILE", mono_config_file.as_posix())

        except PRNoMonoRepoLabel as e:
            body_review_str += f"\n * {e}"
            pr_is_ok = False
        except PRTooManyMonoRepoLabel as e:
            body_review_str += f"\n * {e}"
            pr_is_ok = False

    # Calculate semantic version
    try:
        next_version = git_remote.calculate_next_version()
        body_review_str += f"\n * ✅ Next version is '{next_version}'"
    except FailedSemantics as e:
        body_review_str += f"\n * ❌ Unable to calculate version based on \n\n```{e}```"
        pr_is_ok = False

    if pr_is_ok:
        header += "I found no pr-related issues.\n"
    else:
        header += "I found some pr-related issues:\n\n"

    pr_review_str = header + body_review_str

    set_output('pr_review_ok', str(pr_is_ok).lower())
    set_output('pr_review_str', pr_review_str, True)

    return git_remote


def perform_pr_final_review():
    all_checks = []
    review_str = ''

    # PR
    review_str += deserialize_str(get_env('PR_REVIEW_STR', ''))
    all_checks.append(get_env('PR_REVIEW_OK', 'false') == 'true')

    # Python
    if get_env('PYTHON_ENABLED', 'false') == 'true':
        review_str += deserialize_str(get_env('PYTHON_REVIEW_STR', ''))
        all_checks.append(get_env('PYTHON_REVIEW_OK', 'false') == 'true')

    # Docker
    if get_env('DOCKER_ENABLED', 'false') == 'true':
        review_str += deserialize_str(get_env('DOCKER_REVIEW_STR', ''))
        all_checks.append(get_env('DOCKER_REVIEW_OK', 'false') == 'true')

    # GitOps
    if get_env('GITOPS_ENABLED', 'false') == 'true':
        review_str += deserialize_str(get_env('GITOPS_REVIEW_STR', ''))
        all_checks.append(get_env('GITOPS_REVIEW_OK', 'false') == 'true')

    # check if all_checks are true
    if all(all_checks):
        header = "👋 Hi there! I have checked your PR and found no issues. Thanks for your contribution!\n"
        set_output('review_ok', 'true')
    else:
        header = "👋 Hi there! I have checked your PR and found the following:\n\n"
        set_output('review_ok', 'false')

    if get_env('EXTRA_REVIEW_STR', ''):
        review_str += deserialize_str(get_env('EXTRA_REVIEW_STR', ''))

    body = header + review_str

    # Set the output
    set_output('body', body, True)

    git_remote_adapter = get_git_remote_adapter()
    git_remote_adapter.add_comment_on_pr(body)
    git_remote_adapter.clear_all_previous_pr_bot_comments()
