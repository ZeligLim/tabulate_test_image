"""
Generates a paginated PDF report from the currently loaded workspace view.

Each page corresponds to one test-case row: the row's label (with its
red/orange/normal alert state), followed by each image panel rendered
with its min/max/mean stats. Uses matplotlib's PdfPages backend, so the
resulting file is a completely standard PDF that opens anywhere.
"""

import os
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend, avoids interfering with the Qt event loop
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from PySide6.QtWidgets import QLabel


ROW_COLOR_HEX = {
    "red": "#cc3333",
    "orange": "#cc8800",
    "normal": "#333333",
}


def _collect_case_rows(main_window):
    """Walk case_layout in order, pairing each QLabel with the TestCaseWidget after it."""
    rows = []
    layout = main_window.case_layout
    n = layout.count()
    i = 0
    while i < n:
        item = layout.itemAt(i)
        widget = item.widget() if item else None
        if isinstance(widget, QLabel):
            label_text = widget.text()
            case_widget = None
            if i + 1 < n:
                next_item = layout.itemAt(i + 1)
                candidate = next_item.widget() if next_item else None
                if candidate is not None and hasattr(candidate, "panels"):
                    case_widget = candidate
                    i += 1
            rows.append((label_text, case_widget))
        i += 1
    return rows


def _panel_raw_image(panel):
    """Recover the original (pre-display-transform) pixel array from a panel, if any."""
    if getattr(panel, "image", None) is None:
        return None
    # ImagePanel stores self.image = np.flipud(raw).T for pyqtgraph display.
    # Undo that to get back the natural orientation for the report.
    return np.flipud(panel.image.T)


def _draw_case_page(pdf, label_text, row_color_state, panels):
    n_panels = max(len(panels), 1)
    fig_width = max(4.5 * n_panels, 6)
    fig, axes = plt.subplots(1, n_panels, figsize=(fig_width, 5.2))
    if n_panels == 1:
        axes = [axes]

    fig.suptitle(
        label_text,
        fontsize=13,
        weight="bold",
        color=ROW_COLOR_HEX.get(row_color_state, "#333333"),
    )

    for ax, panel in zip(axes, panels):
        if getattr(panel, "is_na", False) or getattr(panel, "image", None) is None:
            ax.text(0.5, 0.5, "N/A", ha="center", va="center", fontsize=16, color="#888888")
            ax.axis("off")
            continue

        raw = _panel_raw_image(panel)
        ax.imshow(raw, cmap="gray")
        ax.axis("off")

        title_text = getattr(panel.title, "text", lambda: "")()
        min_v, max_v, mean_v = raw.min(), raw.max(), raw.mean()
        negative_flag = " [NEGATIVE]" if getattr(panel, "is_negative", False) else ""

        ax.set_title(
            f"{title_text}\nMin: {min_v:.1f}  Max: {max_v:.1f}  Mean: {mean_v:.1f}{negative_flag}",
            fontsize=8,
            color="#cc3333" if getattr(panel, "is_negative", False) else "#333333",
        )

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    pdf.savefig(fig)
    plt.close(fig)


def export_to_pdf(main_window, path, progress_callback=None):
    """
    Renders the currently loaded case rows to a PDF at `path`.
    progress_callback(value, maximum), if given, is called after each page.
    """
    rows = _collect_case_rows(main_window)
    rows = [(label, widget) for label, widget in rows if widget is not None and widget.panels]

    with PdfPages(path) as pdf:
        # --- Title page ---
        fig = plt.figure(figsize=(11, 8.5))
        fig.text(0.5, 0.62, "TIFF Workspace Analyzer Report", ha="center", fontsize=22, weight="bold")
        fig.text(0.5, 0.55, f"Workspace: {main_window.root or '(none)'}", ha="center", fontsize=11)
        fig.text(
            0.5, 0.50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ha="center", fontsize=11,
        )
        fig.text(0.5, 0.45, f"Test cases: {len(rows)}", ha="center", fontsize=11)
        pdf.savefig(fig)
        plt.close(fig)

        total = len(rows)
        for i, (label_text, case_widget) in enumerate(rows):
            _draw_case_page(pdf, label_text, case_widget.row_color_state, case_widget.panels)
            if progress_callback:
                progress_callback(i + 1, total)

    return path