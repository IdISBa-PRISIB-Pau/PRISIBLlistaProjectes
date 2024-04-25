import os
import csv
import git as git
from pdfreader import SimplePDFViewer
import re
from datetime import datetime
from git import exc
from typing import Optional
import chardet

class Repository:
    def __init__(self, path):
        self.path = path
        self.statuses = {}
        self.last_commit_info = None

    def check_for_file(self, pattern, status_name):
        try:
            for dirpath, dirnames, filenames in os.walk(self.path):
                for file in filenames:
                    if re.match(pattern, file):
                        self.statuses[status_name] = "YES"
                        if is_pdf_signed(os.path.join(dirpath, file)):
                            self.statuses[status_name] = "SIGNED"
                        return
        except Exception as e:
            print(f"Class Repository Exception in {self.path}. Exception: {str(e)}")

    def get_last_commit_info(self):
        try:
            repo = git.Repo(self.path)
            last_commit = list(repo.iter_commits('master', max_count=1))[0]
            self.last_commit_info = (
            datetime.utcfromtimestamp(last_commit.committed_date).strftime('%Y-%m-%d'),
            last_commit.author.email, last_commit.message.strip())
        except exc.InvalidGitRepositoryError:
            print(f"{self.path} is not a Git repository. Skipping...")
            self.last_commit_info = (None, None, None)

    def extract_field_from_readme(self, field):
        readme_path = os.path.join(self.path, 'README.md')
        try:
            with open(readme_path, 'rb') as f:
                result = chardet.detect(f.read())
            with open(readme_path, 'r', encoding=result['encoding']) as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if field.lower() in line.lower():
                        if field.lower() == '### status':
                            return lines[i + 1].strip() if i + 1 < len(lines) else None
                        else:
                            return line.split(':', 1)[1].strip() if ':' in line else None
        except UnicodeDecodeError:
            print(f"Could not decode {readme_path} with the detected encoding.")
        except FileNotFoundError:
            print(f"{readme_path} Not Found")
        return None

    def update_status_in_readme(self, status):
        readme_path = os.path.join(self.path, 'README.md')
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                status_exists = any(line.strip() == "### Status" for line in lines)
                if status_exists:
                    for i, line in enumerate(lines):
                        if line.strip() == "### Status":
                            if status is not None:
                                if i + 1 < len(lines):
                                    lines[i + 1] = status + '\n\n'
                                else:
                                    lines.append(status + '\n\n')
                            break
                else:
                    if status is not None:
                        lines.insert(2, "### Status\n")
                        lines.insert(3, status + '\n\n')
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            except PermissionError:
                print(f"Do not have write permissions for {readme_path}. Skipping...")
        else:
            print(f"{readme_path} does not exist. Skipping...")



def is_pdf_signed(file_path):
    try:
        with open(file_path, 'rb') as fd:
            viewer = SimplePDFViewer(fd)
            if viewer.doc.is_encrypted:
                print(f"PDF file at {file_path} is encrypted. Skipping...")
                return False
            acro_form = viewer.doc.catalog['AcroForm'] if 'AcroForm' in viewer.doc.catalog else None
            return acro_form is not None and acro_form.get("SigFlags", 0) != 0
    except Exception as e:
        print(f"Exception occurred when checking signature in PDF file at {file_path}. Exception: {str(e)}. Skipping...")
        return False

