import json
import os

from action_tool.load_config import load_config
from action_tool.utils import deserialize_str, get_output, set_output


def check_monorepo_labels():
    action_context = load_config()
    if action_context.mono_repo_enabled is False:
        raise Exception("MONO_REPO_ENABLED is not set to true")

    labels = json.loads(os.environ['LABELS'])
    if labels is None:
        raise Exception("LABELS environment variable is not set")

    mono_dict = {m.name: m for m in action_context.mono_repo_project}
    mono_labels = set(mono_dict.keys())

    overlapped_labels = mono_labels.intersection(labels)

    if len(overlapped_labels) == 0:
        set_labels_if_not_already_created(labels, mono_dict)
    elif len(overlapped_labels) > 1:
        raise Exception(f"Multiple LABELS found starting with {startswith}")

    mono_config_file = mono_dict.get(list(overlapped_labels)[0]).config_file

    set_output("MONO_CONFIG_FILE", mono_config_file.as_posix())
