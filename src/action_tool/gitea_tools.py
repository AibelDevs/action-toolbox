import pathlib
import subprocess
import time

import requests
import requests.auth


# Authenticate and get a token
def get_gitea_token(gitea_url: str, username: str, password: str) -> str:
    # API endpoint for creating a new access token
    token_url = f"{gitea_url}/api/v1/users/{username}/tokens"

    # Prepare the headers with basic auth
    auth = requests.auth.HTTPBasicAuth(username, password)

    # Generate a unique token name
    token_name = f"my_token_{int(time.time())}"

    data = {
        "name": token_name,  # Use the unique token name
        "scopes": ["write:user", "write:repository", "read:issue", "write:issue"]  # You can add other scopes as needed
    }

    # Send the POST request to create a token
    response = requests.post(token_url, auth=auth, json=data)

    # Check if the request was successful
    if response.status_code == 201:
        token = response.json().get('sha1')
        print(f"Token created successfully: {token}")
        return token
    else:
        raise ValueError(f"Failed to create token: {response.status_code} - {response.text}")


def create_repository(repo_data: dict, gitea_url: str, token) -> requests.Response:
    create_repo_url = f"{gitea_url}/api/v1/user/repos"

    # Make the POST request to create a repository
    response = requests.post(
        create_repo_url,
        json=repo_data,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
        },
    )
    repo_name = repo_data['name']
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully.")
    else:
        raise ValueError(f"Failed to create fake repository: {response.status_code}")

    return response


def list_gitea_tokens(gitea_url: str, username: str, password: str):
    token_url = f"{gitea_url}/api/v1/users/{username}/tokens"
    auth = requests.auth.HTTPBasicAuth(username, password)

    response = requests.get(token_url, auth=auth)

    if response.status_code == 200:
        tokens = response.json()
        for token in tokens:
            print(f"Token Name: {token['name']} - Token ID: {token['id']}")
        return tokens
    else:
        print(f"Failed to list tokens: {response.status_code} - {response.text}")
        return None


def delete_gitea_token(gitea_url: str, username: str, password: str, token_id: int):
    delete_url = f"{gitea_url}/api/v1/users/{username}/tokens/{token_id}"
    auth = requests.auth.HTTPBasicAuth(username, password)

    response = requests.delete(delete_url, auth=auth)

    if response.status_code == 204:
        print(f"Token with ID {token_id} deleted successfully.")
    else:
        print(f"Failed to delete token: {response.status_code} - {response.text}")


def get_or_create_gitea_token(gitea_url: str, username: str, password: str, token_name: str) -> str:
    # List existing tokens
    tokens = list_gitea_tokens(gitea_url, username, password)

    # Delete any token with the same name
    for token in tokens:
        if token['name'] == token_name:
            delete_gitea_token(gitea_url, username, password, token['id'])

    # Create a new token with the desired name
    return get_gitea_token(gitea_url, username, password)


def create_gitea_pull_request(gitea_url: str, owner: str, repo: str, token: str, title: str, head: str, base: str):
    pr_url = f"{gitea_url}/api/v1/repos/{owner}/{repo}/pulls"

    data = {
        "title": title,
        "head": head,
        "base": base,
    }

    response = requests.post(
        pr_url,
        headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        json=data
    )

    if response.status_code == 201:
        print(f"Pull request created successfully: {response.json().get('html_url')}")
    else:
        raise ValueError(f"Failed to create pull request: {response.status_code} - {response.text}")

def merge_gitea_pr(pr_number, url, owner, repo, token):
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    merge_url = f"{url}/api/v1/repos/{owner}/{repo}/pulls/{pr_number}/merge"

    try:
        response = requests.post(merge_url, headers=headers)
        response.raise_for_status()
        print(f"PR #{pr_number} has been merged successfully.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while merging PR #{pr_number}: {e}")

def get_runner_registration_token(gitea_url: str, admin_username: str, admin_password: str) -> str:
    """
    Retrieves a runner registration token from the Gitea instance.
    """
    # Construct the API endpoint URL for the runner registration token
    api_url = f"{gitea_url}/api/v1/admin/runners/registration-token"

    # Basic Authentication with admin credentials
    auth = requests.auth.HTTPBasicAuth(admin_username, admin_password)

    # Make the API request to get the registration token
    response = requests.get(api_url, auth=auth)

    # Check if the request was successful
    if response.status_code == 200:
        token = response.json().get('token')
        if token:
            print(f"Runner registration token retrieved successfully: {token}")
            return token
        else:
            raise ValueError("Token not found in the response.")
    else:
        raise ValueError(f"Failed to retrieve runner registration token: {response.status_code} - {response.text}")


