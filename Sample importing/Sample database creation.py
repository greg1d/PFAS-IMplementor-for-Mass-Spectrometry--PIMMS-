from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QIcon
import pandas as pd
import os
import xml.etree.ElementTree as ET
import qdarkstyle


class CEFConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEF to Feather Converter")
        self.setGeometry(300, 300, 400, 200)

        # Set the window icon
        self.setWindowIcon(QIcon("Application formatting/Icon.png"))

        self.label = QLabel("Upload CEF files to convert to Feather format.")
        self.button_upload = QPushButton("Select Files")
        self.button_convert = QPushButton("Convert to Feather")
        self.button_convert.setEnabled(False)
        self.status = QLabel("Status: Waiting for files.")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button_upload)
        layout.addWidget(self.button_convert)
        layout.addWidget(self.status)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.files = []
        self.button_upload.clicked.connect(self.select_files)
        self.button_convert.clicked.connect(self.convert_files)

    def select_files(self):
        options = QFileDialog.Options()
        self.files, _ = QFileDialog.getOpenFileNames(
            self, "Select CEF Files", "", "CEF Files (*.cef)", options=options
        )
        if self.files:
            self.status.setText(f"Selected {len(self.files)} files.")
            self.button_convert.setEnabled(True)

    def convert_files(self):
        output_dir = "converted_files"
        os.makedirs(output_dir, exist_ok=True)
        for file in self.files:
            self.convert_cef_to_feather(file, output_dir)
        self.status.setText(f"Converted {len(self.files)} files to `{output_dir}`.")

    def convert_cef_to_feather(self, cef_file, output_dir):
        tree = ET.parse(cef_file)
        root = tree.getroot()
        data = [
            {child.tag: child.text for child in row} for row in root.findall(".//row")
        ]
        df = pd.DataFrame(data)
        output_path = os.path.join(
            output_dir, os.path.basename(cef_file).replace(".cef", ".feather")
        )
        df.to_feather(output_path)


class ThemedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Themed PyQt Application")
        self.setGeometry(300, 300, 400, 200)

        # Set the window icon
        self.setWindowIcon(QIcon("Application formatting/Icon.png"))

        self.label = QLabel("Upload CEF files to convert to Feather format.")
        self.button_upload = QPushButton("Select Files")
        self.button_convert = QPushButton("Convert to Feather")
        self.button_convert.setEnabled(False)
        self.status = QLabel("Status: Waiting for files.")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button_upload)
        layout.addWidget(self.button_convert)
        layout.addWidget(self.status)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.files = []
        self.button_upload.clicked.connect(self.select_files)
        self.button_convert.clicked.connect(self.convert_files)

    def select_files(self):
        options = QFileDialog.Options()
        self.files, _ = QFileDialog.getOpenFileNames(
            self, "Select CEF Files", "", "CEF Files (*.cef)", options=options
        )
        if self.files:
            self.status.setText(f"Selected {len(self.files)} files.")
            self.button_convert.setEnabled(True)

    def convert_files(self):
        output_dir = "converted_files"
        os.makedirs(output_dir, exist_ok=True)
        for file in self.files:
            self.convert_cef_to_feather(file, output_dir)
        self.status.setText(f"Converted {len(self.files)} files to `{output_dir}`.")

    def convert_cef_to_feather(self, cef_file, output_dir):
        tree = ET.parse(cef_file)
        root = tree.getroot()
        data = [
            {child.tag: child.text for child in row} for row in root.findall(".//row")
        ]
        df = pd.DataFrame(data)
        output_path = os.path.join(
            output_dir, os.path.basename(cef_file).replace(".cef", ".feather")
        )
        df.to_feather(output_path)


if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())  # Apply the dark theme
    window = ThemedApp()
    window.show()
    app.exec_()
