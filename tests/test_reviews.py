import os

from action_tool.pr_review import perform_pr_final_review, review_pr
from action_tool.utils import get_output, set_env


def test_pr_review(mock_local_proj_a):

    # Set PR environment variables

    os.environ["PR_REVIEW_OK"] = "true"
    os.environ["PR_TITLE"] = "fix: something"
    os.environ["PR_LABELS"] = '["release-auto","a-sample-project"]'
    os.environ["HAS_SOURCE_KEY"] = "true"
    os.environ["CONFIG_TOML_FILE"] = (mock_local_proj_a / "action_config.toml").as_posix()
    os.environ["SRC_MAIN_BRANCH_DIR"] = mock_local_proj_a.as_posix()

    review_pr()

    output1 = get_output()

    set_env("PR_REVIEW_STR", output1.get('pr_review_str'))

    perform_pr_final_review()

    output = get_output()

    body = output.get('body')
    assert body