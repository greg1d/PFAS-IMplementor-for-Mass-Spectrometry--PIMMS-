from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction
from PyQt6.QtCore import Qt


class DragDropWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.itemEntered.connect(self.highlight_item)  # Connect the itemEntered signal

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            item = QListWidgetItem(file)
            self.addItem(item)
        print("Dropped files:", files)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_item)
        context_menu.addAction(remove_action)
        context_menu.exec(event.globalPos())

    def remove_selected_item(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    def highlight_item(self, item):
        for i in range(self.count()):
            self.item(i).setBackground(Qt.GlobalColor.white)  # Reset background color
        item.setBackground(Qt.GlobalColor.lightGray)  # Highlight the hovered item
