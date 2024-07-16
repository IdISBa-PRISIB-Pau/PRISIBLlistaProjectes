import tkinter as tk
from tkinter import ttk, filedialog
import csv
import os
import main  # Import the main module

def browse_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, directory)

def browse_file(entry):
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    entry.delete(0, tk.END)
    entry.insert(0, file)

def load_csv_data(csv_file):
    data = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)
        for row in reader:
            data.append(row)
    return headers, data

def save_csv_data(csv_file, headers, data):
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

def on_cell_double_click(event):
    item = tree.selection()[0]
    column = tree.identify_column(event.x)
    col_index = int(column.replace('#', '')) - 1
    entry = tk.Entry(root)
    entry.insert(0, tree.item(item, 'values')[col_index])
    entry.place(x=event.x_root, y=event.y_root)
    entry.focus()

    def on_entry_confirm(event):
        new_value = entry.get()
        tree.set(item, column, new_value)
        entry.destroy()

    entry.bind('<Return>', on_entry_confirm)

def on_save_button_click():
    data = []
    for row_id in tree.get_children():
        row = tree.item(row_id)['values']
        data.append(row)
    save_csv_data(file_entry.get(), headers, data)
    main.update_readme_files_from_csv(dir_entry.get(), file_entry.get())  # Call the existing function

root = tk.Tk()
root.geometry('800x600')

dir_label = tk.Label(root, text="Enter directory path:", font=("Arial", 14))
dir_label.pack()

dir_entry = tk.Entry(root, width=50)
dir_entry.insert(0, "C:/Users/Pau/Documents")
dir_entry.pack()
dir_browse_button = tk.Button(root, text="Browse", command=lambda: browse_directory(dir_entry))
dir_browse_button.pack()

file_label = tk.Label(root, text="Enter output file name:", font=("Arial", 14))
file_label.pack()

file_entry = tk.Entry(root, width=50)
file_entry.insert(0, "C:/Users/Pau/Documents/Projectes.csv")
file_entry.pack()

file_browse_button = tk.Button(root, text="Browse", command=lambda: browse_file(file_entry))
file_browse_button.pack()

load_button = tk.Button(root, text="Load Data", command=lambda: load_data())
load_button.pack()

tree = ttk.Treeview(root)
tree.pack(expand=True, fill='both')

def load_data():
    global headers
    headers, data = load_csv_data(file_entry.get())
    tree['columns'] = headers
    tree.heading('#0', text='Index')
    tree.column('#0', width=50)
    for header in headers:
        tree.heading(header, text=header)
        tree.column(header, width=100)
    for i, row in enumerate(data):
        tree.insert('', 'end', text=i, values=row)
    tree.bind('<Double-1>', on_cell_double_click)

save_button = tk.Button(root, text="Save Changes", command=on_save_button_click)
save_button.pack()

root.mainloop()