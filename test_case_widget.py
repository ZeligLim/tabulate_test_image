import os
from PySide6.QtWidgets import QWidget, QHBoxLayout
from image_panel import ImagePanel


class TestCaseWidget(QWidget):

    def __init__(self, root_folder, k_list, case_name, title_mode="filename", files_list=None, original_file=None):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 15)
        self.panels = []

        # --- ORIGINAL (RAW) IMAGE — shown leftmost, matched by index by the caller ---
        # original_file is None entirely if the feature isn't applicable to this workspace
        # (no loose TIFFs found at the workspace root). "" or a missing path means the
        # feature IS active but this particular case has no matching original.
        if original_file is not None:
            has_match = bool(original_file) and os.path.exists(original_file)
            display_path = original_file if has_match else os.path.join(root_folder, "(no matching original)")
            orig_panel = ImagePanel(display_path, title_mode="filename", is_na=not has_match)
            orig_panel.title.setText(
                f"[ORIGINAL] {os.path.basename(original_file)}" if has_match else "[ORIGINAL] N/A"
            )
            orig_panel.setStyleSheet("border: 1px solid #4488ff;")
            self.panels.append(orig_panel)

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
        # (this intentionally overrides the blue "original" border above when negative)
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