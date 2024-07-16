import tkinter as tk
import main as main
from tkinter import filedialog, PhotoImage

def browse_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, directory)


def browse_file(entry):
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    entry.delete(0, tk.END)
    entry.insert(0, file)


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
                       command=lambda: main.run_script(dir_entry, file_entry, write_to_readme, append_to_csv))
run_button.pack()

readme_button = tk.Button(root, text="Update Status in Readme",
                          command=lambda: main.update_readme_files_from_csv(csv_file=file_entry.get(),
                                                                       dir_path=dir_entry.get()))
readme_button.pack()

root.mainloop()
