import os
import json
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import ttk
from PIL import Image, ImageTk

# Show the tkinter version
print(f"Tkinter version: {tk.TkVersion}")

CONFIG_FILE = "config.json"
ICON_PATH = r"Application formatting\Icon.png"  # Path to your .png icon file


def browse_folder():
    folder_path = filedialog.askdirectory(title="Select Folder Containing CEF Files")
    return folder_path


def read_cef(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None


def process_cef_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".cef"):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing file: {file_path}")
            content = read_cef(file_path)
            if content:
                # Process the content as needed
                pass


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)


def main():
    config = load_config()
    folder_path = config.get("folder_path")

    def on_select_folder():
        nonlocal folder_path
        folder_path = browse_folder()
        if folder_path:
            config["folder_path"] = folder_path
            save_config(config)
            print(f"Folder path selected: {folder_path}")
            process_cef_files_in_folder(folder_path)
        else:
            print("No folder selected.")

    def on_drop(event):
        files = root.tk.splitlist(event.data)
        for file_path in files:
            if file_path.endswith(".cef"):
                print(f"Processing dropped file: {file_path}")
                content = read_cef(file_path)
                if content:
                    # Process the content as needed
                    file_listbox.insert(tk.END, file_path)

    # Use TkinterDnD for drag-and-drop functionality
    root = TkinterDnD.Tk()
    root.title("PIMMS v1.2")

    # Load and set the icon using Pillow for better quality
    if os.path.exists(ICON_PATH):
        icon_image = Image.open(ICON_PATH)
        icon_photo = ImageTk.PhotoImage(icon_image)
        root.iconphoto(True, icon_photo)

    # Set the theme using ttk.Style
    style = ttk.Style(root)
    style.theme_use("clam")  # You can choose from 'clam', 'alt', 'default', 'classic'

    # Create a notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    # Create the Data Importing page
    data_importing_frame = ttk.Frame(notebook)
    notebook.add(data_importing_frame, text="Data Importing")

    label = ttk.Label(data_importing_frame, text="Drag and drop files here to process")
    label.pack(pady=10)

    drop_area_frame = ttk.Frame(
        data_importing_frame, relief="ridge", width=400, height=200
    )
    drop_area_frame.pack(pady=20, expand=True, fill="both")
    drop_area_frame.pack_propagate(
        False
    )  # Prevent the frame from resizing to fit its contents

    drop_area = ttk.Label(drop_area_frame, text="Drag and drop CEF files here")
    drop_area.pack(expand=True, fill="both")
    drop_area.drop_target_register(DND_FILES)
    drop_area.dnd_bind("<<Drop>>", on_drop)

    file_listbox = tk.Listbox(data_importing_frame, width=50, height=10)
    file_listbox.pack(pady=10, expand=True, fill="both")

    # Create the Sample Treatment page
    sample_treatment_frame = ttk.Frame(notebook)
    notebook.add(sample_treatment_frame, text="Sample Treatment")

    sample_treatment_label = ttk.Label(
        sample_treatment_frame, text="Sample Treatment Page"
    )
    sample_treatment_label.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
