from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QWidget


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Dashboard")

        # Layout and widgets
        layout = QVBoxLayout()
        convert_button = QPushButton("Convert CEF Files")
        settings_button = QPushButton("Settings")

        # Add widgets to layout
        layout.addWidget(convert_button)
        layout.addWidget(settings_button)

        # Central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect buttons
        convert_button.clicked.connect(self.open_converter)
        settings_button.clicked.connect(self.open_settings)

    def open_converter(self):
        print("Open converter module")

    def open_settings(self):
        print("Open settings module")
