import os
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()
auth_token = os.getenv("AUTH_TOKEN")

# Configuration
AUTH_SERVICE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("ADMIN_NAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")
TEAM_NAME = os.getenv("TEAM_NAME")

ENV_FILE = ".env"
TOKEN_KEY = "AUTH_TOKEN"


def write_token_to_env(token: str):
    """
    Write or replace AUTH_TOKEN in the .env file.
    """
    lines = []

    # Read existing .env if it exists
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    key_found = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{TOKEN_KEY}="):
            new_lines.append(f"{TOKEN_KEY}={token}\n")
            key_found = True
        else:
            new_lines.append(line)

    # If key not found, append it
    if not key_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{TOKEN_KEY}={token}\n")

    # Write back to .env
    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)


def issue_token():
    response = requests.get(
        f"{AUTH_SERVICE_URL}/auth/issue-token",
        params={"name": TEAM_NAME},
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
    )

    if response.status_code == 200:
        token = response.json()["token"]
        write_token_to_env(token)
        print("Token issued and written to .env successfully.")
    else:
        try:
            error = response.json()
        except Exception:
            error = response.text
        print(f"Error: {response.status_code} - {error}")


if __name__ == "__main__":
    issue_token()