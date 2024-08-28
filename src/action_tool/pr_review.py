import os

from action_tool.config import logger
from action_tool.git_remote_adapter import get_git_remote_adapter
from action_tool.utils import deserialize_str, set_output


def check_pr_title(title: str):
    valid_pr_title = ['fix: ', 'fix!: ', 'feat: ', 'feat!: ', 'chore: ']
    return title.startswith(tuple(valid_pr_title))


def review_pr():
    git_remote = get_git_remote_adapter()

    pr_is_ok = True
    header = "\n# PR Review:\n\n"
    body_review_str = ""

    # Check presence of SOURCE_KEY
    source_key_exists = git_remote.check_if_secret_exists('SOURCE_KEY')
    if not source_key_exists:
        body_review_str += "\n * ❌ You need to add SOURCE_KEY as a secret to your repo if you want semantic-release to work"
        pr_is_ok = False
    else:
        body_review_str += "\n * ✅ SOURCE_KEY is set as a secret"

    # Check PR title
    title = git_remote.get_pr_title()
    if check_pr_title(title):
        body_review_str += "\n * ✅ PR title is ok"
    else:
        body_review_str += "\n * ❌ You need to start PR title with fix: feat: fix!: feat!: chore:"

    # Check if a release label is set
    label_names = git_remote.get_pr_labels()
    valid_labels = set(git_remote.rel_labels_with_color.keys())
    intersect_labels = valid_labels.intersection(set(label_names))
    if len(intersect_labels) == 0:
        logger.info("No release label assigned. Applying default PR label 'release-skip'")
        git_remote.set_pr_label('release-skip')
        body_review_str += "\n * ✅ Release label is OK"
    elif len(intersect_labels) == 1:
        body_review_str += f"\n * ✅ Release label is OK"
    else:
        pr_is_ok = False
        body_review_str += f"\n * ❌ Multiple labels found {intersect_labels}. You can only assing 1 release label at the time."

    if pr_is_ok:
        header += "I found no pr-related issues.\n"
    else:
        header += "I found some pr-related issues:\n\n"

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
