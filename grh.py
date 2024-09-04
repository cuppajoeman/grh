import os
import requests
import argparse
import configparser
from subprocess import run, PIPE

# Function to get public repositories from a specified GitHub organization or user
def get_public_repos(github_url):
    print(f"Fetching public repositories from {github_url}...")
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    repos = []
    page = 1
    while True:
        response = requests.get(github_url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code != 200:
            print(f"Failed to retrieve repositories: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

# Function to display the structure of the src directory
def display_src_structure(src_path):
    for root, dirs, files in os.walk(src_path):
        level = root.replace(src_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

# Function to add a submodule
def add_submodule(repo_url, submodule_path, src_path):
    try:
        full_submodule_path = os.path.join(src_path, submodule_path)
        os.makedirs(full_submodule_path, exist_ok=True)

        current_dir = os.getcwd()
        os.chdir(full_submodule_path)

        result = run(["git", "submodule", "add", repo_url], stdout=PIPE, stderr=PIPE)
        os.chdir(current_dir)

        if result.returncode == 0:
            print(f"Submodule added in {full_submodule_path}")
        else:
            print(f"Failed to add submodule. Error: {result.stderr.decode()}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to clone a repository
def clone_repo(repo_url, clone_path, src_path):
    try:
        full_clone_path = os.path.join(src_path, clone_path)
        result = run(["git", "clone", repo_url, full_clone_path], stdout=PIPE, stderr=PIPE)

        if result.returncode == 0:
            print(f"Repository cloned to {full_clone_path}")
        else:
            print(f"Failed to clone repository. Error: {result.stderr.decode()}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main interactive function
def main():
    parser = argparse.ArgumentParser(description="Manage Git repositories from a specified GitHub organization or user.")
    parser.add_argument('src', type=str, help='The src directory where repositories will be added.')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to the configuration file.')
    parser.add_argument('--org', type=str, help='GitHub organization name.')
    parser.add_argument('--user', type=str, help='GitHub username.')

    args = parser.parse_args()
    src_path = args.src
    config_file = args.config
    github_org = args.org
    github_user = args.user

    if not os.path.exists(src_path):
        print(f"The specified src directory '{src_path}' does not exist.")
        return

    # Determine the GitHub URL
    if github_org:
        github_url = f"https://api.github.com/orgs/{github_org}/repos"
    elif github_user:
        github_url = f"https://api.github.com/users/{github_user}/repos"
    else:
        config = configparser.ConfigParser()
        config.read(config_file)

        if 'Settings' not in config or 'github_org' not in config['Settings'] and 'github_user' not in config['Settings']:
            print(f"The configuration file '{config_file}' is missing the 'github_org' or 'github_user' setting.")
            return

        github_org = config['Settings'].get('github_org')
        github_user = config['Settings'].get('github_user')

        if github_org:
            github_url = f"https://api.github.com/orgs/{github_org}/repos"
        elif github_user:
            github_url = f"https://api.github.com/users/{github_user}/repos"
        else:
            print("Neither GitHub organization nor user specified in config file.")
            return

    repos = get_public_repos(github_url)

    while True:
        command = input("Enter 'list' to list all repositories, 'add' to add a repository as a submodule, 'clone' to clone a repository, or 'exit' to quit: ").strip().lower()
        if command == 'exit':
            break
        elif command == 'list':
            print("Public repositories:")
            for repo in repos:
                print(f"{repo['name']} - {repo['ssh_url']}")
        elif command == 'add':
            search_keyword = input("Enter a keyword to search for repositories: ").strip()
            matching_repos = [repo for repo in repos if search_keyword.lower() in repo['name'].lower()]
            if not matching_repos:
                print("No matching repositories found.")
                continue

            print("Matching repositories:")
            for i, repo in enumerate(matching_repos):
                print(f"{i + 1}: {repo['name']} - {repo['ssh_url']}")

            choice = input("Enter the number of the repository to add as a submodule, or 'n' to search again: ").strip()
            if choice.lower() == 'n':
                continue

            try:
                repo_index = int(choice) - 1
                if repo_index < 0 or repo_index >= len(matching_repos):
                    print("Invalid choice.")
                    continue

                repo_to_add = matching_repos[repo_index]
                print("Current src directory structure:")
                display_src_structure(src_path)

                submodule_path = input(f"Enter the path to add the submodule (relative to {src_path}/): ").strip()

                add_submodule(repo_to_add['ssh_url'], submodule_path, src_path)

            except ValueError:
                print("Invalid input. Please enter a valid number.")
        elif command == 'clone':
            search_keyword = input("Enter a keyword to search for repositories: ").strip()
            matching_repos = [repo for repo in repos if search_keyword.lower() in repo['name'].lower()]
            if not matching_repos:
                print("No matching repositories found.")
                continue

            print("Matching repositories:")
            for i, repo in enumerate(matching_repos):
                print(f"{i + 1}: {repo['name']} - {repo['ssh_url']}")

            choice = input("Enter the number of the repository to clone, or 'n' to search again: ").strip()
            if choice.lower() == 'n':
                continue

            try:
                repo_index = int(choice) - 1
                if repo_index < 0 or repo_index >= len(matching_repos):
                    print("Invalid choice.")
                    continue

                repo_to_clone = matching_repos[repo_index]
                print("Current src directory structure:")
                display_src_structure(src_path)

                clone_path = input(f"Enter the path to clone the repository (relative to {src_path}/): ").strip()

                clone_repo(repo_to_clone['ssh_url'], clone_path, src_path)

            except ValueError:
                print("Invalid input. Please enter a valid number.")
        else:
            print("Invalid command. Please enter 'list', 'add', 'clone', or 'exit'.")

if __name__ == "__main__":
    main()
