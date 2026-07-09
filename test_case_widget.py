import os
from PySide6.QtWidgets import QWidget, QHBoxLayout
from image_panel import ImagePanel


class TestCaseWidget(QWidget):

    def __init__(self, root_folder, k_list, case_name, title_mode="filename", files_list=None):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 15)
        self.panels = []

        # --- OLD VIEW MODE ---
        if files_list is not None:
            for path in files_list:
                p = ImagePanel(path, title_mode=title_mode, is_na=False)
                self.panels.append(p)

        # --- NEW CROSS-K VIEW MODE ---
        else:
            for k in k_list:
                target_file = os.path.join(root_folder, k, case_name, "debug_After_normalize.tiff")
                is_na = not os.path.exists(target_file)
                p = ImagePanel(target_file, title_mode=title_mode, is_na=is_na)
                self.panels.append(p)

        # --- EVALUATE TEST CASE ROW STATE (WITHOUT REORDERING IMAGES) ---
        self.row_color_state = "normal"  # "red", "orange", or "normal"

        for p in self.panels:
            if getattr(p, "is_negative", False):
                filename_lower = os.path.basename(p.filename).lower()
                if "normalize" in filename_lower:
                    self.row_color_state = "red"
                    break  # Red takes absolute precedence over orange
                else:
                    self.row_color_state = "orange"

        # Apply visual border styling to panels matching the alert states
        for p in self.panels:
            if getattr(p, "is_negative", False):
                if self.row_color_state == "red":
                    p.setStyleSheet("border: 2px solid #ff4444; background-color: rgba(255, 68, 68, 5);")
                    p.title.setStyleSheet("font-size: 13px; font-weight: bold; padding-bottom: 4px; color: #ff6666;")
                elif self.row_color_state == "orange":
                    p.setStyleSheet("border: 2px solid #ffaa00; background-color: rgba(255, 170, 0, 5);")
                    p.title.setStyleSheet("font-size: 13px; font-weight: bold; padding-bottom: 4px; color: #ffaa00;")

        # Inject panels directly into layout in their native sequential order
        for p in self.panels:
            layout.addWidget(p)

        self.setLayout(layout)