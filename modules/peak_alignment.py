import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QLineEdit,
)
from PyQt6.QtCore import QThread, pyqtSignal, QFileSystemWatcher
import pandas as pd
from modules.feather_reader import feather_reader


class FileWatcher(QThread):
    directory_changed = pyqtSignal()

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.watcher = QFileSystemWatcher([directory])
        self.watcher.fileChanged.connect(self.on_file_changed)
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        print(
            f"FileWatcher initialized for directory: {directory}"
        )  # Debugging statement

    def on_file_changed(self, path):
        if path.endswith(".feather"):
            print(f"File changed detected: {path}")  # Debugging statement
            self.directory_changed.emit()

    def on_directory_changed(self, path):
        print(f"Directory changed detected: {path}")  # Debugging statement
        self.directory_changed.emit()

    def run(self):
        print("FileWatcher thread started")  # Debugging statement
        self.exec()


class PeakAlignment(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.directory = os.getcwd()  # Use the current working directory
        self.file_watcher = FileWatcher(self.directory)  # Initialize file_watcher
        self.file_watcher.directory_changed.connect(self.import_processed_files)
        self.file_watcher.start()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Create header label
        header_label = QLabel("Peak Alignment")
        header_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
        )

        # Create input fields for RT, CCS, and m/z
        self.rt_input = QLineEdit()
        self.ccs_input = QLineEdit()
        self.mz_input = QLineEdit()

        # Create labels for input fields
        self.rt_label = QLabel("RT: ±")
        self.ccs_label = QLabel("CCS: ±")
        self.mz_label = QLabel("m/z: ±")
        self.rt_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.ccs_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.mz_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )

        # Create (min) labels and CCS unit label
        self.rt_min_label = QLabel("(min)")
        self.ccs_min_label = QLabel("(%)")
        self.mz_min_label = QLabel("(Da)")
        self.rt_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.ccs_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.mz_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )

        # Create horizontal layouts for each label-input pair
        rt_layout = QHBoxLayout()
        rt_layout.addWidget(self.rt_label)
        rt_layout.addWidget(self.rt_input)
        rt_layout.addWidget(self.rt_min_label)

        ccs_layout = QHBoxLayout()
        ccs_layout.addWidget(self.ccs_label)
        ccs_layout.addWidget(self.ccs_input)
        ccs_layout.addWidget(self.ccs_min_label)

        mz_layout = QHBoxLayout()
        mz_layout.addWidget(self.mz_label)
        mz_layout.addWidget(self.mz_input)
        mz_layout.addWidget(self.mz_min_label)

        # Create a main horizontal layout for the input fields
        input_layout = QHBoxLayout()
        input_layout.addLayout(rt_layout)
        input_layout.addLayout(ccs_layout)
        input_layout.addLayout(mz_layout)

        # Create file list
        self.file_list = QListWidget()

        # Create buttons
        refresh_button = QPushButton("Refresh Processed Files")
        align_button = QPushButton("Trigger Align Peaks Algorithm")

        # Connect buttons
        refresh_button.clicked.connect(self.import_processed_files)
        align_button.clicked.connect(self.align_peaks)

        # Add widgets to layout
        main_layout.addWidget(header_label)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.file_list)
        main_layout.addWidget(refresh_button)
        main_layout.addWidget(align_button)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Set the width of the input fields to 10% of the window width
        new_width = int(self.width() * 0.1)
        self.rt_input.setFixedWidth(new_width)
        self.ccs_input.setFixedWidth(new_width)
        self.mz_input.setFixedWidth(new_width)

        # Set the width of the labels to be a fixed distance less than the input fields, but not less than 30 pixels
        label_width = max(new_width - 75, 30)
        self.rt_label.setFixedWidth(label_width)
        self.ccs_label.setFixedWidth(label_width)
        self.mz_label.setFixedWidth(label_width)

        # Set the width of the (min) labels to be the same as the input fields
        self.rt_min_label.setFixedWidth(new_width)
        self.ccs_min_label.setFixedWidth(new_width)
        self.mz_min_label.setFixedWidth(new_width)

    def import_processed_files(self):
        temp_folder = os.path.join(self.directory, ".temp")
        print(f"Current working directory: {os.getcwd()}")  # Debugging statement
        print(f"Checking .temp folder: {temp_folder}")  # Debugging statement
        if os.path.exists(temp_folder):
            self.file_list.clear()
            files = os.listdir(temp_folder)
            for file_name in files:
                if file_name.endswith(".feather"):
                    full_path = os.path.join(temp_folder, file_name)
                    self.file_list.addItem(full_path)
                    self.process_file(full_path)
        else:
            print(f".temp folder does not exist: {temp_folder}")  # Debugging statement

    def process_file(self, file_path):
        print(f"Processing file: {file_path}")
        try:
            df = pd.read_feather(file_path)
            print(df.head())  # Print the first few rows of the dataframe for debugging
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")  # Debugging statement

    def align_peaks(self):
        feather_reader()


if __name__ == "__main__":
    print("Running peak_alignment.py as main script")  # Debugging statement
