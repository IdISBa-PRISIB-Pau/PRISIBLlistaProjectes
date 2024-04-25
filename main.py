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
    return last_commit.committed_datetime, last_commit.author.name, last_commit.message

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


def scan_repos_and_create_csv(dir_path: str, csv_file: str, pdf_prefixes: list = None, append_to_csv: bool = False):
    if pdf_prefixes is None:
        pdf_prefixes = ['SSPT','PSPT']

    with open(csv_file, 'a' if append_to_csv else 'w', newline='') as file:
        writer = csv.writer(file)
        if not append_to_csv:
            writer.writerow(["Folder Name", "Codi", "Status", "Sol·licitant", "Correu", "Data Inici", "Last Commit Date",
                             "Last Commit Author", "Last Commit msg"] + pdf_prefixes + ["Dictamen_CEI",
                                                                                                  "Data Model",
                                                                                                  "data_model",
                                                                                                  "dictamen_cei",
                                                                                                  "solicitud",
                                                                                                  "pressupost"])
        for folder in os.listdir(dir_path):
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    if codi is not None:
                        codi = codi.replace("PRISIB","").strip()  # Strip the "PRISIB" prefix
                        codi = codi.replace(" ","").strip()  # Strip the "PRISIB" prefix
                    data_inici = extract_field_from_readme(repo_path, "- Data inici:")
                    data_model = extract_field_from_readme(repo_path, "- Data Model:")
                    dictamen_cei = extract_field_from_readme(repo_path, "- Dictamen CEIB:")
                    solicitud = extract_field_from_readme(repo_path, "- Sol·licitud:")
                    pressupost = extract_field_from_readme(repo_path, "- Pressupost:")
                    nom = extract_field_from_readme(repo_path, "- Nom:")
                    email = extract_field_from_readme(repo_path, "- Correu:")
                    project_status = extract_status_from_readme(repo_path)
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
                                            if prefix == 'SSPT':
                                                solicitud = file
                                            if prefix == 'PSPT':
                                                pressupost = file
                                            if is_pdf_signed(os.path.join(dirpath, file)):
                                                status = "SIGNED"
                                            # Write the filename to the README.md file
                                            with open(os.path.join(repo_path, 'README.md'), 'r', encoding='utf-8') as readme_file:
                                                lines = readme_file.readlines()
                                            with open(os.path.join(repo_path, 'README.md'), 'w', encoding='utf-8') as readme_file:
                                                if prefix == 'SSPT':
                                                    pattern = re.compile(".*- Sol.?licitud: ")
                                                if prefix == 'PSPT':
                                                    pattern = re.compile(".*- Pressupost: ")
                                                for line in lines:
                                                    if pattern.match(line) and file not in line:
                                                        line = line.strip() + ' ' + file + '\n'
                                                    readme_file.write(line)
                                        except ValueError:
                                            continue
                        pdf_statuses.append(status)
                    # Check for dictamen ceim file
                    ceim_status = "NO"
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        for file in filenames:
                            if re.match(r'^.*Dictamen_CEI.*\.pdf$', file) and os.path.exists(os.path.join(repo_path, 'README.md')):
                                ceim_status = "YES"
                                dictamen_cei = file
                                if is_pdf_signed(os.path.join(dirpath, file)):
                                    ceim_status = "SIGNED"
                                    # Write the filename to the README.md file
                                with open(os.path.join(repo_path, 'README.md'), 'r',
                                              encoding='utf-8') as readme_file:
                                    lines = readme_file.readlines()
                                with open(os.path.join(repo_path, 'README.md'), 'w',
                                              encoding='utf-8') as readme_file:
                                    for line in lines:
                                        if "Dictamen CEI" in line and file not in line:
                                            line = line + ' ' + file + '\n'
                                        readme_file.write(line)
                                break
                    # Check for Data Model xlsx file
                    data_model_status = "NO"
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        if codi is not None:
                            for file in filenames:
                                if file.endswith('.xlsx') and 'Data Model' in file and codi in file:
                                    data_model_status = "YES"
                                    data_model = file
                                    with open(os.path.join(repo_path, 'README.md'), 'r', encoding='utf-8') as readme_file:
                                        lines = readme_file.readlines()
                                    with open(os.path.join(repo_path, 'README.md'), 'w', encoding='utf-8') as readme_file:
                                        pattern = re.compile(".*- Data Model:.*")
                                        for line in lines:
                                            if pattern.match(line) and file not in line:
                                                line = line + ' ' + file + '\n'
                                            readme_file.write(line)
                                    break
                    last_commit_date, last_commit_author, last_commit_msg = get_last_commit_info(repo_path)
                    writer.writerow(
                        [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author, last_commit_msg] + pdf_statuses + [
                            ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
            except git.InvalidGitRepositoryError:
                print(f"{folder} is not a valid Git repository. Skipping...")
                last_commit_date, last_commit_author, last_commit_msg = None, None, None
                writer.writerow(
                    [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author,
                     last_commit_msg] + pdf_statuses + [
                        ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
                continue
            except PermissionError:
                print(f"Permission denied for {folder}. Skipping...")
                writer.writerow(
                    [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author,
                     last_commit_msg] + pdf_statuses + [
                        ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
                continue
def scan_repos_and_create_csv_no_write(dir_path: str, csv_file: str, pdf_prefixes: list = None, append_to_csv: bool = False):
    # This function is similar to scan_repos_and_create_csv, but it doesn't write to the README.md files
    # Copy the body of scan_repos_and_create_csv here, but remove or comment out the parts that write to the README.md files
    if pdf_prefixes is None:
        pdf_prefixes = ['SSPT','PSPT']

    with open(csv_file, 'a' if append_to_csv else 'w', newline='') as file:
        writer = csv.writer(file)
        if not append_to_csv:
            writer.writerow(["Folder Name", "Codi", "Status", "Sol·licitant", "Correu", "Data Inici", "Last Commit Date",
                            "Last Commit Author", "Last Commit msg"] + pdf_prefixes + ["Dictamen_CEI", "Data Model",
                                                                                    "data_model",
                                                                                    "dictamen_cei", "solicitud",
                                                                                    "pressupost"])
        for folder in os.listdir(dir_path):
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    if codi is not None:
                        codi = codi.replace("PRISIB", "").strip()  # Strip the "PRISIB" prefix
                        codi = codi.replace(" ", "").strip()  # Strip the "PRISIB" prefix
                    else:
                        print(f"No 'Codi' field found in README.md for {repo_path}")
                    data_inici = extract_field_from_readme(repo_path, "- Data inici:")
                    data_model = extract_field_from_readme(repo_path, "- Data Model:")
                    dictamen_cei = extract_field_from_readme(repo_path, "- Dictamen CEIB:")
                    solicitud = extract_field_from_readme(repo_path, "- Sol·licitud:")
                    pressupost = extract_field_from_readme(repo_path, "- Pressupost:")
                    nom = extract_field_from_readme(repo_path, "	- Nom:")
                    email = extract_field_from_readme(repo_path, "	- Correu:")
                    project_status = extract_status_from_readme(repo_path)
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
                                            if prefix == 'SSPT':
                                                solicitud = file
                                            if prefix == 'PSPT':
                                                pressupost = file
                                            if is_pdf_signed(os.path.join(dirpath, file)):
                                                status = "SIGNED"
                                        except ValueError:
                                            continue
                        pdf_statuses.append(status)
                    # Check for dictamen ceim file
                    ceim_status = "NO"
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        for file in filenames:
                            if re.match(r'^.*Dictamen_CEI.*\.pdf$', file) and os.path.exists(os.path.join(repo_path, 'README.md')):
                                ceim_status = "YES"
                                dictamen_cei = file
                                if is_pdf_signed(os.path.join(dirpath, file)):
                                    ceim_status = "SIGNED"
                                break
                    # Check for Data Model xlsx file
                    data_model_status = "NO"
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        if codi is not None:
                            for file in filenames:
                                if file.endswith('.xlsx') and 'Data Model' in file and codi in file:
                                    data_model_status = "YES"
                                    data_model = file
                                    break
                    last_commit_date, last_commit_author, last_commit_msg = get_last_commit_info(repo_path)
                    writer.writerow(
                        [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author,
                         last_commit_msg] + pdf_statuses + [
                            ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
            except git.InvalidGitRepositoryError:
                print(f"{folder} is not a valid Git repository. Skipping...")
                last_commit_date, last_commit_author, last_commit_msg = None, None, None
                writer.writerow(
                    [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author,
                     last_commit_msg] + pdf_statuses + [
                        ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
                continue
            except PermissionError:
                print(f"Permission denied for {folder}. Skipping...")
                writer.writerow(
                    [folder, codi, project_status, nom, email, data_inici, last_commit_date, last_commit_author,
                     last_commit_msg] + pdf_statuses + [
                        ceim_status, data_model_status, data_model, dictamen_cei, solicitud, pressupost])
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
                    if line.strip().startswith(field):
                        return line[len(field):].replace(':', '').strip()
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"{readme_path} Not Found")
            return None
    print(f"Could not decode {readme_path} with any of the tried encodings.")
    return None



def extract_status_from_readme(repo_path: str) -> Optional[str]:
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='ISO-8859-1') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == "### Status":
                    return lines[i+1].strip() if i+1 < len(lines) else None
    return None

# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')