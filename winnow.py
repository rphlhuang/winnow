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
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QMessageBox, QSizePolicy, QFrame,
    QGraphicsOpacityEffect, QGraphicsProxyWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsOpacityEffect, QGraphicsProxyWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QLineEdit
)
from PyQt6.QtCore import (
    QPoint, QParallelAnimationGroup, QRect, pyqtSignal, QPropertyAnimation, pyqtProperty
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPalette, QAction, QFont, QMouseEvent, QTransform
import csv
import random
import json
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

    class NavigationPdfView(QPdfView):
        def keyPressEvent(self, event):
            # Ignore navigation keys so they bubble up to the parent
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_A, Qt.Key.Key_D, Qt.Key.Key_Escape, Qt.Key.Key_R):
                event.ignore()
            else:
                super().keyPressEvent(event)
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


class CsvWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setStyleSheet("background-color: #111; color: #eee; gridline-color: #444;")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

    def load_csv(self, path):
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        try:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows: return
                
                self.table.setColumnCount(len(rows[0]))
                self.table.setRowCount(len(rows))
                
                for i, row in enumerate(rows):
                    for j, val in enumerate(row):
                        self.table.setItem(i, j, QTableWidgetItem(val))
        except Exception as e:
            print(f"Error reading CSV: {e}")

            print(f"Error reading CSV: {e}")


class NavigationTextEdit(QTextEdit):
    def keyPressEvent(self, event):
        # Ignore navigation keys so they bubble up to the parent (MediaCuller)
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_A, Qt.Key.Key_D, Qt.Key.Key_Escape, Qt.Key.Key_R):
            event.ignore()
        else:
            super().keyPressEvent(event)

class TextWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.text_edit = NavigationTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #111; color: #eee; font-family: monospace; font-size: 14px; border: none;")
        self.layout.addWidget(self.text_edit)

    def load_text(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                self.text_edit.setPlainText(content)
        except Exception as e:
            self.text_edit.setPlainText(f"Error reading file:\n{e}")


class GenericFileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_label)
        
        self.name_label = QLabel()
        self.name_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; margin-top: 20px;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_label)
        
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #aaa; font-size: 16px; margin-top: 10px;")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.details_label)

        # Preload icons
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.icon_file = QPixmap(os.path.join(base_path, "img", "file.png")).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.icon_folder = QPixmap(os.path.join(base_path, "img", "folder.png")).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def set_item(self, path, name, is_dir):
        if is_dir:
            self.icon_label.setPixmap(self.icon_folder)
            self.name_label.setText(name)
            
            try:
                items = os.listdir(path)
                items.sort()
                count = len(items)
                shown_items = items[:10]
                details_text = "\n".join(shown_items)
                if count > 10:
                    details_text += f"\n... and {count - 10} more"
                if count == 0:
                    details_text = "(Empty Folder)"
                self.details_label.setText(details_text)
            except Exception as e:
                self.details_label.setText(f"Error reading folder: {e}")
        else:
            self.icon_label.setPixmap(self.icon_file)
            self.name_label.setText(name)
            self.details_label.setText("Unknown File Type")


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            
    def enterEvent(self, event):
        # Optional hover effect
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)


class QuoteWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: #666; font-style: italic; font-size: 12px; padding: 10px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quotes = []
        self._load_quotes()
        
    def _load_quotes(self):
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_path, "quotes.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.quotes = [(item['quote'], item['author']) for item in data.get('quotes', [])]
        except Exception as e:
            print(f"Error loading quotes: {e}")
            self.quotes = [("The code must go on.", "Anonymous")]

    def refresh_quote(self):
        if not self.quotes: return
        q, a = random.choice(self.quotes)
        self.setText(f'"{q}" — {a}')


class EndWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_msg = QLabel("All files viewed.")
        lbl_msg.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl_msg)
        
        lbl_inst = QLabel("Press 'Esc' to quit\nOR\n'Cmd + R' (or Ctrl + R) to reset log and review all")
        lbl_inst.setStyleSheet("color: #aaa; font-size: 16px; margin-top: 20px;")
        lbl_inst.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl_inst)


