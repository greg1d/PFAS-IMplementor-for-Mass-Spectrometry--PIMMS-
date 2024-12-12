from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QLineEdit,
)


class PeakAlignment(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

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
        self.rt_label = QLabel("RT:")
        self.ccs_label = QLabel("CCS:")
        self.mz_label = QLabel("m/z:")

        # Create horizontal layouts for each label-input pair
        rt_layout = QHBoxLayout()
        rt_layout.addWidget(self.rt_label)
        rt_layout.addWidget(self.rt_input)

        ccs_layout = QHBoxLayout()
        ccs_layout.addWidget(self.ccs_label)
        ccs_layout.addWidget(self.ccs_input)

        mz_layout = QHBoxLayout()
        mz_layout.addWidget(self.mz_label)
        mz_layout.addWidget(self.mz_input)

        # Create a main horizontal layout for the input fields
        input_layout = QHBoxLayout()
        input_layout.addLayout(rt_layout)
        input_layout.addLayout(ccs_layout)
        input_layout.addLayout(mz_layout)

        # Create file list
        self.file_list = QListWidget()

        # Create buttons
        browse_button = QPushButton("Browse")
        align_button = QPushButton("Align Peaks")

        # Connect buttons
        browse_button.clicked.connect(self.browse_files)
        align_button.clicked.connect(self.align_peaks)

        # Add widgets to layout
        main_layout.addWidget(header_label)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.file_list)
        main_layout.addWidget(browse_button)
        main_layout.addWidget(align_button)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Set the width of the input fields to 10% of the window width
        new_width = int(self.width() * 0.1)
        self.rt_input.setFixedWidth(new_width)
        self.ccs_input.setFixedWidth(new_width)
        self.mz_input.setFixedWidth(new_width)

        # Set the width of the labels to be 5% less than the input fields
        label_width = int(new_width * 0.2)
        self.rt_label.setFixedWidth(label_width)
        self.ccs_label.setFixedWidth(label_width)
        self.mz_label.setFixedWidth(label_width)

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
        # Get user input values
        rt_value = self.rt_input.text()
        ccs_value = self.ccs_input.text()
        mz_value = self.mz_input.text()

        # Implement your peak alignment logic here
        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            print(
                f"Aligning peaks in file: {file_path} with RT: {rt_value}, CCS: {ccs_value}, m/z: {mz_value}"
            )
            # Add your logic to examine feather files based on RT, CCS, and m/z
