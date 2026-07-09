import sys
import os

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from view_strategies import SingleKStrategy, CrossKStrategy


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Scalable TIFF Workspace Analyzer")
        self.resize(1800, 1000)
        self.root = None
        self.panels = []

        # Enforce pure black application UI stylesheet properties
        self.setStyleSheet("background-color: #000000; color: #ffffff;")

        central = QWidget()
        layout = QVBoxLayout()
        top = QHBoxLayout()

        open_btn = QPushButton("Open Workspace Folder")
        open_btn.setStyleSheet("background-color: #333333; color: white; padding: 6px;")
        open_btn.clicked.connect(self.open_folder)
        top.addWidget(open_btn)

        # --- THE SCALABILITY LAYER ENGINE CONFIGURATION ---
        # 1. Map readable display modes to their corresponding architectural strategy class rules
        self.view_strategies = {
            "Single K Directory (Old View)": SingleKStrategy,
            "Cross-K Normalization (Side-by-Side View)": CrossKStrategy
        }

        # 2. View Mode Selector Dropdown Box
        self.view_mode_box = QComboBox()
        self.view_mode_box.addItems(list(self.view_strategies.keys()))
        self.view_mode_box.setStyleSheet("background-color: #222222; color: white; padding: 4px; font-weight: bold;")
        self.view_mode_box.currentIndexChanged.connect(self.switch_view_strategy)
        top.addWidget(self.view_mode_box)

        # 3. Dynamic Strategy Context Secondary Dropdown Control Item
        self.strategy_combobox = QComboBox()
        self.strategy_combobox.setStyleSheet("background-color: #333333; color: white; padding: 4px;")
        self.strategy_combobox.currentTextChanged.connect(self.execute_current_layout)
        top.addWidget(self.strategy_combobox)

        self.roi_btn = QPushButton("Enable ROI")
        self.roi_btn.setStyleSheet("background-color: #333333; color: white; padding: 6px;")
        self.roi_btn.setCheckable(True)
        self.roi_btn.clicked.connect(self.toggle_roi)
        top.addWidget(self.roi_btn)

        slider_label = QLabel("Panel Height:")
        slider_label.setStyleSheet("color: white; margin-left: 15px;")

        self.global_height_slider = QSlider(Qt.Horizontal)
        self.global_height_slider.setRange(200, 1000)
        self.global_height_slider.setValue(400)
        self.global_height_slider.setFixedWidth(250)
        self.global_height_slider.valueChanged.connect(self.update_global_heights)

        top.addWidget(slider_label)
        top.addWidget(self.global_height_slider)
        top.addStretch()

        layout.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #000000; }")
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #000000;")
        self.case_layout = QVBoxLayout()
        self.container.setLayout(self.case_layout)

        self.scroll.setWidget(self.container)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # Instantiate our current working strategy rule runtime tracking state
        self.current_strategy = self.view_strategies[self.view_mode_box.currentText()](self)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.root = folder
            self.switch_view_strategy()

    def switch_view_strategy(self):
        """Initializes and activates the selected viewing strategy class structure."""
        self.clear()
        selected_mode_text = self.view_mode_box.currentText()
        
        # Instantiate the new strategy object dynamically
        self.current_strategy = self.view_strategies[selected_mode_text](self)
        
        # Allow the new strategy to adjust relevant toolbar widgets
        self.current_strategy.setup_ui(None)
        
        # Load up the workspace layout maps
        self.execute_current_layout()

    def execute_current_layout(self):
        """Forces container clearing processes before invoking strategic layouts safely."""
        if not self.root:
            return
        self.clear()
        self.current_strategy.load_layout()
        self.update_global_heights(self.global_height_slider.value())

    def clear(self):
        while self.case_layout.count():
            item = self.case_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.panels.clear()

    def toggle_roi(self, state):
        for p in self.panels:
            p.enable_roi(state)

    def update_global_heights(self, value):
        for p in self.panels:
            p.setFixedHeight(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())