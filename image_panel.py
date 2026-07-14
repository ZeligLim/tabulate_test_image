import os
import numpy as np
import tifffile
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class ImagePanel(QWidget):
    """
    Displays a single TIFF (or N/A placeholder) with:
      - a title label
      - a pyqtgraph image view (pannable/zoomable)
      - a stats sidebar (min/max/mean/size)
      - a live histogram of pixel values
      - optional ROI (rectangle) that live-updates stats/histogram

    title_mode:
        "filename"  -> title is the basename of `filename`
        "parent_k"  -> title is the name of the K-folder two levels up
                       from `filename` (root/K/case/file.tiff -> "K")
    is_na:
        Explicit override for "file doesn't exist / not applicable".
        If not given, it's inferred from os.path.exists(filename).
    """

    def __init__(self, filename, title_mode="filename", is_na=None, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.is_negative = False
        self.roi = None
        self.image = None
        self.w = self.h = 0

        self.is_na = (not os.path.exists(filename)) if is_na is None else is_na

        display_title = self._resolve_title(filename, title_mode)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)

        self.title = QLabel(display_title)
        self.title.setStyleSheet("font-size: 13px; font-weight: bold; padding-bottom: 4px; color: #aaaaaa;")

        title_row = QHBoxLayout()
        title_row.addWidget(self.title, stretch=1)

        self.roi_btn = QPushButton("ROI")
        self.roi_btn.setCheckable(True)
        self.roi_btn.setFixedSize(40, 22)
        self.roi_btn.setStyleSheet(
            "QPushButton { background-color: #333333; color: white; font-size: 10px; border-radius: 3px; }"
            "QPushButton:checked { background-color: #cc3333; }"
        )
        self.roi_btn.toggled.connect(self.enable_roi)
        title_row.addWidget(self.roi_btn)

        main_layout.addLayout(title_row)

        content_layout = QHBoxLayout()

        if self.is_na:
            self.roi_btn.setVisible(False)
            self.na_label = QLabel("N/A")
            self.na_label.setAlignment(Qt.AlignCenter)
            self.na_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #555555; "
                "background-color: #111111; border: 1px dashed #333333; border-radius: 4px;"
            )
            content_layout.addWidget(self.na_label, stretch=1)

            right_panel = QVBoxLayout()
            self.stats = QLabel("No Data Available")
            self.stats.setStyleSheet("font-family: monospace; font-size: 11px; color: #666666; padding: 4px;")
            right_panel.addWidget(self.stats)
            right_panel.addStretch()
            content_layout.addLayout(right_panel)

        else:
            try:
                raw_image = tifffile.imread(filename)
                if raw_image.ndim > 2:
                    raw_image = raw_image[0]

                if raw_image.size > 0 and np.min(raw_image) < 0:
                    self.is_negative = True

                self.image = np.flipud(raw_image).T
                self.w, self.h = self.image.shape[:2]

                self.view = pg.PlotWidget()
                self.view.setAspectLocked(True)
                self.view.showAxis('left', False)
                self.view.showAxis('bottom', False)
                self.view.getViewBox().setLimits(
                    xMin=-self.w * 0.9, xMax=self.w * 1.9,
                    yMin=-self.h * 0.9, yMax=self.h * 1.9
                )

                self.img_item = pg.ImageItem()
                self.img_item.setImage(self.image)
                self.view.addItem(self.img_item)
                content_layout.addWidget(self.view, stretch=1)

                right_panel = QVBoxLayout()
                self.stats = QLabel()
                self.stats.setStyleSheet(
                    "font-family: monospace; font-size: 11px; background-color: #000000; color: #ffffff; padding: 4px;"
                )
                right_panel.addWidget(self.stats)

                self.hist = pg.PlotWidget()
                self.hist.setFixedWidth(140)
                self.hist.setMinimumHeight(150)
                self.hist.setMouseEnabled(x=False, y=False)
                self.hist.enableAutoRange(axis='xy')
                right_panel.addWidget(self.hist)
                content_layout.addLayout(right_panel)

            except Exception as e:
                self.is_na = True
                self.roi_btn.setVisible(False)
                err_label = QLabel(f"Load Error:\n{e}")
                err_label.setAlignment(Qt.AlignCenter)
                err_label.setWordWrap(True)
                err_label.setStyleSheet("color: #ff6666; font-size: 11px; padding: 8px;")
                content_layout.addWidget(err_label, stretch=1)
                self.stats = QLabel("")
                content_layout.addWidget(self.stats)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        if not self.is_na and self.image is not None:
            self.update_stats()

    @staticmethod
    def _resolve_title(filename, title_mode):
        if title_mode == "parent_k":
            # filename == root/K/case/debug_After_normalize.tiff
            case_dir = os.path.dirname(filename)
            k_dir = os.path.dirname(case_dir)
            return os.path.basename(k_dir)
        return os.path.basename(filename)

    def enable_roi(self, on):
        """Toggle ROI mode for this panel. Called from MainWindow.toggle_roi()."""
        if self.is_na or self.image is None:
            return

        if on:
            rw, rh = min(200, self.w // 2), min(200, self.h // 2)
            self.roi = pg.RectROI([self.w // 4, self.h // 4], [rw, rh], pen='r')
            self.view.addItem(self.roi)
            self.roi.sigRegionChanged.connect(self.update_stats)
        else:
            if self.roi:
                self.view.removeItem(self.roi)
                self.roi = None
        self.update_stats()

    def update_stats(self):
        if self.is_na or self.image is None:
            return

        data = self.image
        if self.roi:
            pos = self.roi.pos()
            size = self.roi.size()
            x0 = max(0, min(int(pos.x()), self.w - 1))
            y0 = max(0, min(int(pos.y()), self.h - 1))
            x1 = max(0, min(int(pos.x() + size.x()), self.w))
            y1 = max(0, min(int(pos.y() + size.y()), self.h))
            data = self.image[min(x0, x1):max(x0, x1), min(y0, y1):max(y0, y1)]

        if data is None or data.size == 0:
            self.stats.setText("No pixels")
            self.hist.clear()
            return

        min_val = data.min()
        min_style = "color: #ff4444; font-weight: bold;" if min_val < 0 else "font-weight: bold;"

        self.stats.setText(
            f"<span style='{min_style}'>Min : {min_val:.1f}</span><br>"
            f"<b>Max</b> : {data.max():.1f}<br>"
            f"<b>Mean</b>: {data.mean():.1f}<br>"
            f"<b>Size</b>: {data.size}"
        )

        self.hist.clear()
        counts, edges = np.histogram(data.flatten(), bins=256)
        bg = pg.BarGraphItem(
            x=counts / 2.0,
            y=(edges[:-1] + edges[1:]) / 2.0,
            width=counts,
            height=np.diff(edges),
            brush=(70, 130, 180, 140),
            pen=pg.mkPen((70, 130, 180), width=1),
        )
        self.hist.addItem(bg)