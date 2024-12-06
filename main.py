from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget
from PyQt6.QtCore import QFile, QTextStream
from modules.data_importing import (
    create_data_importing_tab,
    open_settings,
)
from modules.cef_conversion import convert_files  # Import the convert_files function


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIMMS v1.2")

        # Create a tab widget
        self.tabs = QTabWidget()

        # Create the data importing tab
        self.data_importing_tab = QWidget()
        create_data_importing_tab(self.data_importing_tab, self)

        # Add tabs to the tab widget
        self.tabs.addTab(self.data_importing_tab, "Data Importing")

        # Set the tab widget as the central widget
        self.setCentralWidget(self.tabs)

    def convert_files(self):
        convert_files()

    def open_settings(self):
        open_settings()


def load_stylesheet():
    file = QFile("styles/theme.qss")
    file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
    stream = QTextStream(file)
    stylesheet = stream.readAll()
    file.close()
    return stylesheet


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Load the stylesheet
    app.setStyleSheet(load_stylesheet())

    # Initialize the main window
    main_window = HomeWindow()
    main_window.show()

    # Run the application
    sys.exit(app.exec())
