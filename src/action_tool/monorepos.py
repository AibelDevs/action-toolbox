import json
import os

from action_tool.load_config import load_config
from action_tool.utils import deserialize_str, get_output, set_output


def get_monorepo_config_file():
    load_config()

    startswith = os.getenv("STARTSWITH")
    if startswith is None:
        raise Exception("STARTSWITH environment variable is not set")

    data = get_output()
    toml_data = json.loads(deserialize_str(data["toml_data"]))
    mono_repos_data = toml_data["tool"]["mono_repo"]
    if len(mono_repos_data) == 0:
        raise Exception("No monorepo found")

    labels = os.getenv("LABELS")
    if labels is None:
        raise Exception("LABELS environment variable is not set")

    mono_dict = {m["name"]: m for m in mono_repos_data}

    labels = [lbl for lbl in labels.split(",") if lbl.startswith(startswith)]
    if len(labels) == 0:
        raise Exception(f"No LABELS found starting with {startswith}")

    if len(labels) > 1:
        raise Exception(f"Multiple LABELS found starting with {startswith}")

    mono_config_file = mono_dict.get(labels[0])["config_file"]

    set_output("MONO_CONFIG_FILE", mono_config_file)
