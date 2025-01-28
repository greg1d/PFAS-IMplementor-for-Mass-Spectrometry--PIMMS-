from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QProgressBar,
    QWidget,
    QFrame,
    QSizePolicy,
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
        for file in files:
            if file not in self.dropped_files:
                self.dropped_files.add(file)
                item = QListWidgetItem(file)  # Set the file path as the item text
                widget = QWidget()
                layout = (
                    QVBoxLayout()
                )  # Change to QVBoxLayout to stack label above progress bar
                frame = QFrame()
                frame_layout = QVBoxLayout()
                progress_bar = QProgressBar()
                progress_bar.setMaximum(100)
                progress_bar.setValue(0)
                progress_bar.setFormat(
                    file
                )  # Set the progress bar label to the file name
                frame_layout.addWidget(progress_bar)
                frame.setLayout(frame_layout)
                layout.addWidget(frame)
                widget.setLayout(layout)
                item.setSizeHint(widget.sizeHint())
                self.addItem(item)
                self.setItemWidget(item, widget)

                frame.setStyleSheet("""
                    QFrame {
                        background-color: transparent;
                        margin: 0px;
                        padding: 0px;
                        }
                    QProgressBar {
                        border: 0px solid grey;
                        border-radius: 0px;
                        text-align: left;
                        width: 100%;
                        height: 10px;
                        font-size: 16px;  
                        margin: 0px;                      
                    }
                    QProgressBar::chunk {
                        background-color: #4caf50;
                    }
                """)
                progress_bar.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
                # Debugging statement to check the properties of the item
                print(f"Added file: {file}")
                print(f"Item text: {item.text()}")
                print(f"Item background color: {item.background().color().name()}")
                print(f"Item text color: {item.foreground().color().name()}")

    def get_selected_files(self):
        selected_files = [item.text() for item in self.selectedItems()]
        print(f"Selected files: {selected_files}")  # Debugging statement
        return selected_files

    def update_progress(self, file, value):
        for index in range(self.count()):
            item = self.item(index)
            widget = self.itemWidget(item)
            progress_bar = widget.findChild(QProgressBar)
            if progress_bar.format() == file:
                progress_bar.setValue(value)
                break

    def remove_selected_item(self):
        for item in self.selectedItems():
            print(f"Removing item: {item.text()}")  # Debugging statement
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
    move_to_processing_button = QPushButton()
    move_to_processing_button.setIcon(
        QIcon("icons/arrow-right.png")
    )  # Set right arrow icon
    move_to_file_button = QPushButton()
    move_to_file_button.setIcon(QIcon("icons/arrow-left.png"))  # Set left arrow icon
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
    processing_label = QLabel("Importing Hub")
    processing_label.setStyleSheet(
        "font-family: 'Montserrat'; font-weight: bold; color: black; font-size: 20px; text-align: center;"
    )
    processing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    processing_layout.addWidget(processing_label)
    processing_layout.addWidget(processing_hub)
    processing_layout.addWidget(
        convert_button
    )  # Add the convert button under the processing hub

    # Create a vertical layout for the arrow buttons
    arrow_layout = QVBoxLayout()
    arrow_layout.addWidget(move_to_processing_button)
    arrow_layout.addWidget(move_to_file_button)

    # Add the file, arrow, and processing layouts to the hubs layout
    hubs_layout.addLayout(file_layout)
    hubs_layout.addLayout(arrow_layout)
    hubs_layout.addLayout(processing_layout)

    # Add the hubs layout and lists layout to the main layout
    main_layout.addLayout(hubs_layout)

    # Add buttons to the main layout
    main_layout.addWidget(remove_button)
    main_layout.addWidget(settings_button)

    # Set layout to the data importing tab
    tab_widget.setLayout(main_layout)

    # Connect buttons
    browse_button.clicked.connect(lambda: browse_files(file_hub))
    move_to_processing_button.clicked.connect(
        lambda: move_files_to_processing(file_hub, processing_hub)
    )
    move_to_file_button.clicked.connect(
        lambda: move_files_to_file(processing_hub, file_hub)
    )
    remove_button.clicked.connect(lambda: remove_files(processing_hub, file_hub))
    convert_button.clicked.connect(
        lambda: main_window.convert_files(
            processing_hub.get_selected_files(), processing_hub
        )
    )
    settings_button.clicked.connect(main_window.open_settings)


def update_file_list(list_widget, hub_widget):
    list_widget.clear()
    for file in hub_widget.dropped_files:
        list_widget.addItem(file)
    print(
        f"Files in {hub_widget.objectName()}: {hub_widget.dropped_files}"
    )  # Debugging


def browse_files(file_hub):
    files, _ = QFileDialog.getOpenFileNames(None, "Select Files")
    if files:
        file_hub.add_files(files)


def move_files_to_processing(file_hub, processing_hub):
    selected_files = file_hub.get_selected_files()
    if selected_files:
        file_hub.remove_selected_item()  # Ensure files are removed from the source hub
        processing_hub.add_files(selected_files)


def move_files_to_file(processing_hub, file_hub):
    selected_files = processing_hub.get_selected_files()
    if selected_files:
        processing_hub.remove_selected_item()  # Ensure files are removed from the source hub
        file_hub.add_files(selected_files)


def remove_files(processing_hub, file_hub):
    selected_files_processing = processing_hub.get_selected_files()
    selected_files_file = file_hub.get_selected_files()
    selected_files = list(set(selected_files_processing + selected_files_file))
    print(f"Selected files to remove: {selected_files}")  # Debugging statement

    if selected_files:
        # Debugging: Print items in processing hub before removal
        print("Items in processing hub before removal:")
        for index in range(processing_hub.count()):
            item = processing_hub.item(index)
            print(f"  {item.text()}")

        # Remove selected items from the processing hub
        for file in selected_files:
            items = processing_hub.findItems(file, Qt.MatchFlag.MatchExactly)
            for item in items:
                processing_hub.takeItem(processing_hub.row(item))
                if file in processing_hub.dropped_files:
                    processing_hub.dropped_files.remove(file)
                print(f"Removed {file} from processing hub")

        # Debugging: Print items in processing hub after removal
        print("Items in processing hub after removal:")
        for index in range(processing_hub.count()):
            item = processing_hub.item(index)
            print(f"  {item.text()}")

        # Debugging: Print items in file hub before removal
        print("Items in file hub before removal:")
        for index in range(file_hub.count()):
            item = file_hub.item(index)
            print(f"  {item.text()}")

        # Remove corresponding items from the file hub
        for file in selected_files:
            items = file_hub.findItems(file, Qt.MatchFlag.MatchExactly)
            for item in items:
                file_hub.takeItem(file_hub.row(item))
                if file in file_hub.dropped_files:
                    file_hub.dropped_files.remove(file)
                print(f"Removed {file} from file hub")

        # Debugging: Print items in file hub after removal
        print("Items in file hub after removal:")
        for index in range(file_hub.count()):
            item = file_hub.item(index)
            print(f"  {item.text()}")

        # Update the UI
        if processing_hub.update_callback:
            processing_hub.update_callback()
        if file_hub.update_callback:
            file_hub.update_callback()
    else:
        print(
            "No files selected to remove."
        )  # Debugging statement # Debugging statement


def open_settings():
    print("Open settings functionality goes here.")
