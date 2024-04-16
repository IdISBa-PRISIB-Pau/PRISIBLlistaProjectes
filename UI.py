import tkinter as tk
from tkinter import filedialog
import main
import os
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

def run_script(dir_entry, file_entry):
    dir_path = dir_entry.get()
    file_path = file_entry.get()
    main.scan_repos_and_create_csv(dir_path, file_path)

root = tk.Tk()

dir_label = tk.Label(root, text="Enter directory path:")
dir_label.pack()

dir_entry = tk.Entry(root)
dir_entry.insert(0, "C:/Users/Pau/Documents")  # Insert the default directory path
dir_entry.pack()

dir_browse_button = tk.Button(root, text="Browse", command=lambda: browse_directory(dir_entry))
dir_browse_button.pack()

file_label = tk.Label(root, text="Enter output file name:")
file_label.pack()

file_entry = tk.Entry(root)
file_entry.insert(0, "C:/Users/Pau/Documents/Projectes.csv")  # Insert the default directory path
file_entry.pack()

file_browse_button = tk.Button(root, text="Browse", command=lambda: browse_file(file_entry))
file_browse_button.pack()

run_button = tk.Button(root, text="Run Script", command=lambda: run_script(dir_entry, file_entry))
run_button.pack()

root.mainloop()