class FlagWidget(QWidget):
    name_changed = pyqtSignal(int, str) # index, new_name

    def __init__(self, index, name, color_hex, parent=None):
        super().__init__(parent)
        self.index = index
        self.color_hex = color_hex
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(8)
        self.setToolTip("Click to rename")
        
        # Color Dot
        self.dot = QLabel()
        self.dot.setFixedSize(12, 12)
        self.dot.setStyleSheet(f"background-color: {color_hex}; border-radius: 6px;")
        self.layout.addWidget(self.dot)
        
        # Editable Name
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Name...")
        self.name_edit.setStyleSheet(f"""
            QLineEdit {{
                color: #aaa;
                background: transparent;
                border: none;
                font-size: 13px;
                font-family: sans-serif;
            }}
            QLineEdit:focus {{
                color: {color_hex};
                border-bottom: 1px solid {color_hex};
            }}
        """)
        self.name_edit.setFixedWidth(80)
        self.name_edit.editingFinished.connect(self._emit_change)
        self.layout.addWidget(self.name_edit)
        
        # Key Hint (A, S, D, F)
        keys = ['A', 'S', 'D', 'F']
        self.hint = QLabel(keys[index])
        self.hint.setStyleSheet(f"color: {color_hex}; font-weight: bold; font-size: 10px;")
        self.layout.addWidget(self.hint)

    def _emit_change(self):
        self.name_changed.emit(self.index, self.name_edit.text())
        self.name_edit.clearFocus() # Unfocus after editing

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.name_edit.clearFocus()
            event.accept()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.name_edit.clearFocus() # Triggers editingFinished
            event.accept()
        else:
            super().keyPressEvent(event)

class RotatableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0.0

    @pyqtProperty(float)
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, angle):
        self._rotation = angle
        self.update()

    def paintEvent(self, event):
        if not self.pixmap() or self.pixmap().isNull():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Rotate around center
        w, h = self.width(), self.height()
        center = QPoint(w // 2, h // 2)
        
        painter.translate(center)
        painter.rotate(self._rotation)
        painter.translate(-center)
        
        # Draw normally
        # We need to draw the pixmap exactly as QLabel would (scaled contents are tricky here)
        # But our overlay sets pixmap exactly.
        # However, QLabel usually centers. 
        # For the overlay, we grabbed the stack, so it matches widget size.
        
        # Standard draw
        x = (w - self.pixmap().width()) // 2
        y = (h - self.pixmap().height()) // 2
        painter.drawPixmap(x, y, self.pixmap())


class MediaCuller(QMainWindow):
    def __init__(self, directory):
        super().__init__()
        self.directory = os.path.abspath(directory)
        self.rejected_dir = os.path.join(self.directory, "_rejected") # Keep strict reject folder? 
        # User wants flags instead. We'll use the flag folders.
        self.log_file = os.path.join(self.directory, ".winnow_log") # Move log to hidden file in dir
        
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flags.json")
        self.flags = self._load_flags()

        # Load Viewed Log
        self.viewed_files = self._load_log()

        # Supported Extensions
        self.image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
        self.video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        self.pdf_exts = {'.pdf'} if PDF_SUPPORT else set()
        self.csv_exts = {'.csv'}
        self.txt_exts = {'.txt', '.md', '.log', '.json', '.xml', '.py', '.js', '.html', '.css'}
        
        # Scan files
        self.files = self._scan_directory()
        self.current_index = 0
        
        # Double Esc Logic
        self.esc_pending = False
        self.esc_timer = QTimer()
        self.esc_timer.setSingleShot(True)
        self.esc_timer.timeout.connect(self._reset_esc_pending)
        
        # Quote Logic
        self.files_processed_since_quote = 0
        self.next_quote_threshold = max(3, int(random.gauss(5, 1))) # Initial threshold
        
        # Simple Cache for 1-ahead preload
        self._preload_cache = {}  # {index: QImage}
        self.current_pdf_doc = None  # Hold reference for PDF document

        # Setup GUI
        self.setWindowTitle("winnow")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) # Frameless
        self.resize(1000, 800)
        self.setMinimumSize(400, 300)
        self.drag_pos = None # For dragging functionality
        
        # Main container with layout to hold header and stack
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Header ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_widget.setStyleSheet("background-color: black;") 
        
        # Left: Reject
        self.lbl_reject = ClickableLabel("← reject")
        self.lbl_reject.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 16px;")
        self.lbl_reject.clicked.connect(lambda: self._animate_and_navigate(direction=-1, action='reject'))
        header_layout.addWidget(self.lbl_reject, alignment=Qt.AlignmentFlag.AlignLeft)

        # Center Container (Flags + Filename)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(5)

        # Filename
        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.lbl_filename)
        
        # Flags (Tiny)
        flags_container = QWidget()
        flags_layout = QHBoxLayout(flags_container)
        flags_layout.setContentsMargins(0,0,0,0)
        flags_layout.setSpacing(10)
        flags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.flag_widgets = []
        for i, flag in enumerate(self.flags):
            fw = FlagWidget(i, flag['name'], flag['color'])
            fw.name_changed.connect(self._update_flag_name)
            flags_layout.addWidget(fw)
            self.flag_widgets.append(fw)
            
        center_layout.addWidget(flags_container)
        header_layout.addWidget(center_widget, stretch=1)

        # Right: Keep
        self.lbl_keep = ClickableLabel("keep →")
        self.lbl_keep.setStyleSheet("color: #44ff44; font-weight: bold; font-size: 16px;")
        self.lbl_keep.clicked.connect(lambda: self._animate_and_navigate(direction=1, action='keep'))
        header_layout.addWidget(self.lbl_keep, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(header_widget)
        
        # Hint below header
        hint_widget = QWidget()
        hint_layout = QHBoxLayout(hint_widget)
        hint_layout.setContentsMargins(0, 0, 0, 5)
        self.lbl_hint = QLabel("Left/Right to Reject/Keep • A/S/D/F to Sort • esc to finish")
        self.lbl_hint.setStyleSheet("color: #444; font-size: 10px; font-style: italic;")
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_layout.addWidget(self.lbl_hint)
        self.main_layout.addWidget(hint_widget)
        
        # Stack Container (for animations)
        self.stack_container = QWidget()
        self.stack_layout = QVBoxLayout(self.stack_container)
        self.stack_layout.setContentsMargins(0,0,0,0)
        
        self.stack = QStackedWidget()
        self.stack_layout.addWidget(self.stack)
        
        self.main_layout.addWidget(self.stack_container, stretch=1)
        
        # --- Footer Quote (Visible) ---
        self.quote_label = QuoteWidget()
        self.main_layout.addWidget(self.quote_label)
        # self.quote_label.hide() # Do not hide initially, let load_media decide/or show default
        self.quote_label.show() # Force show as requested "persist at bottom"
        self.quote_label.refresh_quote() # Initial quote
        
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
            self.pdf_view = NavigationPdfView(None)
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            self.stack.addWidget(self.pdf_view)
            
        # CSV View
        self.csv_widget = CsvWidget()
        self.stack.addWidget(self.csv_widget)
        
        # Text View
        self.text_widget = TextWidget()
        self.stack.addWidget(self.text_widget)
        
        # Generic File/Folder View
        self.generic_widget = GenericFileWidget()
        self.stack.addWidget(self.generic_widget)
        
        # End/Done View
        self.end_widget = EndWidget()
        self.stack.addWidget(self.end_widget)
        
        # Media Player Setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # Initial Load
        if not self.files:
            # If files were found originally but filtered out by log, show end screen
            # check raw scan
            raw_files = [f for f in os.listdir(self.directory) if not f.startswith('.') and f != '_rejected' and f != os.path.basename(__file__)]
            if raw_files and len(self.viewed_files) > 0:
                 self._show_end_screen()
            else:
                 print("No media files found.")
                 QTimer.singleShot(0, self._finish_execution)
        else:
            # Clear focus from any initial inputs if any (just in case)
            self.setFocus()
            self._load_media()

    def _load_log(self):
        viewed = set()
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        viewed.add(line.strip())
            except Exception as e:
                print(f"Error reading log: {e}")
        return viewed

    def _log_file_viewed(self, filename):
        if filename not in self.viewed_files:
            self.viewed_files.add(filename)
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(filename + "\n")
            except Exception as e:
                print(f"Error writing to log: {e}")

    def _reset_log(self):
        self.viewed_files.clear()
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except Exception as e:
                print(f"Error resetting log: {e}")
        
        # Rescan
        self.files = self._scan_directory()
        self.current_index = 0
        self._preload_cache.clear()
        
        if self.files:
            self.lbl_reject.show()
            self.lbl_keep.show()
            self.lbl_filename.show()
            self.lbl_hint.show()
            self._load_media()
        else:
            self._show_end_screen()

    def _load_flags(self):
        defaults = [
            {'name': '', 'color': '#ff79c6'}, # A - Pink/Purple
            {'name': '', 'color': '#bd93f9'}, # S - Purple
            {'name': '', 'color': '#8be9fd'}, # D - Cyan
            {'name': '', 'color': '#f1fa8c'}  # F - Yellow
        ]
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Check for legacy defaults and clear them if found
                    legacy_names = {'Reject', 'Maybe', 'Good', 'Best'}
                    for item in loaded:
                        if item.get('name') in legacy_names:
                            item['name'] = ''
                    return loaded
            except:
                pass
        return defaults

    def _save_flags(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.flags, f)
        except Exception as e:
            print(f"Error saving flags: {e}")

    def _update_flag_name(self, index, new_name):
        self.flags[index]['name'] = new_name
        self._save_flags()

    def _show_end_screen(self):
        # Hide header controls
        self.lbl_reject.hide()
        self.lbl_keep.hide()
        self.lbl_filename.hide()
        self.lbl_hint.hide()
        
        self.stack.setCurrentWidget(self.end_widget)
        self.setWindowTitle("winnow - Done")

    def _scan_directory(self):
        found_files = []
        try:
            entries = os.listdir(self.directory)
            entries.sort()
            for f in entries:
                if f.startswith('.') or f == '_rejected': continue
                if f == os.path.basename(__file__): continue
                if f == "flags.json": continue
                
                # Check log
                if f in self.viewed_files: continue
                
                # Check if it's a directory? The requirements say "browses all file types AND folders".
                # But creating flag folders might create a loop if we scan them.
                # We should exclude the flag folders from the scan to avoid moving a folder into itself or similar.
                # Since flag folder names are dynamic, we just rely on "viewed" log or user sense?
                # Best practice: Skip folders that match current flag names? 
                # For now, simplistic scan.
                
                full_path = os.path.join(self.directory, f)
                found_files.append(f)
        except Exception as e:
            print(f"Error scanning directory: {e}")
            sys.exit(1)
        
        print(f"Found {len(found_files)} new items (Total items in dir: {len(entries) if 'entries' in locals() else '?'}).")
        return found_files

    def _load_media(self):
        if self.current_index >= len(self.files):
            self._show_end_screen()
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

        # Check if we should update the quote
        should_refresh_quote = False
        if self.files_processed_since_quote >= self.next_quote_threshold:
            should_refresh_quote = True
            self.files_processed_since_quote = 0
            val = int(random.gauss(5, 1.5))
            self.next_quote_threshold = max(3, min(10, val))

        if should_refresh_quote:
            self.quote_label.refresh_quote()
            
        # Ensure quote is visible (it might have been hidden by specific views previously, restore logic)
        self.quote_label.show() 

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
                # If image load fails, treat as generic
                self.stack.setCurrentWidget(self.generic_widget)
                self.generic_widget.set_item(file_path, filename, False)
                # self.quote_label.show() # Already shown
                
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
                    # Fallback
                    self.stack.setCurrentWidget(self.generic_widget)
                    self.generic_widget.set_item(file_path, filename, False)
            except Exception as e:
                print(f"Error loading PDF: {e}")
                self.stack.setCurrentWidget(self.generic_widget)
                self.generic_widget.set_item(file_path, filename, False)
        
        elif ext in self.csv_exts:
             self.stack.setCurrentWidget(self.csv_widget)
             self.csv_widget.load_csv(file_path)

        elif ext in self.txt_exts:
            self.stack.setCurrentWidget(self.text_widget)
            self.text_widget.load_text(file_path)

        else:
            # Generic File or Folder
            is_dir = os.path.isdir(file_path)
            self.stack.setCurrentWidget(self.generic_widget)
            self.generic_widget.set_item(file_path, filename, is_dir)
            
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        key = event.key()

        # Handle focus clearing if escape is pressed while focusing a widget
        focus_widget = QApplication.focusWidget()
        if focus_widget and isinstance(focus_widget, QLineEdit):
             # The LineEdit handles escape itself (clears focus), so we might check if still focused?
             pass

        # If user presses Esc and NO focus, check double press
        if key == Qt.Key.Key_Escape:
            if focus_widget and isinstance(focus_widget, QLineEdit):
                focus_widget.clearFocus()
                return
            
            if self.esc_pending:
                self.close()
            else:
                self.esc_pending = True
                self.lbl_hint.setText("Press Esc again to exit")
                self.lbl_hint.setStyleSheet("color: #ff5555; font-size: 12px; font-weight: bold;")
                self.esc_timer.start(2000) # 2 seconds window
            return

        # Reset Log Shortcut: Cmd+R
        if key == Qt.Key.Key_R and (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
            self._reset_log()
            return
            
        # If typing in a flag name, don't trigger shortcuts!
        if focus_widget and isinstance(focus_widget, QLineEdit):
            super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_Right:
            self._animate_and_navigate(direction=1, action='keep')
        elif key == Qt.Key.Key_Left:
            self._animate_and_navigate(direction=-1, action='reject')
        elif key == Qt.Key.Key_A:
            self._sort_file(0)
        elif key == Qt.Key.Key_S:
            self._sort_file(1)
        elif key == Qt.Key.Key_D:
            self._sort_file(2)
        elif key == Qt.Key.Key_F:
            self._sort_file(3)
        elif key == Qt.Key.Key_Escape:
            # Already handled above
            pass
        else:
            super().keyPressEvent(event)

    def _reset_esc_pending(self):
        self.esc_pending = False
        # Restore hint text
        self.lbl_hint.setText("Left/Right to Reject/Keep • A/S/D/F to Sort • esc to finish")
        self.lbl_hint.setStyleSheet("color: #444; font-size: 10px; font-style: italic;")

    def _sort_file(self, flag_index):
        if self.current_index >= len(self.files): return
        
        filename = self.files[self.current_index]
        flag = self.flags[flag_index]
        target_dir = os.path.join(self.directory, flag['name'])
        
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except:
                print(f"Could not create {target_dir}")
                return

        src = os.path.join(self.directory, filename)
        dst = os.path.join(target_dir, filename)
        
        # Handle collision
        if os.path.exists(dst):
             base, ext = os.path.splitext(filename)
             import uuid
             dst = os.path.join(target_dir, f"{base}_{uuid.uuid4().hex[:6]}{ext}")
             
        try:
            # Release handles
            self.player.stop()
            self.player.setSource(QUrl())
            self.image_widget.set_pixmap(None)
            if PDF_SUPPORT:
                self.pdf_view.setDocument(None)
            self.current_pdf_doc = None
            
            shutil.move(src, dst)
            print(f"Moved {filename} to {flag['name']}")
            
            # Log
            self._log_file_viewed(filename)
            
            # Animate
            self._animate_sort(flag_index)
            
            # Next
            del self.files[self.current_index]
            if self.current_index in self._preload_cache:
                del self._preload_cache[self.current_index]
            self._load_media()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move file: {e}")

    def _animate_sort(self, flag_index):
        # 1. Grab visual
        current_pixmap = self.stack.grab()
        
        # 2. Overlay
        # Use RotatableLabel for tilt
        overlay = RotatableLabel(self.stack_container)
        overlay.setPixmap(current_pixmap)
        overlay.setGeometry(self.stack.geometry())
        overlay.show()
        
        # 3. Setup Animation
        # Direction logic:
        # A (0): Left Left
        # S (1): Left
        # D (2): Right
        # F (3): Right Right
        
        # Tilt logic:
        # A: -15, S: -5, D: +5, F: +15
        
        tilts = [-15, -5, 5, 15]
        shifts_x = [-200, -50, 50, 200]
        
        end_x = overlay.x() + shifts_x[flag_index]
        end_y = overlay.y() - 400 # Upwards
        end_rot = tilts[flag_index]
        
        anim_group = QParallelAnimationGroup(overlay)
        
        # Pos
        anim_pos = QPropertyAnimation(overlay, b"pos")
        anim_pos.setDuration(300)
        anim_pos.setStartValue(overlay.pos())
        anim_pos.setEndValue(QPoint(end_x, end_y))
        anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Rotation
        anim_rot = QPropertyAnimation(overlay, b"rotation")
        anim_rot.setDuration(300)
        anim_rot.setStartValue(0.0)
        anim_rot.setEndValue(end_rot)
        
        # Opacity
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)
        anim_op = QPropertyAnimation(effect, b"opacity")
        anim_op.setDuration(300)
        anim_op.setStartValue(1.0)
        anim_op.setEndValue(0.0)
        
        anim_group.addAnimation(anim_pos)
        anim_group.addAnimation(anim_rot)
        anim_group.addAnimation(anim_op)
        
        anim_group.finished.connect(overlay.deleteLater)
        anim_group.start()

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
            
            # Log
            self._log_file_viewed(filename)

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
            # Log keep as viewed? Probably. The user made a decision.
            # But "keep" implies staying in folder. So yes, viewed.
            current_file = self.files[self.current_index]
            self._log_file_viewed(current_file)
            
            self.current_index += 1
            self.files_processed_since_quote += 1
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
