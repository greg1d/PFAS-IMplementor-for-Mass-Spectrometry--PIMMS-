from PyQt6.QtWidgets import QWidget, QVBoxLayout
from modules.peak_alignment import PeakAlignment
from modules.blank_subtraction import BlankSubtraction


class PreProcessingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Create Peak Alignment and Blank Subtraction sections
        peak_alignment = PeakAlignment()
        blank_subtraction = BlankSubtraction()

        # Add sections to layout
        main_layout.addWidget(peak_alignment)
        main_layout.addWidget(blank_subtraction)

        self.setLayout(main_layout)
