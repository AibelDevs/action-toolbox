import os
import pathlib
import shutil
import tempfile
import time

import docker
import git
import pytest
import requests
from action_tool.git_remote_adapter import is_in_github_action, is_in_gitea_action
from action_tool.gitea_tools import get_gitea_token, create_repository, \
    get_runner_registration_token, generate_ssh_keypair, add_deploy_key_to_gitea, add_secret_to_gitea
from action_tool.utils import encode_ssh_key
from docker.errors import NotFound


def get_docker_env():
    if is_in_github_action() or is_in_gitea_action():
        client = docker.from_env()
    else:  # Running locally
        try:
            client = docker.DockerClient(base_url='tcp://localhost:2375')
        except docker.errors.DockerException:
            client = docker.from_env()

    return client


@pytest.fixture(scope="session")
def docker_network():
    client = get_docker_env()

    # Create a network if it doesn't exist
    network_name = "gitea_network"
    try:
        network = client.networks.get(network_name)
    except docker.errors.NotFound:
        network = client.networks.create(network_name, driver="bridge")

    yield network

    # Optionally remove the network after the tests
    network.remove()


@pytest.fixture(scope="session")
def gitea_container(docker_network):
    client = get_docker_env()

    # Pull the latest Gitea image if not present
    try:
        client.images.get("gitea/gitea:latest")
    except NotFound:
        print("Pulling Gitea Docker image...")
        client.images.pull("gitea/gitea:latest")

    # Start a Gitea container
    container = client.containers.run(
        "gitea/gitea:latest",
        detach=True,
        environment={
            "USER_UID": "1000",
            "USER_GID": "1000",
            "DB_TYPE": "sqlite3",
            "GITEA__database__DB_TYPE": "sqlite3",
            "GITEA__database__PATH": "/data/gitea/gitea.db",
            "GITEA__security__INSTALL_LOCK": "true",
            "GITEA__security__SECRET_KEY": "supersecretkey",
            "GITEA__server__SSH_DOMAIN": "localhost",
            "GITEA__server__DOMAIN": "localhost",
            "GITEA__server__HTTP_PORT": "3000",
            "GITEA__service__DISABLE_REGISTRATION": "false",
            "GITEA__service__REQUIRE_SIGNIN_VIEW": "false"
        },
        ports={"3000/tcp": 3000},
        volumes={
            "pytest_gitea_volume": {"bind": "/data", "mode": "rw"}
        },
        name="pytest_gitea",
        network=docker_network.name
    )

    time.sleep(10)  # Give Gitea some time to start up

    yield container

    # Clean up after tests
    container.stop()
    container.remove()
    client.volumes.get("pytest_gitea_volume").remove(force=True)

@pytest.fixture(scope="session")
def ssh_deploy_key(gitea_url, create_dummy_user, create_fake_repository, docker_network, created_token):
    # Generate SSH key pair for the source key
    key_path, public_key = generate_ssh_keypair()

    # Add the public key as a deploy key in the Gitea repository
    add_deploy_key_to_gitea(
        gitea_url=gitea_url,
        token=created_token,  # Assume the token is available
        repo_owner=create_dummy_user["username"],
        repo_name=create_fake_repository["name"],
        public_key=public_key
    )

    # Base64 encode the private key and add it as a secret to the Gitea repository
    encoded_private_key = encode_ssh_key(key_path)
    data = dict(encoded_private_key=encoded_private_key)
    yield data

    os.remove(key_path)
    os.remove(f"{key_path}.pub")


@pytest.fixture(scope="session")
def act_runner_container(gitea_url, create_dummy_user, create_fake_repository, docker_network, created_token, root_dir):
    client = get_docker_env()

    dockerfile_path = root_dir / "tests/files/runner.Dockerfile"
    # Docker image for the GitHub Actions runner
    runner_image = "my-gitea-runner:latest"

    # Build the runner image if it's not available locally
    try:
        client.images.get(runner_image)
    except docker.errors.ImageNotFound:
        print(f"Building {runner_image}...")
        client.images.build(path=dockerfile_path.parent.as_posix(), dockerfile=dockerfile_path.as_posix(),
                            tag=runner_image)

    runner_token = get_runner_registration_token(gitea_url, create_dummy_user["username"],
                                                 create_dummy_user["password"])

    # Start the Gitea runner container
    container = client.containers.run(
        runner_image,
        detach=True,
        environment={
            "GITEA_INSTANCE_URL": "http://pytest_gitea:3000",
            "GITEA_RUNNER_REGISTRATION_TOKEN": runner_token,
            "RUNNER_NAME": f"{create_dummy_user['username']}-runner",
            "RUNNER_REPOSITORY": f"{create_dummy_user['username']}/{create_fake_repository['name']}",
            "RUNNER_WORKDIR": "/runner/_work",
            "RUNNER_LABELS": "self-hosted,Linux,X64,ubuntu-latest"
        },
        volumes={
            "runner_workdir": {"bind": "/runner/_work", "mode": "rw"},
            "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},  # Mount Docker socket
        },
        name="gitea_runner",
        network=docker_network.name
    )

    time.sleep(10)  # Give the runner some time to register

    yield container

    # Cleanup after the tests
    container.stop()
    container.remove()



