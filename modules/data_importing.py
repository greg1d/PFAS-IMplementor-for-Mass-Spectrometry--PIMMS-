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
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.dropped_files = []  # Store the list of dropped files
        self.setMouseTracking(True)  # Enable mouse tracking

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
            event.acceptProposedAction()
            urls = event.mimeData().urls()
            files = [url.toLocalFile() for url in urls]
            self.add_files(files)

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
    source_label = QLabel("File Hub")
    source_label.setStyleSheet(
        "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
    )
    source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    source_layout.addWidget(source_label)
    source_layout.addWidget(source_hub)
    source_layout.addWidget(browse_button)

    # Create a vertical layout for the target hub and its label
    target_layout = QVBoxLayout()
    target_label = QLabel("Importing Hub")
    target_label.setStyleSheet(
        "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
    )
    target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    target_layout.addWidget(target_label)
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
