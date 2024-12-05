from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget


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
        convert_button.clicked.connect(self.convert_files)
        settings_button.clicked.connect(self.open_settings)

    def convert_files(self):
        print("Convert files functionality goes here.")

    def open_settings(self):
        print("Open settings functionality goes here.")


def load_stylesheet():
    with open("styles/theme.qss", "r") as file:
        return file.read()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Load the stylesheet
    app.setStyleSheet(load_stylesheet())

    # Initialize the main window
    main_window = HomeWindow()
    main_window.show()

    # Run the application
    sys.exit(app.exec_())
