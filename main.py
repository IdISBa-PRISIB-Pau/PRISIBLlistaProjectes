import os
import git
import csv
import re
from datetime import datetime
from PyPDF2 import PdfReader
from endesive import pdf
from typing import Optional

def get_last_commit_info(repo_path: str):
    """
    Get the date and author of the last commit in a Git repository.

    Args:
        repo_path (str): The path to the Git repository.

    Returns:
        tuple: A tuple containing the date and author of the last commit.
    """
    repo = git.Repo(repo_path)
    last_commit = next(repo.iter_commits('master', max_count=1))
    return last_commit.committed_datetime, last_commit.author.name

def extract_readme_lines(repo_path: str, num_lines: int = 5) -> Optional[str]:
    """
    Extract the first few lines from a README.md file in a repository.

    Args:
        repo_path (str): The path to the repository.
        num_lines (int, optional): The number of lines to extract. Defaults to 5.

    Returns:
        Optional[str]: The extracted lines, or None if the README.md file does not exist.
    """
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            return ''.join([next(f) for _ in range(num_lines)])
    return None


def scan_repos_and_create_csv(dir_path: str, csv_file: str, pdf_prefixes: list = None):
    if pdf_prefixes is None:
        pdf_prefixes = ['SSPT','PSPT', 'IMP_Dictamen_CEI']

    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Folder Name", "Codi", "Data Inici", "Last Commit Date", "Last Commit Author"] + pdf_prefixes + ["Data Model"])

        for folder in os.listdir(dir_path):
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    if codi is not None:
                        codi = codi.replace("PRISIB","").strip()  # Strip the "PRISIB" prefix
                        codi = codi.replace(" ","").strip()  # Strip the "PRISIB" prefix
                    data_inici = extract_field_from_readme(repo_path, "- Data inici:")
                    pdf_statuses = []
                    for prefix in pdf_prefixes:
                        status = "NO"
                        for dirpath, dirnames, filenames in os.walk(repo_path):
                            for file in filenames:
                                if prefix in file and os.path.exists(os.path.join(repo_path, 'README.md')):
                                    if re.match(r'^' + prefix + r'.*\d{8}.*\.pdf$', file):
                                        date_part = re.search(r'\d{8}', file).group()
                                        try:
                                            datetime.strptime(date_part, '%Y%m%d')
                                            status = "YES"
                                            if is_pdf_signed(os.path.join(dirpath, file)):
                                                status = "SIGNED"
                                            # Write the filename to the README.md file
                                            with open(os.path.join(repo_path, 'README.md'), 'a') as readme_file:
                                                readme_file.write(f'\n- {prefix}: {file}\n')
                                        except ValueError:
                                            continue
                        pdf_statuses.append(status)
                    # Check for Data Model xlsx file
                    data_model_status = "NO"
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        for file in filenames:
                            if file.endswith('.xlsx') and 'Data Model' in file:
                                data_model_status = "YES"
                                break
                    last_commit_date, last_commit_author = get_last_commit_info(repo_path)
                    writer.writerow([folder, codi, data_inici, last_commit_date, last_commit_author] + pdf_statuses + [
                        data_model_status])
            except git.InvalidGitRepositoryError:
                print(f"{folder} is not a valid Git repository. Skipping...")
                writer.writerow([folder, codi, data_inici, 'not a Git repository', 'not a Git repository'] + pdf_statuses + [
                    data_model_status])
                continue
            except PermissionError:
                print(f"Permission denied for {folder}. Skipping...")
                writer.writerow([folder, codi, data_inici, last_commit_date, last_commit_author] + pdf_statuses + [
                    data_model_status])
                continue

def is_pdf_signed(file_path):
    """
    Check if a PDF file is signed.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        bool: True if the PDF is signed, False otherwise.
    """
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            acro_form = reader.trailer["/Root"].get("/AcroForm", None)
            return acro_form is not None and acro_form.get("/SigFlags", 0) != 0
    except AttributeError:
        print(f"Error reading PDF file at {file_path}. Skipping...")
        return False

def extract_field_from_readme(repo_path: str, field: str) -> Optional[str]:
    readme_path = os.path.join(repo_path, 'README.md')
    encodings = ['utf-8', 'ISO-8859-1', 'windows-1252']  # Add more encodings if needed
    for encoding in encodings:
        try:
            with open(readme_path, 'r', encoding=encoding) as file:
                for line in file:
                    if line.startswith(field):
                        return line[len(field):].strip()
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"{readme_path} Not Found")
            return None
    print(f"Could not decode {readme_path} with any of the tried encodings.")
    return None
# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')