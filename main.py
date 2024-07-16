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


def scan_repos_and_create_csv(dir_path: str, csv_file: str, pdf_prefixes: list = None, append_to_csv: bool = False):
    if pdf_prefixes is None:
        pdf_prefixes = ['SSPT','PSPT']

    with open(csv_file, 'a' if append_to_csv else 'w', newline='',encoding='utf-8') as file:
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
            folder = os.fsdecode(folder)
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    if codi is not None:
                        codi = codi.replace("PRISIB","").strip()  # Strip the "PRISIB" prefix
                        codi = codi.replace(" ","").strip()  # Strip the "PRISIB" prefix
                    else:
                        codi_parts = os.path.basename(repo_path).split("-")
                        if len(codi_parts) > 1:
                            codi = codi_parts[1].strip()
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

    with open(csv_file, 'a' if append_to_csv else 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not append_to_csv:
            writer.writerow(["Folder Name", "Codi", "Status", "Sol·licitant", "Correu", "Data Inici", "Last Commit Date",
                            "Last Commit Author", "Last Commit msg"] + pdf_prefixes + ["Dictamen_CEI", "Data Model",
                                                                                    "data_model",
                                                                                    "dictamen_cei", "solicitud",
                                                                                    "pressupost"])
        for folder in os.listdir(dir_path):
            folder = os.fsdecode(folder)
            repo_path = os.path.join(dir_path, folder)
            try:
                if os.path.isdir(repo_path):
                    codi = extract_field_from_readme(repo_path, "- Codi:")
                    if codi is not None:
                        codi = codi.replace("PRISIB", "").strip()  # Strip the "PRISIB" prefix
                        codi = codi.replace(" ", "").strip()  # Strip the "PRISIB" prefix
                    else:
                        codi_parts = os.path.basename(repo_path).split("-")
                        if len(codi_parts) > 1:
                            codi = codi_parts[1].strip()
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
    encodings = ['windows-1252', 'utf-8', 'ISO-8859-1']  # Add more encodings if needed
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
        except FileNotFoundError:
            print(f"{readme_path} Not Found")
            return None
    return None



def extract_status_from_readme(repo_path: str) -> Optional[str]:
    readme_path = os.path.join(repo_path, 'README.md')
    encodings = ['windows-1252', 'utf-8', 'ISO-8859-1']  # Add more encodings if needed
    for encoding in encodings:
        try:
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if line.strip() == "### Status":
                            return lines[i+1].strip() if i+1 < len(lines) else None

        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"{readme_path} Not Found")
            return None

def update_readme_files_from_csv(dir_path: str, csv_file: str):
    encodings = ['utf-8', 'ISO-8859-1', 'windows-1252']
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
                                break
                            except UnicodeDecodeError:
                                continue
                break
        except UnicodeDecodeError:
            continue

# Usage
# scan_repos_and_create_csv('/path/to/your/folder', 'output.csv')