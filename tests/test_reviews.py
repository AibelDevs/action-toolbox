from action_tool.pr_review import perform_pr_final_review


def test_pr_review(tmp_dir, proj_mono_1):

    perform_pr_final_review()