from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction


class DragDropWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )  # Enable multiple selection
        self.setMouseTracking(True)  # Enable mouse tracking
        self.current_hover_item = None  # Track the currently hovered item
        self.setStyleSheet("""
            QListWidget::item {
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: #DAD7CD;
            }
            QListWidget::item:hover {
                background-color: #DAD7CD;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                item = QListWidgetItem(file)
                self.addItem(item)
            event.acceptProposedAction()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_selected_item)
        context_menu.addAction(remove_action)
        context_menu.exec(event.globalPos())

    def remove_selected_item(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
