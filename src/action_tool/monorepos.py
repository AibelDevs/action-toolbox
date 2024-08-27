import json
import os

from action_tool.load_config import load_config
from action_tool.utils import deserialize_str, get_output, set_output


def check_monorepo_labels():
    action_context = load_config()
    if action_context.mono_repo_enabled is False:
        raise Exception("MONO_REPO_ENABLED is not set to true")

    labels = os.getenv("LABELS")
    if labels is None:
        raise Exception("LABELS environment variable is not set")

    mono_dict = {m.name: m for m in action_context.mono_repo_project}

    labels = set(labels.split(","))
    if len(labels) == 0:
        raise Exception(f"No LABELS found starting with {startswith}")

    if len(labels) > 1:
        raise Exception(f"Multiple LABELS found starting with {startswith}")

    mono_config_file = mono_dict.get(list(labels)[0]).config_file

    set_output("MONO_CONFIG_FILE", mono_config_file.as_posix())
