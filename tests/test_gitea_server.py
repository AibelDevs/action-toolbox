import pathlib
import time

import docker
import pytest
import requests
from docker.errors import NotFound

from action_tool.gitea_tools import get_gitea_token, create_repository, upload_files_to_repo, get_or_create_gitea_token
from action_tool.github_state import is_in_github_action
from tests.conftest import proj_mono_1


@pytest.fixture(scope="session")
def gitea_container():
    if is_in_github_action():
        client = docker.from_env()
    else:
        client = docker.DockerClient(base_url='tcp://localhost:2375')

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
    )

    time.sleep(10)  # Give Gitea some time to start up

    yield container

    # Clean up after tests
    container.stop()
    container.remove()
    client.volumes.get("pytest_gitea_volume").remove(force=True)


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
    session = requests.Session()
    login_url = f"{gitea_url}/user/login"
    csrf_token = session.cookies.get("i_like_gitea")

    # Log in as the dummy user
    session.post(
        login_url,
        data={
            "user_name": create_dummy_user["username"],
            "password": create_dummy_user["password"],
            "_csrf": csrf_token,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )



    # Create a new repository
    repo_data = {
        "name": "fakerepo",  # Adjust the key to "name" (not "repo_name") as per Gitea API
        "description": "A fake repository for testing purposes",
        "private": False,  # Set to True if you want to create a private repo
    }

    create_repository(repo_data, gitea_url, created_token)

    return repo_data


def test_gitea_setup(gitea_container, gitea_url, create_dummy_user, create_fake_repository):
    assert gitea_container.status == "created"
    assert requests.get(gitea_url).status_code == 200
    print("Gitea setup and tests passed successfully.")

def test_gitea_upload(gitea_container, gitea_url, create_dummy_user, create_fake_repository, created_token):
    proj_mono_1 = pathlib.Path(__file__).parent.absolute() / "files/proj_mono_1"
    files = dict()
    for fp in proj_mono_1.rglob(".*"):
        fp_rel = fp.relative_to(proj_mono_1)
        files[fp_rel.as_posix()] = "auto-commited"

    upload_files_to_repo(gitea_url, create_dummy_user["username"], create_fake_repository["name"], created_token, files, "initial commit")
