import tkinter as tk
from tkinter import filedialog, messagebox

def choose_folder():
    folder = filedialog.askdirectory(title="Select folder")
    if folder:
        global example
        example = folder
        lbl.config(text=folder)
        print("example =", example)
    else:
        messagebox.showinfo("No folder", "No folder selected")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Select Folder")
    root.geometry("520x120")
    example = ""  # will hold the selected folder path

    btn = tk.Button(root, text="Choose Folder", command=choose_folder)
    btn.pack(pady=10)

    lbl = tk.Label(root, text="No folder selected", wraplength=500)
    lbl.pack()

    root.mainloop()
