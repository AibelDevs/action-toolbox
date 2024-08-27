import base64
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
        "scopes": ["write:user", "write:repository"]  # You can add other scopes as needed
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

    if response.status_code == 201:
        print("Fake repository created successfully.")
    else:
        raise ValueError(f"Failed to create fake repository: {response.status_code}")

    return response


# Function to upload files to the repo
def upload_files_to_repo(gitea_url: str, owner: str, repo: str, token: str, files: dict, commit_message: str):
    upload_url = f"{gitea_url}/api/v1/repos/{owner}/{repo}/contents/"

    # Iterate over each file you want to upload
    for file_path, file_content in files.items():
        # Base64 encode the file content as required by the API
        encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')

        # Define the request payload
        data = {
            "content": encoded_content,
            "message": commit_message,
        }

        # Upload each file
        response = requests.post(
            f"{upload_url}{file_path}",
            headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            json=data
        )

        # Check if the upload was successful
        if response.status_code == 201:
            print(f"File '{file_path}' uploaded successfully.")
        else:
            print(f"Failed to upload '{file_path}': {response.status_code} - {response.text}")


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
