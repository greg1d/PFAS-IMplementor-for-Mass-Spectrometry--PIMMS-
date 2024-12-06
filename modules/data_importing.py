from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class DragDropListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

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
    main_layout = QVBoxLayout()

    # Create two hubs
    source_hub = DragDropListWidget()
    target_hub = DragDropListWidget()

    # Create buttons
    browse_button = QPushButton("Browse")
    move_button = QPushButton("Move Selected Files")
    remove_button = QPushButton("Remove Selected Files")
    convert_button = QPushButton("Convert to Feather Files")
    settings_button = QPushButton("Settings")

    # Create a horizontal layout for the hubs
    hubs_layout = QHBoxLayout()

    # Create a vertical layout for the source hub and its label
    source_layout = QVBoxLayout()
    source_layout.addWidget(QLabel("File Hub"))
    source_layout.addWidget(source_hub)
    source_layout.addWidget(browse_button)

    # Create a vertical layout for the target hub and its label
    target_layout = QVBoxLayout()
    target_layout.addWidget(QLabel("Importing Hub"))
    target_layout.addWidget(target_hub)

    # Add the source and target layouts to the hubs layout
    hubs_layout.addLayout(source_layout)
    hubs_layout.addLayout(target_layout)

    # Add the hubs layout to the main layout
    main_layout.addLayout(hubs_layout)

    # Add buttons to the main layout
    main_layout.addWidget(move_button)
    main_layout.addWidget(remove_button)
    main_layout.addWidget(convert_button)
    main_layout.addWidget(settings_button)

    # Set layout to the data importing tab
    tab_widget.setLayout(main_layout)

    # Connect buttons
    browse_button.clicked.connect(lambda: browse_files(source_hub))
    move_button.clicked.connect(lambda: move_files(source_hub, target_hub))
    remove_button.clicked.connect(lambda: remove_files(target_hub))
    convert_button.clicked.connect(
        lambda: main_window.convert_files(target_hub.get_selected_files())
    )
    settings_button.clicked.connect(main_window.open_settings)


def browse_files(source_hub):
    files, _ = QFileDialog.getOpenFileNames(None, "Select Files")
    if files:
        source_hub.add_files(files)


def move_files(source_hub, target_hub):
    selected_files = source_hub.get_selected_files()
    target_hub.add_files(selected_files)
    source_hub.remove_selected_files()


def remove_files(target_hub):
    target_hub.remove_selected_files()


def open_settings():
    print("Open settings functionality goes here.")
