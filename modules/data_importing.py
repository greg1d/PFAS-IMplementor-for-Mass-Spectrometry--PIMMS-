from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
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
    def __init__(self, update_callback=None, other_hub=None):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.dropped_files = (
            set()
        )  # Store the set of dropped files to prevent duplicates
        self.setMouseTracking(True)  # Enable mouse tracking
        self.update_callback = update_callback  # Callback to update the file list
        self.other_hub = other_hub  # Reference to the other hub

        # Set the stylesheet
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #BEBEBE;
                border-radius: 8px;
                padding: 5px;
                background-color: #F7F6F3;
            }
            QListWidget::item {
                background-color: white;
                margin: 2px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #DAD7CD;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #ECECEC;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.add_files(files)
            event.acceptProposedAction()

    def add_files(self, files):
        new_files = []
        for file in files:
            if file not in self.dropped_files and (
                self.other_hub is None or file not in self.other_hub.dropped_files
            ):
                new_files.append(file)
        self.dropped_files.update(new_files)
        for file in new_files:
            item = QListWidgetItem(file)
            self.addItem(item)
        if self.update_callback:
            self.update_callback()

    def get_selected_files(self):
        return [item.text() for item in self.selectedItems()]

    def remove_selected_item(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
            self.dropped_files.remove(item.text())
        if self.update_callback:
            self.update_callback()

    def clear_all_items(self):
        self.clear()
        self.dropped_files.clear()
        if self.update_callback:
            self.update_callback()


def create_data_importing_tab(tab_widget, main_window):
    main_layout = QVBoxLayout()

    # Create two hubs
    file_hub = DragDropListWidget(
        update_callback=lambda: update_file_list(file_list, file_hub)
    )
    processing_hub = DragDropListWidget(
        update_callback=lambda: update_file_list(processing_list, processing_hub),
        other_hub=file_hub,
    )
    file_hub.other_hub = processing_hub  # Set the reference to the other hub

    # Create file lists
    file_list = QListWidget()
    processing_list = QListWidget()

    # Create buttons
    browse_button = QPushButton("Browse")
    move_button = QPushButton("Move Selected Files")
    remove_button = QPushButton("Remove Selected Files")
    convert_button = QPushButton("Convert to Feather Files")
    settings_button = QPushButton("Settings")

    # Create a horizontal layout for the hubs
    hubs_layout = QHBoxLayout()

    # Create a vertical layout for the file hub and its label
    file_layout = QVBoxLayout()
    file_label = QLabel("File Hub")
    file_label.setStyleSheet(
        "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
    )
    file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    file_layout.addWidget(file_label)
    file_layout.addWidget(file_hub)
    file_layout.addWidget(browse_button)

    # Create a vertical layout for the processing hub and its label
    processing_layout = QVBoxLayout()
    processing_label = QLabel("Processing Hub")
    processing_label.setStyleSheet(
        "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
    )
    processing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    processing_layout.addWidget(processing_label)
    processing_layout.addWidget(processing_hub)

    # Add the file and processing layouts to the hubs layout
    hubs_layout.addLayout(file_layout)
    hubs_layout.addLayout(processing_layout)

    # Add the hubs layout and lists layout to the main layout
    main_layout.addLayout(hubs_layout)

    # Add buttons to the main layout
    main_layout.addWidget(move_button)
    main_layout.addWidget(remove_button)
    main_layout.addWidget(convert_button)
    main_layout.addWidget(settings_button)

    # Set layout to the data importing tab
    tab_widget.setLayout(main_layout)

    # Connect buttons
    browse_button.clicked.connect(lambda: browse_files(file_hub))
    move_button.clicked.connect(lambda: move_files(file_hub, processing_hub))
    remove_button.clicked.connect(lambda: remove_files(processing_hub))
    convert_button.clicked.connect(
        lambda: main_window.convert_files(processing_hub.get_selected_files())
    )
    settings_button.clicked.connect(main_window.open_settings)


def update_file_list(list_widget, hub_widget):
    list_widget.clear()
    for file in hub_widget.dropped_files:
        list_widget.addItem(file)
    print(f"Files in {hub_widget.objectName()}: {hub_widget.dropped_files}")


def browse_files(file_hub):
    files, _ = QFileDialog.getOpenFileNames(None, "Select Files")
    if files:
        file_hub.add_files(files)


def move_files(file_hub, processing_hub):
    selected_files = file_hub.get_selected_files()
    processing_hub.add_files(selected_files)
    file_hub.remove_selected_item()


def remove_files(processing_hub):
    processing_hub.remove_selected_item()


def open_settings():
    print("Open settings functionality goes here.")
