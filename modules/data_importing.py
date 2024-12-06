from PyQt6.QtWidgets import QVBoxLayout, QPushButton
from modules.drag_drop_widget import DragDropWidget


def create_data_importing_tab(tab_widget, main_window):
    layout = QVBoxLayout()
    drag_drop_widget = DragDropWidget()
    convert_button = QPushButton("Convert CEF Files")
    settings_button = QPushButton("Settings")

    # Add widgets to layout
    layout.addWidget(drag_drop_widget)
    layout.addWidget(convert_button)
    layout.addWidget(settings_button)

    # Set layout to the data importing tab
    tab_widget.setLayout(layout)

    # Connect buttons
    convert_button.clicked.connect(
        lambda: main_window.convert_files(drag_drop_widget.dropped_files)
    )
    settings_button.clicked.connect(main_window.open_settings)


def open_settings():
    print("Open settings functionality goes here.")
