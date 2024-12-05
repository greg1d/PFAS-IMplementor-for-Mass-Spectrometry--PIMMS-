from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QTabWidget,
    QLabel,
)
from PyQt6.QtCore import QFile, QTextStream
from modules.drag_drop_widget import DragDropWidget  # Import the DragDropWidget class


class HomeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIMMS v1.2")

        # Create a tab widget
        self.tabs = QTabWidget()

        # Create the data importing tab
        self.data_importing_tab = QWidget()
        self.create_data_importing_tab()

        # Create additional tabs
        self.data_processing_tab = QWidget()
        self.create_data_processing_tab()

        self.data_filtration_tab = QWidget()
        self.create_data_filtration_tab()

        self.scoring_tab = QWidget()
        self.create_scoring_tab()

        self.results_tab = QWidget()
        self.create_results_tab()

        # Add tabs to the tab widget
        self.tabs.addTab(self.data_importing_tab, "Data Importing")
        self.tabs.addTab(self.data_processing_tab, "Data Processing")
        self.tabs.addTab(self.data_filtration_tab, "Data Filtration")
        self.tabs.addTab(self.scoring_tab, "Scoring")
        self.tabs.addTab(self.results_tab, "Results")

        # Set the tab widget as the central widget
        self.setCentralWidget(self.tabs)

    def create_data_importing_tab(self):
        layout = QVBoxLayout()
        drag_drop_widget = DragDropWidget()
        convert_button = QPushButton("Convert CEF Files")
        settings_button = QPushButton("Settings")

        # Add widgets to layout
        layout.addWidget(drag_drop_widget)
        layout.addWidget(convert_button)
        layout.addWidget(settings_button)

        # Set layout to the data importing tab
        self.data_importing_tab.setLayout(layout)

        # Connect buttons
        convert_button.clicked.connect(self.convert_files)
        settings_button.clicked.connect(self.open_settings)

    def create_data_processing_tab(self):
        layout = QVBoxLayout()
        label = QLabel("Data Processing functionality goes here.")
        layout.addWidget(label)
        self.data_processing_tab.setLayout(layout)

    def create_data_filtration_tab(self):
        layout = QVBoxLayout()
        label = QLabel("Data Filtration functionality goes here.")
        layout.addWidget(label)
        self.data_filtration_tab.setLayout(layout)

    def create_scoring_tab(self):
        layout = QVBoxLayout()
        label = QLabel("Scoring functionality goes here.")
        layout.addWidget(label)
        self.scoring_tab.setLayout(layout)

    def create_results_tab(self):
        layout = QVBoxLayout()
        label = QLabel("Results functionality goes here.")
        layout.addWidget(label)
        self.results_tab.setLayout(layout)

    def convert_files(self):
        print("Convert files functionality goes here.")

    def open_settings(self):
        print("Open settings functionality goes here.")


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
