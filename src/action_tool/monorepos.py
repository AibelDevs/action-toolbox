import json
import os

from action_tool.config import logger
from action_tool.github_tools import set_labels_if_not_already_created
from action_tool.load_config import load_config
from action_tool.git_remote_adapter import is_in_github_action
from action_tool.utils import set_output


def check_monorepo_labels():
    action_context = load_config()
    if action_context.mono_repo_enabled is False:
        logger.info("Not a monorepo, skipping...")
        return

    labels = json.loads(os.environ['LABELS'])
    if labels is None:
        raise Exception("LABELS environment variable is not set")

    if is_in_github_action():
        set_labels_if_not_already_created(labels)

    mono_dict = {m.name: m for m in action_context.mono_repo_project}
    mono_labels = set(mono_dict.keys())

    overlapped_labels = mono_labels.intersection(labels)

    if len(overlapped_labels) == 0:
        raise Exception(f"You must add at least 1 label of the valid: {overlapped_labels}")
    elif len(overlapped_labels) > 1:
        raise Exception(f"Multiple LABELS found starting with {overlapped_labels}")

    mono_config_file = mono_dict.get(list(overlapped_labels)[0]).config_file

    set_output("MONO_CONFIG_FILE", mono_config_file.as_posix())
