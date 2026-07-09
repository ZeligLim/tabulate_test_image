import os
import numpy as np
import tifffile
from PySide6.QtCore import QRunnable, QObject, Signal

class LoaderSignals(QObject):
    # Sends: (index, raw_image_array, file_path, is_negative_flag)
    loaded = Signal(int, object, str, bool)
    error = Signal(int, str)

class ImageLoadWorker(QRunnable):
    def __init__(self, index, file_path, is_na):
        super().__init__()
        self.index = index
        self.file_path = file_path
        self.is_na = is_na
        self.signals = LoaderSignals()

    def run(self):
        if self.is_na or not os.path.exists(self.file_path):
            self.signals.loaded.emit(self.index, None, self.file_path, False)
            return

        try:
            # Heavy I/O Operation safely isolated on background worker thread
            raw_image = tifffile.imread(self.file_path)
            if raw_image.ndim > 2:
                raw_image = raw_image[0]
            
            is_negative = False
            if raw_image.size > 0 and np.min(raw_image) < 0:
                is_negative = True
                
            self.signals.loaded.emit(self.index, raw_image, self.file_path, is_negative)
        except Exception as e:
            self.signals.error.emit(self.index, str(e))