def get_gitea_labels(gitea_url: str, owner: str, repo: str, token: str) -> list[dict]:
    get_label_url = f"{gitea_url}/api/v1/repos/{owner}/{repo}/labels"
    # Make the POST request to create a repository
    response = requests.get(
        get_label_url,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
        },
    )

    if response.status_code == 200:
        labels = response.json()
        return labels
    else:
        raise ValueError(f"Failed to retrieve labels: {response.status_code} - {response.text}")


def create_gitea_label(label: str, gitea_url: str, owner: str, repo: str, token: str, color: str = "#00aabb"):
    create_label_url = f"{gitea_url}/api/v1/repos/{owner}/{repo}/labels"
    label_data = {
        "name": label,
        "color": color
    }
    # Make the POST request to create a repository
    response = requests.post(
        create_label_url,
        json=label_data,
        headers={
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
        },
    )
    if response.status_code == 201:
        print(f"Label '{label}' created successfully.")
    else:
        raise ValueError(f"Failed to create label: {response.status_code} - {response.text}")


def create_gitea_release_labels_if_not_exists(gitea_url: str, owner: str, repo: str, token: str):
    lbls_with_color = {
        'release-skip': 'b3b3b3',  # Gray
        'release-auto': 'ffff00',  # Yellow
        'release-patch': '00ff00',  # Green
        'release-minor': '0000ff',  # Blue
        'release-major': 'ff0000',  # Red
        'silence-bot': '000000'  # Black
    }
    valid_labels = set(lbls_with_color.keys())
    existing_labels = set(get_gitea_labels(gitea_url, owner, repo, token))
    missing_labels = valid_labels - existing_labels
    for label in missing_labels:
        lbl_with_color = lbls_with_color[label]
        create_gitea_label(label, gitea_url, owner, repo, token, color=lbl_with_color)


def generate_ssh_keypair(key_name="source_key"):
    """
    Generate an SSH key pair.
    """
    key_dir = pathlib.Path("/tmp/ssh_keys")
    key_dir.mkdir(parents=True, exist_ok=True)
    key_path = key_dir / key_name
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(key_path), "-N", ""])

    with open(f"{key_path}.pub", "r") as pub_key_file:
        public_key = pub_key_file.read()

    return str(key_path), public_key


def add_deploy_key_to_gitea(gitea_url, token, repo_owner, repo_name, public_key):
    """
    Add the generated SSH public key as a deploy key to the specified Gitea repository.
    """
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": "Source Deploy Key",
        "key": public_key,
        "read_only": False
    }
    response = requests.post(
        f"{gitea_url}/api/v1/repos/{repo_owner}/{repo_name}/keys",
        headers=headers,
        json=data
    )
    response.raise_for_status()  # Raise an error for bad HTTP response


def add_secret_to_gitea(gitea_url, token, repo_owner, repo_name, secret_name, secret_value):
    """
    Add a secret to a Gitea repository.
    """
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }

    data = {
        "name": secret_name,
        "data": secret_value  # Use 'data' to represent the secret value
    }
    response = requests.put(
        f"{gitea_url}/api/v1/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}",
        headers=headers,
        json=data
    )
    if response.status_code == 201:
        print(f"Secret '{secret_name}' added successfully.")
    else:
        raise ValueError(f"Failed to add secret: {response.status_code} - {response.text}")

    print(f"Secret '{secret_name}' added to {repo_owner}/{repo_name}.")


def comment_on_gitea_pr(comment_body, pr_index, gitea_url, repo_owner, repo_name, token):
    # Set up the headers for authentication
    headers = {
        'Authorization': f'token {token}',
        'Content-Type': 'application/json'
    }

    # The URL for adding a comment to a pull request
    url = f'{gitea_url}/api/v1/repos/{repo_owner}/{repo_name}/pulls/{pr_index}/reviews'

    # The payload containing the comment body
    payload = {
        'body': comment_body
    }

    # Make the POST request to add the comment
    response = requests.post(url, headers=headers, json=payload)

    # Check the response
    if response.status_code == 200:
        print("Comment added successfully!")
    else:
        raise ValueError(f"Failed to add comment: {response.status_code} - {response.text}")
