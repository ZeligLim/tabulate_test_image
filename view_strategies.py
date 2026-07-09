import os
from collections import defaultdict
from PySide6.QtWidgets import QLabel
from test_case_widget import TestCaseWidget


def _discover_root_originals(root):
    """
    Loose TIFF files sitting directly in the workspace root (siblings of the K folders,
    e.g. k1/k2/k3). Returns a dict mapping filename-without-extension -> full path, so
    a case named "32_bottom_..." matches the original file "32_bottom_....tiff" exactly.
    """
    if not root:
        return {}
    result = {}
    for f in os.listdir(root):
        full = os.path.join(root, f)
        if os.path.isfile(full) and f.lower().endswith((".tif", ".tiff")):
            stem = os.path.splitext(f)[0]
            result[stem] = full
    return result


class BaseViewStrategy:
    def __init__(self, main_window):
        self.window = main_window

    def setup_ui(self, top_layout):
        pass

    def load_layout(self):
        raise NotImplementedError


class SingleKStrategy(BaseViewStrategy):
    """Pick one K directory, show first 3 TIFF files per test case."""
    def setup_ui(self, top_layout):
        self.kbox = self.window.strategy_combobox
        self.kbox.show()
        self.kbox.clear()

        if self.window.root:
            ks = sorted([
                k for k in os.listdir(self.window.root)
                if os.path.isdir(os.path.join(self.window.root, k))
            ])
            self.kbox.addItems(ks)

    def _get_sort_priority(self, state):
        return {"red": 2, "orange": 1, "normal": 0}.get(state, 0)

    def load_layout(self):
        k = self.window.strategy_combobox.currentText()
        if not self.window.root or not k:
            return

        path = os.path.join(self.window.root, k)
        cases = sorted([c for c in os.listdir(path) if os.path.isdir(os.path.join(path, c))])
        originals = _discover_root_originals(self.window.root)

        total = len(cases)
        case_rows = []
        for i, c in enumerate(cases):
            folder = os.path.join(path, c)
            files = sorted([
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith((".tif", ".tiff"))
            ])[:3]

            original_file = None
            if originals:
                original_file = originals.get(c, "")

            widget = TestCaseWidget(
                self.window.root, [k], c, title_mode="filename",
                files_list=files, original_file=original_file
            )
            case_rows.append((c, widget))
            self.window.report_progress(i + 1, total)

        case_rows.sort(key=lambda x: self._get_sort_priority(x[1].row_color_state), reverse=True)

        for c, widget in case_rows:
            label = QLabel(c)
            if widget.row_color_state == "red":
                label.setText(f"{c} [CRITICAL: NEGATIVE NORMALIZE]")
                label.setStyleSheet("font-size:18px; font-weight:bold; color: #ff4444; padding-top: 10px;")
            elif widget.row_color_state == "orange":
                label.setText(f"{c} [WARNING: NEGATIVE VALUE]")
                label.setStyleSheet("font-size:18px; font-weight:bold; color: #ffaa00; padding-top: 10px;")
            else:
                label.setStyleSheet("font-size:18px; font-weight:bold; color: #ffffff; padding-top: 10px;")

            self.window.case_layout.addWidget(label)
            self.window.panels.extend(widget.panels)
            self.window.case_layout.addWidget(widget)


class CrossKStrategy(BaseViewStrategy):
    """Look across all K directories for 'debug_After_normalize.tiff'."""
    def setup_ui(self, top_layout):
        self.window.strategy_combobox.hide()

    def _get_sort_priority(self, state):
        return {"red": 2, "orange": 1, "normal": 0}.get(state, 0)

    def load_layout(self):
        if not self.window.root:
            return

        k_folders = sorted([
            k for k in os.listdir(self.window.root) if os.path.isdir(os.path.join(self.window.root, k))
        ])
        if not k_folders:
            return

        # Traversal Mapping Setup
        case_to_k_map = defaultdict(list)
        for k in k_folders:
            k_path = os.path.join(self.window.root, k)
            cases_in_k = [c for c in os.listdir(k_path) if os.path.isdir(os.path.join(k_path, c))]
            for c in cases_in_k:
                case_to_k_map[c].append(k)

        frequency_buckets = defaultdict(list)
        for case_name, containing_ks in case_to_k_map.items():
            frequency_buckets[len(containing_ks)].append(case_name)

        sorted_prioritized_cases = []
        for count in sorted(frequency_buckets.keys(), reverse=True):
            for case_name in sorted(frequency_buckets[count]):
                sorted_prioritized_cases.append((case_name, count))

        total = len(sorted_prioritized_cases)
        originals = _discover_root_originals(self.window.root)

        case_rows = []
        for i, (c, count) in enumerate(sorted_prioritized_cases):
            original_file = None
            if originals:
                original_file = originals.get(c, "")

            widget = TestCaseWidget(
                self.window.root, k_folders, c, title_mode="parent_k",
                original_file=original_file
            )
            case_rows.append((c, count, widget))
            self.window.report_progress(i + 1, total)

        case_rows.sort(key=lambda x: self._get_sort_priority(x[2].row_color_state), reverse=True)

        for c, count, widget in case_rows:
            presence_tag = f"[{count}/{len(k_folders)} K Folders Found]"
            label_text = f"Test Case: {c}   {presence_tag}"

            label = QLabel()
            if widget.row_color_state == "red":
                label.setText(f"{label_text} [CRITICAL: NEGATIVE NORMALIZE]")
                label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff4444; padding-top: 15px;")
            elif widget.row_color_state == "orange":
                label.setText(f"{label_text} [WARNING: NEGATIVE VALUE]")
                label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffaa00; padding-top: 15px;")
            else:
                label.setText(label_text)
                label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; padding-top: 15px;")

            self.window.case_layout.addWidget(label)
            self.window.panels.extend(widget.panels)
            self.window.case_layout.addWidget(widget)