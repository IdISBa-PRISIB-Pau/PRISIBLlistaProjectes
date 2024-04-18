import os
import git
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader
from endesive import pdf
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

def scan_repos_and_create_csv(dir_path: str, csv_file: str, pdf_prefixes: list = None):
    if pdf_prefixes is None:
        pdf_prefixes = ['SSPT','PSPT']  # Default value

    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Folder Name", "Codi", "Data Inici",  "Last Commit Date", "Last Commit Author"] + pdf_prefixes)

        for folder in os.listdir(dir_path):
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    data_inici = extract_field_from_readme(repo_path, "- Data inici:")

                    pdf_statuses = []
                    for prefix in pdf_prefixes:
                        status = "NO"
                        for dirpath, dirnames, filenames in os.walk(repo_path):
                            for file in filenames:
                                if re.match(r'^' + prefix + r'.*\d{8}.*\.pdf$', file):
                                    date_part = re.search(r'\d{8}', file).group()  # Extract the date part of the file name
                                    try:
                                        datetime.strptime(date_part, '%Y%m%d')  # Check if the date part is a valid date
                                        status = "YES"
                                        with open(os.path.join(dirpath, file), 'rb') as f:
                                            reader = PdfReader(f)
                                            if is_pdf_signed(os.path.join(dirpath, file)):
                                                status = "SIGNED"
                                                break
                                    except ValueError:
                                        continue  # If the date part is not a valid date, ignore the file
                        pdf_statuses.append(status)
                    if '.git' in os.listdir(repo_path):
                        commit_date, commit_author = get_last_commit_info(repo_path)
                        writer.writerow([folder, codi,  data_inici, commit_date, commit_author] + pdf_statuses)
                    else:
                        writer.writerow([folder, codi, data_inici, "N/A", "N/A"] + pdf_statuses)
            except git.InvalidGitRepositoryError:
                print(f"{folder} is not a valid Git repository. Skipping...")
                continue
            except PermissionError:
                print(f"Permission denied for {folder}. Skipping...")
                continue

def is_pdf_signed(file_path):
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        acro_form = reader.trailer["/Root"].get("/AcroForm", None)
        return acro_form is not None and acro_form.get("/SigFlags", 0) != 0

def extract_field_from_readme(readme_path: str, field: str) -> Optional[str]:
    if not os.path.exists(readme_path+"/README.md"):
        print(f"{readme_path}/README.md Not Found")
        return None

    with open(readme_path+"/README.md", 'r') as f:
        print(f"Reading {readme_path}/README.md ")
        lines = f.readlines()

    for line in lines:
        # If the line starts with the field name, return the rest of the line
        match = re.match(r'^\s*' + re.escape(field), line)
        if match:
            return line[len(match.group()):].strip()

    # If the field was not found in the README.md file, return None
    print(f"{field} Not Found in {readme_path}/README.md ")

    return None
# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')