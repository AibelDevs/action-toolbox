import os

from action_tool.pr_review import perform_pr_final_review, review_pr
from action_tool.utils import get_output


def test_pr_review(tmp_dir, proj_mono_1):

    # Set pre-requisities

    os.environ["PR_REVIEW_OK"] = "true"
    os.environ["PR_TITLE"] = "fix: something"
    os.environ["PR_LABELS"] = '["release-auto"]'
    os.environ["SECRETS"] = '["SOURCE_KEY"]'

    review_pr()

    output1 = get_output()
    os.environ["PR_REVIEW_STR"] = output1.get('pr_review_str')

    perform_pr_final_review()

    output = get_output()

    body = output.get('body')
    assert body