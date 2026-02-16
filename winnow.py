import sys
import os
import shutil
import glob
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QMessageBox, QSizePolicy, QFrame,
    QGraphicsOpacityEffect, QGraphicsProxyWidget
)
from PyQt6.QtCore import (
    Qt, QUrl, QSize, QTimer, QPropertyAnimation, QEasingCurve, 
    QPoint, QParallelAnimationGroup, QRect
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPalette, QAction
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

# High DPI Support
if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

try:
    from PyQt6.QtPdf import QPdfDocument
    from PyQt6.QtPdfWidgets import QPdfView
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: PyQt6.QtPdf not found. PDF support disabled.")



class ImageWidget(QWidget):
    """
    A custom widget to display an image centered and scaled, maintaining aspect ratio.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        # Set background to black
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.black)
        self.setAutoFillBackground(True)
        self.setPalette(pal)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if not self.pixmap or self.pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Calculate scaling to fit window while keeping aspect ratio
        w_widget = self.width()
        h_widget = self.height()
        
        if w_widget <= 0 or h_widget <= 0:
            return

        scaled_pixmap = self.pixmap.scaled(
            QSize(w_widget, h_widget),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Center draw position
        x = (w_widget - scaled_pixmap.width()) // 2
        y = (h_widget - scaled_pixmap.height()) // 2
        
        painter.drawPixmap(x, y, scaled_pixmap)


class MediaCuller(QMainWindow):
    def __init__(self, directory):
        super().__init__()
        self.directory = os.path.abspath(directory)
        self.rejected_dir = os.path.join(self.directory, "_rejected")

        # Supported Extensions
        self.image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
        self.video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        self.pdf_exts = {'.pdf'} if PDF_SUPPORT else set()
        
        # Scan files
        self.files = self._scan_directory()
        self.current_index = 0
        
        # Simple Cache for 1-ahead preload
        self._preload_cache = {}  # {index: QImage}
        self.current_pdf_doc = None  # Hold reference for PDF document

        # Setup GUI
        # Setup GUI
        self.setWindowTitle("winnow")
        self.resize(1000, 700)
        self.setMinimumSize(400, 300)
        
        # Main container with layout to hold header and stack
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Value Proposition Header ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)
        # Completely black, no borders as requested (or minimalist)
        header_widget.setStyleSheet("background-color: black;") 

        # Left: Reject
        self.lbl_reject = QLabel("← reject")
        self.lbl_reject.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.lbl_reject, alignment=Qt.AlignmentFlag.AlignLeft)

        # Center: Filename
        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("color: white; font-size: 14px;")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.lbl_filename, stretch=1)

        # Right: Keep
        self.lbl_keep = QLabel("keep →")
        self.lbl_keep.setStyleSheet("color: #44ff44; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.lbl_keep, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(header_widget)
        
        # Stack Container (for animations)
        self.stack_container = QWidget()
        self.stack_layout = QVBoxLayout(self.stack_container)
        self.stack_layout.setContentsMargins(0,0,0,0)
        
        self.stack = QStackedWidget()
        self.stack_layout.addWidget(self.stack)
        
        self.main_layout.addWidget(self.stack_container, stretch=1)
        
        # Image View
        self.image_widget = ImageWidget()
        self.stack.addWidget(self.image_widget)
        
        # Video View
        self.video_container = QWidget()
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        # QVideoWidget usually handles aspect ratio well by default or can be set
        # self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        video_layout.addWidget(self.video_widget)
        
        self.stack.addWidget(self.video_container)

        # PDF View
        if PDF_SUPPORT:
            self.pdf_view = QPdfView(None)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            self.stack.addWidget(self.pdf_view)
        
        # Media Player Setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # Ensure rejected folder exists
        if not os.path.exists(self.rejected_dir):
            try:
                os.makedirs(self.rejected_dir)
            except OSError as e:
                print(f"Error creating rejected folder: {e}")
                sys.exit(1)
        
        # Initial Load
        if not self.files:
            print("No media files found.")
            QTimer.singleShot(0, self._finish_execution)
        else:
            self._load_media()

    def _scan_directory(self):
        found_files = []
        try:
            entries = os.listdir(self.directory)
            entries.sort()
            for f in entries:
                if f.startswith('.'): continue
                ext = os.path.splitext(f)[1].lower()
                if ext in self.image_exts or ext in self.video_exts or ext in self.pdf_exts:
                    full_path = os.path.join(self.directory, f)
                    if os.path.isfile(full_path):
                        found_files.append(f)
        except Exception as e:
            print(f"Error scanning directory: {e}")
            sys.exit(1)
        
        print(f"Found {len(found_files)} media files.")
        return found_files

    def _load_media(self):
        if self.current_index >= len(self.files):
            self._finish_execution()
            return

        filename = self.files[self.current_index]
        file_path = os.path.join(self.directory, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        self.setWindowTitle("winnow")
        self.lbl_filename.setText(f"{self.current_index + 1}/{len(self.files)}: {filename}")
        
        # Reset Player
        self.player.stop()
        self.player.setSource(QUrl())
        self.image_widget.set_pixmap(None) # Clear previous image
        self.current_pdf_doc = None # Clear PDF doc reference

        if ext in self.image_exts:
            self.stack.setCurrentWidget(self.image_widget)
            
            # Check cache
            if self.current_index in self._preload_cache:
                qimg = self._preload_cache.pop(self.current_index)
                pixmap = QPixmap.fromImage(qimg)
            else:
                pixmap = QPixmap(file_path)
            
            if not pixmap.isNull():
                self.image_widget.set_pixmap(pixmap)
            else:
                print(f"Failed to load image: {filename}")
                
        elif ext in self.video_exts:
            self.stack.setCurrentWidget(self.video_container)
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
        
        elif PDF_SUPPORT and ext in self.pdf_exts:
            self.stack.setCurrentWidget(self.pdf_view)
            self.current_pdf_doc = QPdfDocument(self)
            try:
                self.current_pdf_doc.load(file_path)
                if self.current_pdf_doc.status() == QPdfDocument.Status.Ready:
                    self.pdf_view.setDocument(self.current_pdf_doc)
                else:
                    print(f"Failed to load PDF: {filename} (Status: {self.current_pdf_doc.status()})")
            except Exception as e:
                print(f"Error loading PDF: {e}")
            
        # Trigger Preload for next item
        self._preload_next()

    def _preload_next(self):
        next_idx = self.current_index + 1
        if next_idx < len(self.files):
            fname = self.files[next_idx]
            ext = os.path.splitext(fname)[1].lower()
            if ext in self.image_exts and next_idx not in self._preload_cache:
                path = os.path.join(self.directory, fname)
                # Load QImage in a way that doesn't block too much. 
                # For a simple script, doing it directly is usually fine unless images are massive.
                # To be super smooth, use a QThread, but avoiding complexity for "complete single file".
                # We'll just load it. If user notices lag, they can ask for optimization.
                img = QImage(path)
                if not img.isNull():
                    self._preload_cache[next_idx] = img

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Right:
            self._animate_and_navigate(direction=1, action='keep')
        elif key == Qt.Key.Key_Left or key == Qt.Key.Key_D:
            self._animate_and_navigate(direction=-1, action='reject')
        elif key == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _move_to_rejected(self):
        if self.current_index >= len(self.files):
            return

        filename = self.files[self.current_index]
        src = os.path.join(self.directory, filename)
        dst = os.path.join(self.rejected_dir, filename)
        
        # Avoid overwrite
        if os.path.exists(dst):
            base, ext = os.path.splitext(filename)
            import uuid
            dst = os.path.join(self.rejected_dir, f"{base}_{uuid.uuid4().hex[:6]}{ext}")

        try:
            # Release file handles if possible
            self.player.stop()
            self.player.setSource(QUrl())
            self.image_widget.set_pixmap(None)
            if PDF_SUPPORT:
                self.pdf_view.setDocument(None)
            self.current_pdf_doc = None
            
            shutil.move(src, dst)
            print(f"Moved '{filename}' to rejected.")
            
            # Remove from list
            del self.files[self.current_index]
            
            # Don't increment index, just refresh current (which is now the next item)
            # Clear cache for this index if it existed (unlikely as we just viewed it)
            if self.current_index in self._preload_cache:
                del self._preload_cache[self.current_index]
                
            self._load_media()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move file:\n{e}")

    def _animate_and_navigate(self, direction, action):
        """
        Animate the current view sliding off to 'direction' (Left: -1, Right: 1).
        Then perform the action (keep/reject) and load next.
        """
        if self.current_index >= len(self.files):
            return

        # 1. Grab current visual state
        current_pixmap = self.stack.grab()
        
        # 2. Create overlay widget for animation
        overlay = QLabel(self.stack_container)
        overlay.setPixmap(current_pixmap)
        overlay.setGeometry(self.stack.geometry())
        overlay.show()
        
        # 3. Perform Logic seamlessly behind the overlay
        if action == 'reject':
            self._move_to_rejected()
            # _move_to_rejected calls _load_media(), updating self.stack
        elif action == 'keep':
            self.current_index += 1
            self._load_media()
            
        # 4. Setup Animation
        # Slide off screen to Left (-width) or Right (+width)
        end_x = -self.stack.width() if direction == -1 else self.stack.width()
        
        anim_group = QParallelAnimationGroup(overlay)
        
        # Position Animation
        anim_pos = QPropertyAnimation(overlay, b"pos")
        anim_pos.setDuration(250) # Lightweight, quick
        anim_pos.setStartValue(overlay.pos())
        anim_pos.setEndValue(QPoint(end_x, overlay.y()))
        anim_pos.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Opacity Animation (Fade out)
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)
        anim_op = QPropertyAnimation(effect, b"opacity")
        anim_op.setDuration(250)
        anim_op.setStartValue(1.0)
        anim_op.setEndValue(0.0)
        
        anim_group.addAnimation(anim_pos)
        anim_group.addAnimation(anim_op)
        
        # Cleanup when done
        anim_group.finished.connect(overlay.deleteLater)
        anim_group.start()


    def _finish_execution(self):
        QMessageBox.information(self, "Done", "All files processed.")
        self.close()

if __name__ == "__main__":
    app_target_dir = os.getcwd() # Default
    if len(sys.argv) > 1:
        app_target_dir = sys.argv[1]
    
    if not os.path.isdir(app_target_dir):
        print(f"Error: '{app_target_dir}' is not a directory.")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MediaCuller(app_target_dir)
    window.show()
    sys.exit(app.exec())
