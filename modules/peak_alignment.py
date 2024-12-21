import os

import pandas as pd
from PyQt6.QtCore import QFileSystemWatcher, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.feather_reader import (
    align_peaks,
    process_file,
)  # Import functions from feather_reader


class FileWatcher(QThread):
    directory_changed = pyqtSignal()

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.watcher = QFileSystemWatcher([directory])
        self.watcher.fileChanged.connect(self.on_file_changed)
        self.watcher.directoryChanged.connect(self.on_directory_changed)

    def on_file_changed(self, path):
        if path.endswith(".feather"):
            self.directory_changed.emit()

    def on_directory_changed(self, path):
        self.directory_changed.emit()

    def run(self):
        self.exec()


class PeakAlignment(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.directory = os.getcwd()  # Use the current working directory
        self.file_watcher = FileWatcher(self.directory)  # Initialize file_watcher
        self.file_watcher.directory_changed.connect(self.import_processed_files)
        self.file_watcher.start()

        # Store imported data arrays
        self.data_arrays = []

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

        # Create drift tolerance labels and input fields
        self.rt_drift_label = QLabel("Drift Tolerance: ±")
        self.ccs_drift_label = QLabel("Drift Tolerance: ±")
        self.mz_drift_label = QLabel("Drift Tolerance: ±")
        self.rt_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.ccs_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.mz_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px; text-align: center;"
        )
        self.rt_drift_input = QLineEdit()
        self.ccs_drift_input = QLineEdit()
        self.mz_drift_input = QLineEdit()

        # Create grid layout for input fields and drift tolerance
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.rt_label, 0, 0)
        grid_layout.addWidget(self.rt_input, 0, 1)
        grid_layout.addWidget(self.rt_min_label, 0, 2)
        grid_layout.addWidget(self.rt_drift_label, 1, 0)
        grid_layout.addWidget(self.rt_drift_input, 1, 1)

        grid_layout.addWidget(self.ccs_label, 0, 3)
        grid_layout.addWidget(self.ccs_input, 0, 4)
        grid_layout.addWidget(self.ccs_min_label, 0, 5)
        grid_layout.addWidget(self.ccs_drift_label, 1, 3)
        grid_layout.addWidget(self.ccs_drift_input, 1, 4)

        grid_layout.addWidget(self.mz_label, 0, 6)
        grid_layout.addWidget(self.mz_input, 0, 7)
        grid_layout.addWidget(self.mz_min_label, 0, 8)
        grid_layout.addWidget(self.mz_drift_label, 1, 6)
        grid_layout.addWidget(self.mz_drift_input, 1, 7)

        # Create file list
        self.file_list = QListWidget()

        # Create buttons
        refresh_button = QPushButton("Refresh Processed Files")
        align_button = QPushButton("Trigger Align Peaks Algorithm")

        # Connect buttons
        refresh_button.clicked.connect(self.import_processed_files)
        align_button.clicked.connect(self.trigger_align_peaks)

        # Add widgets to layout
        main_layout.addWidget(header_label)
        main_layout.addLayout(grid_layout)
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
        self.rt_drift_input.setFixedWidth(new_width)
        self.ccs_drift_input.setFixedWidth(new_width)
        self.mz_drift_input.setFixedWidth(new_width)

        # Set the width of the labels to be a fixed distance less than the input fields, but not less than 30 pixels
        label_width = max(new_width - 75, 30)
        self.rt_label.setFixedWidth(label_width)
        self.ccs_label.setFixedWidth(label_width)
        self.mz_label.setFixedWidth(label_width)
        self.rt_drift_label.setFixedWidth(label_width)
        self.ccs_drift_label.setFixedWidth(label_width)
        self.mz_drift_label.setFixedWidth(label_width)

        # Set the width of the (min) labels to be the same as the input fields
        self.rt_min_label.setFixedWidth(new_width)
        self.ccs_min_label.setFixedWidth(new_width)
        self.mz_min_label.setFixedWidth(new_width)

    def process_file(self, file_path):
        print(f"Processing file: {file_path}")
        try:
            df = pd.read_feather(file_path)
            print(df.head())  # Print the first few rows of the dataframe for debugging
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            # Debugging statement

    def import_processed_files(self):
        temp_folder = os.path.join(self.directory, ".temp")
        self.data_arrays = []  # Clear previous data arrays
        if os.path.exists(temp_folder):
            self.file_list.clear()
            files = os.listdir(temp_folder)
            for file_name in files:
                if file_name.endswith(".feather"):
                    full_path = os.path.join(temp_folder, file_name)
                    self.file_list.addItem(full_path)
                    data_array = process_file(full_path)  # Use imported function
                    if data_array is not None:
                        self.data_arrays.append(data_array)
        else:
            print(f".temp folder does not exist: {temp_folder}")

    def trigger_align_peaks(self):
        if not self.data_arrays:
            print(
                "No data arrays available for alignment. Please import processed files first."
            )
            return

        align_peaks(self.data_arrays)  # Use imported function
