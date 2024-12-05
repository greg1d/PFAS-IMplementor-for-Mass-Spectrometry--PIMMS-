from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DragDropWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setPlaceholderText("Drag and drop files here")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.setPlainText("\n".join(files))
        # Handle the dropped files as needed
        print("Dropped files:", files)
