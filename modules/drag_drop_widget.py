from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction, QColor
from PyQt6.QtCore import Qt


class DragDropWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.current_hover_item = None  # Track the currently hovered item
        self.setStyleSheet("""
            QListWidget::item {
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #006400;
            }
        """)
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

    def mouseMoveEvent(self, event):
        print("mouseMoveEvent called")
        item = self.itemAt(event.pos())
        if item != self.current_hover_item:
            if self.current_hover_item:
                print(f"Resetting color of item: {self.current_hover_item.text()}")
                print(
                    f"Previous color: {self.current_hover_item.background().color().name()}"
                )
                self.current_hover_item.setBackground(
                    QColor(Qt.GlobalColor.white)
                )  # Reset background color of the previous item
                print(
                    f"New color: {self.current_hover_item.background().color().name()}"
                )
            if item:
                print(f"Highlighting item: {item.text()}")
                print(f"Previous color: {item.background().color().name()}")
                item.setBackground(
                    QColor(0, 100, 0)
                )  # Highlight the hovered item with dark green color
                print(f"New color: {item.background().color().name()}")
                item.setSelected(False)  # Ensure the item is not selected
                print(f"Item selected state: {item.isSelected()}")
            self.current_hover_item = item
            print(
                f"Current hover item set to: {self.current_hover_item.text() if self.current_hover_item else 'None'}"
            )
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        print("leaveEvent called")
        if self.current_hover_item:
            print(f"Resetting color of item: {self.current_hover_item.text()}")
            print(
                f"Previous color: {self.current_hover_item.background().color().name()}"
            )
            self.current_hover_item.setBackground(QColor(Qt.GlobalColor.white))
            print(f"New color: {self.current_hover_item.background().color().name()}")
            self.current_hover_item = None
        super().leaveEvent(event)