@pytest.fixture(scope="session")
def gitea_url():
    return "http://localhost:3000"


@pytest.fixture(scope="session")
def create_dummy_user(gitea_url):
    user_data = {
        "email": "dummy@example.com",
        "username": "dummyuser",
        "password": "dummypassword",
    }

    # Register the user
    registration_url = f"{gitea_url}/user/sign_up"
    session = requests.Session()
    session.get(registration_url)  # Retrieve the CSRF token
    csrf_token = session.cookies.get("i_like_gitea")

    response = session.post(
        registration_url,
        data={
            "user_name": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "retype": user_data["password"],
            "_csrf": csrf_token,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    if response.status_code == 200:
        print("Dummy user created successfully.")
    else:
        print(f"Failed to create dummy user: {response.status_code}")

    return user_data


@pytest.fixture(scope="session")
def created_token(gitea_url, create_dummy_user):
    return get_gitea_token(gitea_url, create_dummy_user["username"], create_dummy_user["password"])


@pytest.fixture(scope="session")
def create_fake_repository(gitea_url, create_dummy_user, created_token):
    # Create a new repository
    repo_data = {
        "name": "fakerepo",
        "description": "A fake repository for testing purposes",
        "private": False,
    }

    create_repository(repo_data, gitea_url, created_token)

    return repo_data


@pytest.fixture(scope="session")
def create_action_toolbox_repository(gitea_url, create_dummy_user, created_token):
    # Create a new repository
    repo_data = {
        "name": "action-toolbox",
        "description": "Action toolbox repo",
        "private": False,
    }

    create_repository(repo_data, gitea_url, created_token)

    return repo_data


def directory_ignore_func(directory, contents):
    ignore_list = []
    if ".git" in contents:
        ignore_list.append(".git")
    if "ci-testing.yaml" in contents:
        ignore_list.append("ci-testing.yaml")
    return ignore_list


@pytest.fixture(scope="session")
def mock_proj_a(gitea_container, gitea_url, proj_mono_1, create_dummy_user, create_fake_repository) -> pathlib.Path:
    username = create_dummy_user["username"]
    password = create_dummy_user["password"]
    repo_name = create_fake_repository["name"]

    repo_url = f"http://{username}:{password}@{gitea_url.replace('http://', '')}/{username}/{repo_name}.git"
    # ssh_git_url = gitea_url.replace('http://', '').replace('3000', '2222')
    # repo_url = f"git@{ssh_git_url}:{username}/{repo_name}.git"
    # Create a temporary directory for the local repository
    with tempfile.TemporaryDirectory() as local_temp_dir:
        # Clone a Git repository in the temporary directory
        local_repo = git.Repo.clone_from(repo_url, local_temp_dir)
        # Copy the contents of the mono-repo to the temporary directory
        shutil.copytree(str(proj_mono_1), local_temp_dir, dirs_exist_ok=True)

        curr_branch = local_repo.active_branch

        # Add the username and email
        local_repo.git.config("user.email", create_dummy_user["email"])
        local_repo.git.config("user.name", username)

        # Perform any Git-related operations here, e.g., adding and committing files
        local_repo.git.add(".")
        local_repo.git.execute(["git", "commit", "-am", "Initial Commit"])
        local_repo.git.push("origin", curr_branch.name, set_upstream=True)
        yield pathlib.Path(local_temp_dir)


@pytest.fixture(scope="session")
def action_toolbox_proj(gitea_container, gitea_url, root_dir, create_dummy_user,
                        create_action_toolbox_repository) -> pathlib.Path:
    username = create_dummy_user["username"]
    password = create_dummy_user["password"]
    repo_name = create_action_toolbox_repository["name"]

    repo_url = f"http://{username}:{password}@{gitea_url.replace('http://', '')}/{username}/{repo_name}.git"
    # ssh_git_url = gitea_url.replace('http://', '').replace('3000', '2222')
    # repo_url = f"git@{ssh_git_url}:{username}/{repo_name}.git"
    # Create a temporary directory for the local repository
    with tempfile.TemporaryDirectory() as local_temp_dir:
        # Clone a Git repository in the temporary directory
        local_repo = git.Repo.clone_from(repo_url, local_temp_dir)
        # Copy the contents of the mono-repo to the temporary directory
        shutil.copytree(str(root_dir), pathlib.Path(local_temp_dir), dirs_exist_ok=True, ignore=directory_ignore_func)
        curr_branch = local_repo.active_branch

        # Add the username and email
        local_repo.git.config("user.email", create_dummy_user["email"])
        local_repo.git.config("user.name", username)

        # Perform any Git-related operations here, e.g., adding and committing files
        local_repo.git.add(".")
        local_repo.git.execute(["git", "commit", "-am", "Initial Commit"])
        local_repo.git.push("origin", curr_branch.name, set_upstream=True)
        yield pathlib.Path(local_temp_dir)
