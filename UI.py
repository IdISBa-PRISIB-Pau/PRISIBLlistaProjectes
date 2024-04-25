import tkinter as tk
from tkinter import filedialog, PhotoImage
import main
import os
import csv
import git as git
from typing import Optional


def browse_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, directory)


def browse_file(entry):
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    entry.delete(0, tk.END)
    entry.insert(0, file)


def run_script(dir_entry, file_entry, write_to_readme, append_to_csv):
    try:
        dir_path = dir_entry.get()
        file_path = file_entry.get()
        if write_to_readme.get():
            main.scan_repos_and_create_csv(dir_path, file_path, ['SSPT', 'PSPT'], append_to_csv.get())
        else:
            main.scan_repos_and_create_csv_no_write(dir_path, file_path, ['SSPT', 'PSPT'], append_to_csv.get())
    except Exception as e:
        print(f"Exception occurred: {e}")


# If the repository is a git repository, we can update the README files
def extract_status_from_readme(repo_path: str) -> Optional[str]:
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='ISO-8859-1') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip() == "### Status":
                    return lines[i+1].strip() if i+1 < len(lines) else None
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

root = tk.Tk()
root.geometry('800x600')  # Adjust the dimensions as needed

logo = PhotoImage(file="logo.png")  # Replace with the path to your logo
logo_label = tk.Label(root, image=logo)
logo_label.pack(side=tk.RIGHT)

dir_label = tk.Label(root, text="Enter directory path:", font=("Arial", 14))
dir_label.pack()

dir_entry = tk.Entry(root, width=50)
dir_entry.insert(0, "C:/Users/Pau/Documents")  # Insert the default directory path
dir_entry.pack()

dir_browse_button = tk.Button(root, text="Browse", command=lambda: browse_directory(dir_entry))
dir_browse_button.pack()

file_label = tk.Label(root, text="Enter output file name:", font=("Arial", 14))
file_label.pack()

file_entry = tk.Entry(root, width=50)
file_entry.insert(0, "C:/Users/Pau/Documents/Projectes.csv")  # Insert the default directory path
file_entry.pack()

file_browse_button = tk.Button(root, text="Browse", command=lambda: browse_file(file_entry))
file_browse_button.pack()

write_to_readme = tk.BooleanVar()
write_to_readme.set(False)  # Default value

write_checkbox = tk.Checkbutton(root, text="Write to README.md", variable=write_to_readme)
write_checkbox.pack()

append_to_csv = tk.BooleanVar()
append_to_csv.set(False)  # Default value

append_checkbox = tk.Checkbutton(root, text="Append to CSV", variable=append_to_csv)
append_checkbox.pack()

run_button = tk.Button(root, text="Run Script",
                       command=lambda: run_script(dir_entry, file_entry, write_to_readme, append_to_csv))
run_button.pack()

readme_button = tk.Button(root, text="Update Status in Readme",
                          command=lambda: update_readme_files_from_csv(csv_file=file_entry.get(),
                                                                       dir_path=dir_entry.get()))
readme_button.pack()

root.mainloop()
