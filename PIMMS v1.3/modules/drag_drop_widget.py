from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDrag, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
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

    def startDrag(self, supportedActions):
        print("Starting drag")
        drag = QDrag(self)
        mimeData = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mimeData)
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent):
        print("Drag enter event")
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        print("Drag move event")
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        print("Drop event")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            urls = event.mimeData().urls()
            files = [url.toLocalFile() for url in urls]
            self.add_files(files)
        elif event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            for item in self.selectedItems():
                self.takeItem(self.row(item))
        else:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            source = event.source()
            for item in source.selectedItems():
                print(f"Moving item: {item.text()} from {source} to {self}")
                self.addItem(item.text())
                source.takeItem(source.row(item))

    def add_files(self, files):
        print(f"Adding files: {files}")
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
        print(f"Files in {self.objectName()}: {self.dropped_files}")  # Debugging

    def get_selected_files(self):
        return [item.text() for item in self.selectedItems()]

    def remove_selected_files(self):
        print("Removing selected items...")  # Debugging
        for item in self.selectedItems():
            print(f"Removing: {item.text()}")  # Debugging
            self.takeItem(self.row(item))
            self.dropped_files.remove(item.text())
        if self.update_callback:
            self.update_callback()


def create_data_importing_tab(tab_widget, main_window):
    main_layout = QVBoxLayout()

    # Create two hubs
    source_hub = DragDropListWidget(other_hub=None)
    target_hub = DragDropListWidget(other_hub=source_hub)
    source_hub.other_hub = target_hub  # Set the reference to the other hub

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
    widget = QWidget()
    widget.setLayout(main_layout)
    tab_widget.addTab(widget, "Data Importing")

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
    print("Moving selected files...")  # Debugging
    selected_files = source_hub.get_selected_files()
    print(f"Selected files to move: {selected_files}")  # Debugging
    target_hub.add_files(selected_files)
    source_hub.remove_selected_files()
    print(f"Files in source hub after move: {source_hub.dropped_files}")  # Debugging
    print(f"Files in target hub after move: {target_hub.dropped_files}")  # Debugging


def remove_files(target_hub):
    print("Removing selected files from target hub...")  # Debugging
    target_hub.remove_selected_files()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop File Management")
        self.resize(800, 600)

        # Create a tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add data importing tab
        create_data_importing_tab(self.tabs, self)

    def convert_files(self, files):
        print(f"Converting files to Feather format: {files}")

    def open_settings(self):
        print("Opening settings")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
