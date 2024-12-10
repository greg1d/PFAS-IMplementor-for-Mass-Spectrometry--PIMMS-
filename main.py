from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget

from modules.cef_conversion import convert_files
from modules.data_importing import create_data_importing_tab, open_settings


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

        # Load the Montserrat font variants
        QFontDatabase.addApplicationFont("fonts/Montserrat-Regular.ttf")
        QFontDatabase.addApplicationFont("fonts/Montserrat-Bold.ttf")
        QFontDatabase.addApplicationFont("fonts/Montserrat-Medium.ttf")

        # Apply the stylesheet
        with open("styles/theme.qss", "r") as f:
            self.setStyleSheet(f.read())

    def convert_files(self, dropped_files, processing_hub):
        # Debugging statement
        print(f"Converting files: {dropped_files}")
        print(f"Processing hub: {processing_hub}")

        # Call the convert_files function with the processing hub
        convert_files(dropped_files, processing_hub)

    def open_settings(self):
        open_settings()


if __name__ == "__main__":
    app = QApplication([])
    window = HomeWindow()
    window.show()
    app.exec()
