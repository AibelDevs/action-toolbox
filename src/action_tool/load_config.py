import json
import os
import pathlib
from dataclasses import dataclass, field
import toml
from semantic_release.cli.config import RawConfig
from semantic_release.cli.util import load_raw_config_file

from action_tool.utils import set_output


@dataclass
class MonoRepo:
    name: str
    enabled: bool
    path: pathlib.Path
    config_file: pathlib.Path
    raw_config: RawConfig


@dataclass
class ActionContext:
    config_toml_file: pathlib.Path
    config_toml_data: dict
    raw_config: RawConfig

    mono_repo_enabled: bool
    docker_enabled: bool
    gitops_enabled: bool
    python_enabled: bool
    pip_enabled: bool
    conda_enabled: bool
    custom_pypi_server: bool
    custom_quetz_server: bool
    anaconda_server: bool

    mono_repo_project: list[MonoRepo] = field(default_factory=list)

    def set_outputs(self):
        set_output("toml_data", json.dumps(self.config_toml_data), True)
        set_output("docker_enabled", self.docker_enabled)
        # I cannot pass a list to the github actions matrix, so I have to convert the list to a dict
        set_output("docker_matrix", json.dumps({'docker': self.config_toml_data["tool"].get("docker", [])}))
        set_output("gitops_enabled", self.gitops_enabled)

        # I cannot pass a list to the github actions matrix, so I have to convert the list to a dict
        set_output("gitops_matrix", json.dumps({'gitops': self.config_toml_data["tool"].get("gitops", [])}))

        set_output("python_enabled", self.python_enabled)
        if self.python_enabled:
            set_output("pip_enabled", self.pip_enabled)
            if self.pip_enabled:
                set_output("custom_pypi_server", self.custom_pypi_server)

            set_output("conda_enabled", self.conda_enabled)
            if self.conda_enabled:
                set_output("custom_quetz_server", self.custom_quetz_server)
                set_output("anaconda_server", self.anaconda_server)

    def get_toml_version(self, specific_mono_repo=None):
        if self.mono_repo_enabled:
            if specific_mono_repo is None:
                raise ValueError("specific_mono_repo must be set if mono_repo_enabled is True")
            for mono_repo in self.mono_repo_project:
                if mono_repo.name == specific_mono_repo:
                    config = load_config(mono_repo.config_file)
                    return config.get_toml_version()

        return self.config_toml_data["tool"]["action"]["version"]


def load_config(config_file=None) -> ActionContext:
    config_toml_file = config_file if config_file is not None else os.getenv("CONFIG_TOML_FILE")
    if config_toml_file is None:
        raise ValueError("CONFIG_TOML_FILE environment variable is not set")

    config_toml_file = pathlib.Path(config_toml_file).resolve().absolute()

    data = toml.load(config_toml_file)

    # Docker
    docker_config_list = data["tool"].get("docker", [])
    docker_enabled = False
    for docker_config in docker_config_list:
        if docker_config["enabled"]:
            docker_enabled = True
            break

    # GitOps
    gitops_config_list = data["tool"].get("gitops", [])
    gitops_enabled = False
    for gitops_config in gitops_config_list:
        if gitops_config["enabled"]:
            gitops_enabled = True
            break

    # Python
    py_tool = data["tool"].get("python", dict(enabled=False))
    python_enabled = py_tool.get("enabled", False)

    pip_enabled = False
    conda_enabled = False
    custom_pypi_server = False
    custom_quetz_server = False
    anaconda_server = False
    if python_enabled:
        pip_tool = py_tool.get("pip", dict(enabled=False))
        pip_enabled = pip_tool.get("enabled", False)

        if pip_enabled:
            custom_pypi_server = pip_tool.get("use_custom_pypi_server", False)

        conda_tool = py_tool.get("conda", dict(enabled=False))
        conda_enabled = conda_tool.get("enabled", False)

        if conda_enabled:
            custom_quetz_server = conda_tool.get("use_custom_quetz_server", False)
            anaconda_server = conda_tool.get("use_anaconda_server", False)


    mono_repos_data = data["tool"].get("mono_repo", dict()).get("project", [])
    mono_repo_enabled = False
    mono_repo_project = []
    for mono_repo in mono_repos_data:
        mono_repo_enabled = mono_repo.get("enabled", False)
        mono_config_file = config_toml_file.parent / mono_repo["config_file"]
        config_obj = load_raw_config_file(mono_config_file)
        model = RawConfig.model_validate(config_obj)

        mono_repo_project.append(MonoRepo(
            name=mono_repo["name"],
            enabled=mono_repo_enabled,
            path=config_toml_file.parent / mono_repo["path"],
            config_file=mono_config_file,
            raw_config=model,
        ))

    if mono_repo_enabled:
        raw_config = None
    else:
        config_obj = load_raw_config_file(config_toml_file)
        raw_config = RawConfig.model_validate(config_obj)

    return ActionContext(
        config_toml_file=config_toml_file,
        config_toml_data=data,
        raw_config=raw_config,
        mono_repo_enabled=mono_repo_enabled,
        docker_enabled=docker_enabled,
        gitops_enabled=gitops_enabled,
        python_enabled=python_enabled,
        pip_enabled=pip_enabled,
        conda_enabled=conda_enabled,
        custom_pypi_server=custom_pypi_server,
        custom_quetz_server=custom_quetz_server,
        anaconda_server=anaconda_server,
        mono_repo_project=mono_repo_project
    )
