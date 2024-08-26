import json
import os

import toml

from action_tool.utils import set_output


def load_config():
    data = toml.load(os.getenv("CONFIG_TOML_FILE"))
    set_output("toml_data", json.dumps(data), True)

    # Docker
    docker_config_list = data["tool"].get("docker", [])
    docker_enabled = False
    for docker_config in docker_config_list:
        if docker_config["enabled"]:
            docker_enabled = True
            break

    set_output("docker_enabled", docker_enabled)

    # I cannot pass a list to the github actions matrix, so I have to convert the list to a dict
    set_output("docker_matrix", json.dumps({'docker': docker_config_list}))

    # GitOps
    gitops_config_list = data["tool"].get("gitops", [])
    gitops_enabled = False
    for gitops_config in gitops_config_list:
        if gitops_config["enabled"]:
            gitops_enabled = True
            break

    set_output("gitops_enabled", gitops_enabled)

    # I cannot pass a list to the github actions matrix, so I have to convert the list to a dict
    set_output("gitops_matrix", json.dumps({'gitops': gitops_config_list}))

    # Python
    py_tool = data["tool"].get("python", dict(enabled=False))
    python_enabled = py_tool.get("enabled", False)
    set_output("python_enabled", python_enabled)

    if python_enabled:
        pip_tool = py_tool.get("pip", dict(enabled=False))
        pip_enabled = pip_tool.get("enabled", False)
        set_output("pip_enabled", pip_enabled)

        if pip_enabled:
            custom_pypi_server = pip_tool.get("use_custom_pypi_server", False)
            set_output("custom_pypi_server", custom_pypi_server)

        conda_tool = py_tool.get("conda", dict(enabled=False))
        conda_enabled = conda_tool.get("enabled", False)
        set_output("conda_enabled", conda_enabled)

        if conda_enabled:
            custom_quetz_server = conda_tool.get("use_custom_quetz_server", False)
            set_output("custom_quetz_server", custom_quetz_server)

            anaconda_server = conda_tool.get("use_anaconda_server", False)
            set_output("anaconda_server", anaconda_server)

    print(data)
