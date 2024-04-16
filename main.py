import os
import git
import csv
from typing import Optional

def get_last_commit_info(repo_path: str):
    repo = git.Repo(repo_path)
    last_commit = next(repo.iter_commits('master', max_count=1))
    return last_commit.committed_datetime, last_commit.author.name

def extract_readme_lines(repo_path: str, num_lines: int = 5) -> Optional[str]:
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            return ''.join([next(f) for _ in range(num_lines)])
    return None

def scan_repos_and_create_csv(dir_path: str, csv_file: str):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Folder Name", "Last Commit Date", "Last Commit Author", "README Extract"])

        for folder in os.listdir(dir_path):
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path) and '.git' in os.listdir(repo_path):
                    commit_date, commit_author = get_last_commit_info(repo_path)
                    readme_extract = extract_readme_lines(repo_path)
                    writer.writerow([folder, commit_date, commit_author, readme_extract])
            except git.InvalidGitRepositoryError:
                print(f"{folder} is not a valid Git repository. Skipping...")
                continue
            except PermissionError:
                print(f"Permission denied for {folder}. Skipping...")
                continue
# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')