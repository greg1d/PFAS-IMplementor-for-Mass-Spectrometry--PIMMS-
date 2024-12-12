from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
)


class PeakAlignment(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create file list
        self.file_list = QListWidget()

        # Create buttons
        browse_button = QPushButton("Browse")
        align_button = QPushButton("Align Peaks")

        # Connect buttons
        browse_button.clicked.connect(self.browse_files)
        align_button.clicked.connect(self.align_peaks)

        # Add widgets to layout
        layout.addWidget(QLabel("Peak Alignment"))
        layout.addWidget(self.file_list)
        layout.addWidget(browse_button)
        layout.addWidget(align_button)

        self.setLayout(layout)

    def browse_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*);;Python Files (*.py)",
            options=options,
        )
        if files:
            self.file_list.addItems(files)

    def align_peaks(self):
        # Implement your peak alignment logic here
        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            print(f"Aligning peaks in file: {file_path}")