def scan_repos_and_create_csv(dir_path: str, csv_file: str, write_to_readme: bool, append_to_csv: bool):
    mode = 'a' if append_to_csv else 'w'
    with open(csv_file, mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        headers = ['Folder', 'Codi', 'Project Status', 'Nom', 'Email', 'Data Inici', 'Last Commit Date',
                   'Last Commit Author', 'Last Commit Message', 'SSPT Status', 'PSPT Status', 'CEIM Status',
                   'Data Model Status', 'Data Model', 'Dictamen CEI', 'Solicitud', 'Pressupost']
        if mode == 'w':
            writer.writerow(headers)
        for folder in os.listdir(dir_path):
            try:
                repo_path = os.path.join(dir_path, folder)
                if os.path.isdir(repo_path):
                    repo = Repository(repo_path)
                    repo.check_for_file(r'^.*SSPT.*\.pdf$', 'SSPT Status')
                    repo.check_for_file(r'^.*PSPT.*\.pdf$', 'PSPT Status')
                    repo.check_for_file(r'^.*Dictamen_CEI.*\.pdf$', 'CEIM Status')
                    repo.check_for_file(r'^.*Data Model.*\.xlsx$', 'Data Model Status')
                    repo.get_last_commit_info()
                    row = [folder, repo.extract_field_from_readme('- Codi:'), repo.extract_field_from_readme('### Status'),
                           repo.extract_field_from_readme('- Nom:'), repo.extract_field_from_readme('- Correu:'),
                           repo.extract_field_from_readme('- Data inici:')] + list(repo.last_commit_info) + [repo.statuses.get('SSPT Status', 'NO'), repo.statuses.get('PSPT Status', 'NO'),
                           repo.statuses.get('CEIM Status', 'NO'), repo.statuses.get('Data Model Status', 'NO'),
                           repo.extract_field_from_readme('- Data Model:'), repo.extract_field_from_readme('- Dictamen CEI:'),
                           repo.extract_field_from_readme('- Sol·licitud:'), repo.extract_field_from_readme('- Pressupost:')]
                    writer.writerow(row)
                    if write_to_readme:
                        repo.update_status_in_readme(repo.extract_field_from_readme('Project Status'))
            except Exception as e:
                print(f"Exception occurred when processing folder {folder}. Exception: {str(e)}")




def update_readme_files_from_csv(dir_path: str, csv_file: str):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)
        status_index = headers.index("Status")
        for row in reader:
            folder = row[0]
            status = row[status_index]
            repo_path = os.path.join(dir_path, folder)
            if os.path.isdir(repo_path):
                repo = Repository(repo_path)
                repo.update_status_in_readme(status)




def run_script(dir_entry, file_entry, write_to_readme, append_to_csv):
    try:
        dir_path = dir_entry.get()
        file_path = file_entry.get()
        scan_repos_and_create_csv(dir_path, file_path, write_to_readme.get(), append_to_csv.get())
    except Exception as e:
        print(f"Exception occurred: {e}")


# If the repository is a git repository, we can update the README files
def extract_field_from_readme(self, field):
    readme_path = os.path.join(self.path, 'README.md')
    try:
        with open(readme_path, 'rb') as f:
            result = chardet.detect(f.read())
        with open(readme_path, 'r', encoding=result['encoding']) as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if field in line:
                    if field == '### Status':
                        return lines[i + 1].strip() if i + 1 < len(lines) else None
                    else:
                        return line.split(':', 1)[1].strip()
    except UnicodeDecodeError:
        print(f"Could not decode {readme_path} with the detected encoding.")
    except FileNotFoundError:
        print(f"{readme_path} Not Found")
    return None


def update_readme_files_from_csv(dir_path: str, csv_file: str):
    encodings = ['utf-8', 'ISO-8859-1', 'windows-1252']  # Add more encodings if needed
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as file:
                reader = csv.reader(file)
                headers = next(reader)
                status_index = headers.index("Status")
                for row in reader:
                    folder = row[0]
                    status = row[status_index]
                    readme_path = os.path.join(dir_path, folder, 'README.md')
                    if os.path.exists(readme_path):
                        for readme_encoding in encodings:
                            try:
                                with open(readme_path, 'r', encoding=readme_encoding) as f:
                                    lines = f.readlines()
                                status_exists = any(line.strip() == "### Status" for line in lines)
                                if status_exists:
                                    for i, line in enumerate(lines):
                                        if line.strip() == "### Status":
                                            if status is not None:  # Check if status is not None
                                                if i + 1 < len(lines):
                                                    lines[i + 1] = status + '\n\n'
                                                else:
                                                    lines.append(status + '\n\n')
                                            break
                                else:
                                    if status is not None:  # Check if status is not None
                                        lines.insert(2, "### Status\n")
                                        lines.insert(3, status + '\n\n')
                                with open(readme_path, 'w', encoding='utf-8') as f:
                                    f.writelines(lines)
                                break
                            except UnicodeDecodeError:
                                continue
                break
        except UnicodeDecodeError:
            continue
# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')