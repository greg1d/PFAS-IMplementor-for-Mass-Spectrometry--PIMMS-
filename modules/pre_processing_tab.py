from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
)


class PreProcessingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Create file list
        self.file_list = QListWidget()

        # Create buttons
        browse_button = QPushButton("Browse")
        process_button = QPushButton("Process Files")

        # Connect buttons
        browse_button.clicked.connect(self.browse_files)
        process_button.clicked.connect(self.process_files)

        # Add widgets to layout
        main_layout.addWidget(QLabel("Pre-Processing"))
        main_layout.addWidget(self.file_list)
        main_layout.addWidget(browse_button)
        main_layout.addWidget(process_button)

        self.setLayout(main_layout)

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

    def process_files(self):
        # Implement your file processing logic here
        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            print(f"Processing file: {file_path}")
