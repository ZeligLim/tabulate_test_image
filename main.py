import sys
import os

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from view_strategies import SingleKStrategy, CrossKStrategy
from export_report import export_to_pdf


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Scalable TIFF Workspace Analyzer")
        self.resize(1800, 1000)
        self.root = None
        self.panels = []

        self.setStyleSheet("background-color: #000000; color: #ffffff;")

        # --- STACK: start screen / loading screen / main content ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_page = self._build_start_page()
        self.loading_page = self._build_loading_page()
        self.content_page = self._build_content_page()

        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.loading_page)
        self.stack.addWidget(self.content_page)
        self.stack.setCurrentWidget(self.start_page)

        # --- THE SCALABILITY LAYER ENGINE CONFIGURATION ---
        self.view_strategies = {
            "Single K Directory (Old View)": SingleKStrategy,
            "Cross-K Normalization (Side-by-Side View)": CrossKStrategy
        }
        self.view_mode_box.addItems(list(self.view_strategies.keys()))

        self.current_strategy = self.view_strategies[self.view_mode_box.currentText()](self)

    # ------------------------------------------------------------------
    # PAGE BUILDERS
    # ------------------------------------------------------------------

    def _build_start_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(page)
        outer.addStretch(1)

        title = QLabel("Scalable TIFF Workspace Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ffffff; margin-bottom: 20px;")
        outer.addWidget(title)

        row = QHBoxLayout()
        row.addStretch(1)

        open_btn = QPushButton("Open Workspace Folder")
        open_btn.setFixedSize(320, 70)
        open_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #2266cc; color: white; font-size: 16px; font-weight: bold;"
            "  border-radius: 8px;"
            "}"
            "QPushButton:hover { background-color: #2f7ae0; }"
            "QPushButton:pressed { background-color: #1a4d99; }"
        )
        open_btn.clicked.connect(self.open_folder)
        row.addWidget(open_btn)

        row.addStretch(1)
        outer.addLayout(row)

        hint = QLabel("Select a folder containing your K test-case directories to begin.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #888888; margin-top: 16px;")
        outer.addWidget(hint)

        outer.addStretch(1)
        return page

    def _build_loading_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(page)
        outer.addStretch(1)

        self.loading_label = QLabel("Loading images...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; margin-bottom: 12px;")
        outer.addWidget(self.loading_label)

        bar_row = QHBoxLayout()
        bar_row.addStretch(1)

        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedWidth(420)
        self.loading_bar.setFixedHeight(24)
        self.loading_bar.setRange(0, 1)
        self.loading_bar.setValue(0)
        self.loading_bar.setTextVisible(True)
        self.loading_bar.setStyleSheet(
            "QProgressBar {"
            "  background-color: #222222; color: white; border: 1px solid #444444;"
            "  border-radius: 4px; text-align: center;"
            "}"
            "QProgressBar::chunk { background-color: #2266cc; border-radius: 4px; }"
        )
        bar_row.addWidget(self.loading_bar)

        bar_row.addStretch(1)
        outer.addLayout(bar_row)

        outer.addStretch(1)
        return page

    def _build_content_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        top = QHBoxLayout()

        open_btn = QPushButton("Open Workspace Folder")
        open_btn.setStyleSheet("background-color: #333333; color: white; padding: 6px;")
        open_btn.clicked.connect(self.open_folder)
        top.addWidget(open_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: #333333; color: white; padding: 6px;")
        refresh_btn.clicked.connect(self.refresh_layout)
        top.addWidget(refresh_btn)

        export_btn = QPushButton("Export PDF")
        export_btn.setStyleSheet("background-color: #333333; color: white; padding: 6px;")
        export_btn.clicked.connect(self.export_pdf)
        top.addWidget(export_btn)

        self.view_mode_box = QComboBox()
        self.view_mode_box.setStyleSheet("background-color: #222222; color: white; padding: 4px; font-weight: bold;")
        self.view_mode_box.currentIndexChanged.connect(self.switch_view_strategy)
        top.addWidget(self.view_mode_box)

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

        width_label = QLabel("Panel Width:")
        width_label.setStyleSheet("color: white; margin-left: 15px;")

        self.global_width_slider = QSlider(Qt.Horizontal)
        self.global_width_slider.setRange(200, 1200)
        self.global_width_slider.setValue(500)
        self.global_width_slider.setFixedWidth(250)
        self.global_width_slider.valueChanged.connect(self.update_global_widths)

        top.addWidget(width_label)
        top.addWidget(self.global_width_slider)

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

        page.setLayout(layout)
        return page

    # ------------------------------------------------------------------
    # PAGE SWITCHING / PROGRESS
    # ------------------------------------------------------------------

    def show_start(self):
        self.stack.setCurrentWidget(self.start_page)

    def show_loading(self, text="Loading images..."):
        self.loading_label.setText(text)
        self.loading_bar.setRange(0, 1)
        self.loading_bar.setValue(0)
        self.stack.setCurrentWidget(self.loading_page)
        QApplication.processEvents()

    def show_content(self):
        self.stack.setCurrentWidget(self.content_page)

    def report_progress(self, value, maximum):
        """Called by view strategies as each test-case row finishes loading."""
        if maximum <= 0:
            return
        self.loading_bar.setRange(0, maximum)
        self.loading_bar.setValue(value)
        self.loading_label.setText(f"Loading images... ({value}/{maximum})")
        QApplication.processEvents()

    # ------------------------------------------------------------------
    # CORE LOGIC
    # ------------------------------------------------------------------

    def export_pdf(self):
        if not self.root or not self.panels:
            QMessageBox.warning(self, "Export PDF", "No images are currently loaded to export.")
            return

        default_name = os.path.join(self.root, "workspace_report.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", default_name, "PDF Files (*.pdf)")
        if not path:
            return

        self.show_loading("Exporting PDF...")
        try:
            export_to_pdf(self, path, progress_callback=self.report_progress)
        except Exception as e:
            self.show_content()
            QMessageBox.critical(self, "Export Failed", f"Could not export PDF:\n{e}")
            return

        self.show_content()
        QMessageBox.information(self, "Export Complete", f"Report saved to:\n{path}")

    def refresh_layout(self):
        """Re-reads files from disk and rebuilds the current view (e.g. after a re-render)."""
        if not self.root:
            return
        self.execute_current_layout()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.root = folder
            self.switch_view_strategy()

    def switch_view_strategy(self):
        """Initializes and activates the selected viewing strategy class structure."""
        self.clear()
        selected_mode_text = self.view_mode_box.currentText()

        self.current_strategy = self.view_strategies[selected_mode_text](self)
        self.current_strategy.setup_ui(None)

        self.execute_current_layout()

    def execute_current_layout(self):
        """Forces container clearing processes before invoking strategic layouts safely."""
        if not self.root:
            return

        self.clear()
        self.show_loading("Loading images...")

        self.current_strategy.load_layout()

        self.update_global_heights(self.global_height_slider.value())
        self.update_global_widths(self.global_width_slider.value())
        self.show_content()

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

    def update_global_widths(self, value):
        for p in self.panels:
            p.setFixedWidth(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())