import os

from action_tool.github_tools import finalize_pr_review
from action_tool.git_remote_adapter import is_in_github_action
from action_tool.utils import deserialize_str, set_output


def review_pr():
    set_output('pr_review_ok', 'true')
    set_output('pr_review_str', 'A pr review has been performed')


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

    if is_in_github_action():
        finalize_pr_review(body)
