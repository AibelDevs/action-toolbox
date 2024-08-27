import os

from action_tool.pr_review import perform_pr_final_review
from action_tool.utils import get_output


def test_pr_review(tmp_dir, proj_mono_1):

    # Set pre-requisities

    os.environ["PR_REVIEW_OK"] = "true"

    perform_pr_final_review()

    output = get_output()

    body = output.get('body')
    assert body