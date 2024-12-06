from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class DragDropListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def add_files(self, files):
        for file in files:
            item = QListWidgetItem(file)
            self.addItem(item)

    def get_selected_files(self):
        return [item.text() for item in self.selectedItems()]

    def remove_selected_files(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))


def create_data_importing_tab(tab_widget, main_window):
    layout = QVBoxLayout()

    # Create two hubs
    source_hub = DragDropListWidget()
    target_hub = DragDropListWidget()

    # Create buttons
    move_button = QPushButton("Move Selected Files")
    remove_button = QPushButton("Remove Selected Files")
    convert_button = QPushButton("Convert to Feather Files")
    settings_button = QPushButton("Settings")

    # Add widgets to layout
    layout.addWidget(QLabel("Source Hub"))
    layout.addWidget(source_hub)
    layout.addWidget(QLabel("Target Hub"))
    layout.addWidget(target_hub)
    layout.addWidget(move_button)
    layout.addWidget(remove_button)
    layout.addWidget(convert_button)
    layout.addWidget(settings_button)

    # Set layout to the data importing tab
    tab_widget.setLayout(layout)

    # Connect buttons
    move_button.clicked.connect(lambda: move_files(source_hub, target_hub))
    remove_button.clicked.connect(lambda: remove_files(target_hub))
    convert_button.clicked.connect(
        lambda: main_window.convert_files(target_hub.get_selected_files())
    )
    settings_button.clicked.connect(main_window.open_settings)


def move_files(source_hub, target_hub):
    selected_files = source_hub.get_selected_files()
    target_hub.add_files(selected_files)
    source_hub.remove_selected_files()


def remove_files(target_hub):
    target_hub.remove_selected_files()


def open_settings():
    print("Open settings functionality goes here.")
