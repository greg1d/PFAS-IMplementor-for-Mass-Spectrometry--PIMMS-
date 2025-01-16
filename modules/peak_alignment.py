import os

import pandas as pd
from PyQt6.QtCore import QFileSystemWatcher, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from modules.Align_peaks_algorithm import align_peaks, process_file


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
        self.file_watcher.start()

        # Store imported data arrays
        self.data_arrays = []
        self.file_paths = []  # Store file paths

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Create header label
        header_label = QLabel("Peak Alignment")
        header_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
        )

        # Create input fields for RT, CCS, and m/z with reduced width
        self.rt_input = QLineEdit()
        self.rt_input.setFixedWidth(100)

        self.ccs_input = QLineEdit()
        self.ccs_input.setFixedWidth(100)

        self.mz_input = QLineEdit()
        self.mz_input.setFixedWidth(100)

        # Create labels for input fields
        self.rt_label = QLabel("RT: ±")
        self.ccs_label = QLabel("CCS: ±")
        self.mz_label = QLabel("m/z: ±")

        # Right-align the labels
        self.rt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ccs_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.mz_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rt_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.ccs_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.mz_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )

        # Create (min) labels and CCS unit label
        self.rt_min_label = QLabel("(min)")
        self.ccs_min_label = QLabel("(%)")
        self.mz_min_label = QLabel("(Da)")
        self.rt_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.ccs_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.mz_min_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )

        # Create drift tolerance labels and input fields with reduced width
        self.rt_drift_label = QLabel("Drift Tolerance: ±")
        self.ccs_drift_label = QLabel("Drift Tolerance: ±")
        self.mz_drift_label = QLabel("Drift Tolerance: ±")

        self.rt_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.ccs_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.mz_drift_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )

        # Create question mark buttons for tooltips
        self.rt_drift_tooltip_button = QPushButton("?")
        self.rt_drift_tooltip_button.setFixedSize(20, 20)
        self.rt_drift_tooltip_button.setStyleSheet(
            "background-color: lightgray; border-radius: 10px;"
        )
        self.rt_drift_tooltip_button.clicked.connect(
            lambda: self.show_tooltip(
                self.rt_drift_label, "Enter the drift tolerance for RT."
            )
        )

        self.ccs_drift_tooltip_button = QPushButton("?")
        self.ccs_drift_tooltip_button.setFixedSize(20, 20)
        self.ccs_drift_tooltip_button.setStyleSheet(
            "background-color: lightgray; border-radius: 10px;"
        )
        self.ccs_drift_tooltip_button.clicked.connect(
            lambda: self.show_tooltip(
                self.ccs_drift_label, "Enter the drift tolerance for CCS."
            )
        )

        self.mz_drift_tooltip_button = QPushButton("?")
        self.mz_drift_tooltip_button.setFixedSize(20, 20)
        self.mz_drift_tooltip_button.setStyleSheet(
            "background-color: lightgray; border-radius: 10px;"
        )
        self.mz_drift_tooltip_button.clicked.connect(
            lambda: self.show_tooltip(
                self.mz_drift_label, "Enter the drift tolerance for m/z."
            )
        )

        self.rt_drift_input = QLineEdit()
        self.rt_drift_input.setFixedWidth(100)

        self.ccs_drift_input = QLineEdit()
        self.ccs_drift_input.setFixedWidth(100)

        self.mz_drift_input = QLineEdit()
        self.mz_drift_input.setFixedWidth(100)

        # Create unit labels for drift tolerance
        self.rt_drift_unit_label = QLabel("(unit)")
        self.ccs_drift_unit_label = QLabel("(unit)")
        self.mz_drift_unit_label = QLabel("(unit)")
        self.rt_drift_unit_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.ccs_drift_unit_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )
        self.mz_drift_unit_label.setStyleSheet(
            "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 12px;"
        )

        # Create grid layout for input fields and drift tolerance
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(5)
        grid_layout.setVerticalSpacing(5)
        grid_layout.addWidget(self.rt_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.rt_input, 0, 1)
        grid_layout.addWidget(self.rt_min_label, 0, 2, Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(self.rt_drift_label, 1, 0, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.rt_drift_input, 1, 1)
        grid_layout.addWidget(
            self.rt_drift_unit_label, 1, 2, Qt.AlignmentFlag.AlignLeft
        )
        grid_layout.addWidget(self.rt_drift_tooltip_button, 1, 3)

        grid_layout.addWidget(self.ccs_label, 0, 3, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.ccs_input, 0, 4)
        grid_layout.addWidget(self.ccs_min_label, 0, 5, Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(self.ccs_drift_label, 1, 3, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.ccs_drift_input, 1, 4)
        grid_layout.addWidget(
            self.ccs_drift_unit_label, 1, 5, Qt.AlignmentFlag.AlignLeft
        )
        grid_layout.addWidget(self.ccs_drift_tooltip_button, 1, 6)

        grid_layout.addWidget(self.mz_label, 0, 6, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.mz_input, 0, 7)
        grid_layout.addWidget(self.mz_min_label, 0, 8, Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(self.mz_drift_label, 1, 6, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.mz_drift_input, 1, 7)
        grid_layout.addWidget(
            self.mz_drift_unit_label, 1, 8, Qt.AlignmentFlag.AlignLeft
        )
        grid_layout.addWidget(self.mz_drift_tooltip_button, 1, 9)

        # Create file list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )  # Allow multiple selection

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

    def show_tooltip(self, label, text):
        QToolTip.showText(label.mapToGlobal(label.rect().bottomRight()), text)

    def process_file(self, file_path):
        print(f"Processing file: {file_path}")
        try:
            df = pd.read_feather(file_path)
            print(df.head())  # Print the first few rows of the dataframe for debugging
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    def import_processed_files(self):
        temp_folder = os.path.join(self.directory, ".temp")
        self.data_arrays = []  # Clear previous data arrays
        self.file_paths = []  # Clear previous file paths
        if os.path.exists(temp_folder):
            self.file_list.clear()
            files = os.listdir(temp_folder)
            for file_name in files:
                if file_name.endswith(".feather"):
                    full_path = os.path.join(temp_folder, file_name)
                    self.file_list.addItem(full_path)
                    data_array = process_file(full_path)
                    if data_array is not None:
                        self.data_arrays.append(data_array)
                        self.file_paths.append(full_path)  # Store file path
        else:
            print(f".temp folder does not exist: {temp_folder}")

    def trigger_align_peaks(self):
        selected_items = self.file_list.selectedItems()
        selected_file_paths = [item.text() for item in selected_items]

        if not selected_file_paths:
            print("No file paths selected for alignment. Please select files first.")
            return

        rt_tolerance = float(self.rt_input.text())
        ccs_tolerance = float(self.ccs_input.text())
        mz_tolerance = float(self.mz_input.text())

        align_peaks(selected_file_paths, rt_tolerance, ccs_tolerance, mz_tolerance)
