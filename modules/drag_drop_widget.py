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
        print("DragDropWidget initialized")

    def dragEnterEvent(self, event: QDragEnterEvent):
        print("dragEnterEvent called")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            print("Drag event accepted")
        else:
            print("Drag event not accepted")

    def dragMoveEvent(self, event: QDragEnterEvent):
        print("dragMoveEvent called")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            print("Drag move event accepted")
        else:
            print("Drag move event not accepted")

    def dropEvent(self, event: QDropEvent):
        print("dropEvent called")
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                item = QListWidgetItem(file)
                self.addItem(item)
            print("Dropped files:", files)
            event.acceptProposedAction()
        else:
            print("Drop event not accepted")

    def contextMenuEvent(self, event):
        print("contextMenuEvent called")
        context_menu = QMenu(self)
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_item)
        context_menu.addAction(remove_action)
        context_menu.exec(event.globalPos())

    def remove_selected_item(self):
        print("remove_selected_item called")
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        print("Selected item removed")

    def highlight_item(self, item):
        print("highlight_item called")
        for i in range(self.count()):
            self.item(i).setBackground(Qt.GlobalColor.white)  # Reset background color
        item.setBackground(Qt.GlobalColor.lightGray)  # Highlight the hovered item
        print("Item highlighted:", item.text())
