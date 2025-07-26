import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QLabel, QSlider, QSplitter, QStyle, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
import cv2
import numpy as np
import qtawesome as qta
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QTime, QEvent, Signal
from PySide6.QtGui import QImage, QPixmap, QIcon, QKeyEvent, QPainter, QKeySequence


class FrameDisplayWidget(QWidget):
    """A widget to display a pixmap with a fixed aspect ratio."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setMinimumSize(160, 90) # Minimum size with 16:9 ratio

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update() # Trigger a repaint

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return
        
        painter = QPainter(self)
        target_rect = self.rect()
        
        pixmap_scaled = self._pixmap.scaled(target_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Center the pixmap
        x = (target_rect.width() - pixmap_scaled.width()) / 2
        y = (target_rect.height() - pixmap_scaled.height()) / 2
        
        painter.drawPixmap(x, y, pixmap_scaled)

    def sizeHint(self):
        return self.minimumSize()

    def heightForWidth(self, width):
        return width * 9 / 16


class VideoControlWidget(QWidget):
    """왼쪽 패널: 비디오 컨트롤, 프레임 디스플레이, 시간 정보 등을 관리하는 위젯"""
    record_requested = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        self.start_time = 0
        self.end_time = 0

        # Layout
        main_layout = QVBoxLayout(self)

        # 1. Main Video Display
        main_layout.addWidget(self.video_widget, stretch=5)

        # 2. Timeline Slider and Time Display
        slider_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00:00 / 00:00:00")
        
        self.play_icon = qta.icon('fa5s.play')
        self.pause_icon = qta.icon('fa5s.pause')
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.play_icon)
        self.play_pause_button.setFlat(True)

        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.time_label)
        slider_layout.addWidget(self.play_pause_button)
        main_layout.addLayout(slider_layout)


        # 3. Frame Displays and Buttons
        frames_layout = QHBoxLayout()
        
        # Start Frame
        start_frame_layout = QVBoxLayout()
        self.start_frame_widget = FrameDisplayWidget()
        self.set_start_button = QPushButton("Set Start")
        start_frame_layout.addWidget(self.start_frame_widget, stretch=1)
        start_frame_layout.addWidget(self.set_start_button)
        
        # End Frame
        end_frame_layout = QVBoxLayout()
        self.end_frame_widget = FrameDisplayWidget()
        self.set_end_button = QPushButton("Set End")
        end_frame_layout.addWidget(self.end_frame_widget, stretch=1)
        end_frame_layout.addWidget(self.set_end_button)

        frames_layout.addLayout(start_frame_layout)
        frames_layout.addLayout(end_frame_layout)
        main_layout.addLayout(frames_layout, stretch=3) # Increased stretch factor

        # 4. Time Info Labels
        time_info_layout = QHBoxLayout()
        self.start_time_label = QLabel("Start: 00:00:00.000")
        self.end_time_label = QLabel("End: 00:00:00.000")
        
        # Apply bootstrap-like style
        label_style = """
            QLabel {
                background-color: #e7f3fe;
                border: 1px solid #d0e3f0;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
        """
        self.start_time_label.setStyleSheet(label_style)
        self.end_time_label.setStyleSheet(label_style)
        
        time_info_layout.addWidget(self.start_time_label)
        time_info_layout.addWidget(self.end_time_label)
        main_layout.addLayout(time_info_layout)
        
        self.interval_label = QLabel("Interval: 00:00:00.000")
        font = self.interval_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.interval_label.setFont(font)
        self.interval_label.setAlignment(Qt.AlignCenter)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_label, stretch=1)
        self.record_button = QPushButton("Record")
        interval_layout.addWidget(self.record_button)
        
        main_layout.addLayout(interval_layout)

        self.setLayout(main_layout)

        self.record_button.clicked.connect(self.on_record_clicked)

    def on_record_clicked(self):
        start_text = self.start_time_label.text().replace("Start: ", "")
        end_text = self.end_time_label.text().replace("End: ", "")
        interval_text = self.interval_label.text().replace("Interval: ", "")
        if interval_text != "00:00:00.000":
            self.record_requested.emit(start_text, end_text, interval_text)

class MainWindow(QMainWindow):
    """메인 윈도우: 전체 레이아웃과 파일 목록을 관리"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BONI")
        self.setGeometry(100, 100, 1280, 720)
        
         # Set application icon
        icon = QIcon("boni.png")
        self.setWindowIcon(icon)
        # File data storage
        self.file_data = {}
        self.video_capture = None

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left panel
        self.video_control_widget = VideoControlWidget()
        splitter.addWidget(self.video_control_widget)

        # Middle panel (new)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Start", "End", "Interval"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        splitter.addWidget(self.table_widget)

        # Right panel
        self.file_list_widget = QListWidget()
        self.file_list_widget.setAcceptDrops(True)
        splitter.addWidget(self.file_list_widget)
        
        splitter.setSizes([800, 400, 280])
        
        # Install event filter for drag and drop
        self.file_list_widget.installEventFilter(self)


        # --- Signal Connections ---
        self.file_list_widget.currentItemChanged.connect(self.current_file_changed)

        self.video_control_widget.set_start_button.clicked.connect(self.set_start_keyframe)
        self.video_control_widget.set_end_button.clicked.connect(self.set_end_keyframe)
        self.video_control_widget.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.video_control_widget.record_requested.connect(self.add_record_to_table)


        player = self.video_control_widget.media_player
        player.positionChanged.connect(self.position_changed)
        player.durationChanged.connect(self.duration_changed)
        player.mediaStatusChanged.connect(self.media_status_changed)
        self.video_control_widget.slider.sliderMoved.connect(self.set_position)

    def eventFilter(self, source, event):
        if source is self.file_list_widget:
            if event.type() == event.Type.DragEnter:
                if event.mimeData().hasUrls():
                    # Check if any of the files are mp4
                    for url in event.mimeData().urls():
                        if url.toLocalFile().lower().endswith('.mp4'):
                            event.acceptProposedAction()
                            return True
                event.ignore()
                return True
            elif event.type() == event.Type.Drop:
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.mp4'):
                        # Check for duplicates by file name
                        file_name = file_path.split('/')[-1]
                        items = self.file_list_widget.findItems(file_name, Qt.MatchExactly)
                        if not items:
                            self.file_list_widget.addItem(file_name)
                            self.file_data[file_path] = {
            'start': 0, 
            'end': 0, 
            'start_frame': None, 
            'end_frame': None,
            'intervals': []  # Store intervals for this file
        }
                return True
        return super().eventFilter(source, event)

    def current_file_changed(self, current, previous):
        if not current:
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            self.update_ui_for_current_file()
            return
        
        # Pause playback before switching files
        player = self.video_control_widget.media_player
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.pause()
            self.video_control_widget.play_pause_button.setIcon(self.video_control_widget.play_icon)
        
        file_path = self.get_selected_filepath()
        if file_path:
            self.video_control_widget.media_player.setSource(QUrl.fromLocalFile(file_path))
            if self.video_capture:
                self.video_capture.release()
            self.video_capture = cv2.VideoCapture(file_path)
            # The mediaStatusChanged signal will handle the rest
            
        # Update UI including the table for the new file
        self.update_ui_for_current_file()
        self.update_table_for_current_file()
            
    def media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.video_control_widget.media_player.play()
            self.video_control_widget.media_player.pause()
            self.update_ui_for_current_file()

    def get_selected_filepath(self):
        current_item = self.file_list_widget.currentItem()
        if not current_item:
            return None
            
        current_text = current_item.text()
        for path in self.file_data:
            if path.endswith(current_text):
                return path
        return None

    def set_start_keyframe(self):
        file_path = self.get_selected_filepath()
        if not file_path:
            return
        
        position = self.video_control_widget.media_player.position()
        self.file_data[file_path]['start'] = position
        
        if self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_MSEC, position)
            ret, frame = self.video_capture.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.file_data[file_path]['start_frame'] = pixmap
        
        self.update_ui_for_current_file()
        
    def set_end_keyframe(self):
        file_path = self.get_selected_filepath()
        if not file_path:
            return
            
        position = self.video_control_widget.media_player.position()
        self.file_data[file_path]['end'] = position
        
        if self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_MSEC, position)
            ret, frame = self.video_capture.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.file_data[file_path]['end_frame'] = pixmap

        self.update_ui_for_current_file()

    def position_changed(self, position):
        self.video_control_widget.slider.setValue(position)
        duration = self.video_control_widget.media_player.duration()
        self.video_control_widget.time_label.setText(
            f"{self.format_time(position)} / {self.format_time(duration)}"
        )

    def duration_changed(self, duration):
        self.video_control_widget.slider.setRange(0, duration)
        position = self.video_control_widget.media_player.position()
        self.video_control_widget.time_label.setText(
            f"{self.format_time(position)} / {self.format_time(duration)}"
        )

    def set_position(self, position):
        self.video_control_widget.media_player.setPosition(position)

    def toggle_play_pause(self):
        player = self.video_control_widget.media_player
        button = self.video_control_widget.play_pause_button
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.pause()
            button.setIcon(self.video_control_widget.play_icon)
        else:
            player.play()
            button.setIcon(self.video_control_widget.pause_icon)

    def keyPressEvent(self, event: QKeyEvent):
        # Play/Pause with spacebar - ensure it works globally
        if event.key() == Qt.Key.Key_P and event.modifiers() == Qt.ControlModifier:
            self.toggle_play_pause()
            event.accept()  # Mark event as handled
            return
            
        # Set start with Ctrl+1
        if event.key() == Qt.Key.Key_1 and event.modifiers() == Qt.ControlModifier:
            self.set_start_keyframe()
            return
            
        # Set end with Ctrl+2
        if event.key() == Qt.Key.Key_2 and event.modifiers() == Qt.ControlModifier:
            self.set_end_keyframe()
            return
            
        # Record with Ctrl+Enter
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.video_control_widget.record_button.click()
            return

        # Video seeking with arrow keys
        if not self.table_widget.hasFocus():
            player = self.video_control_widget.media_player
            if event.key() == Qt.Key.Key_Left:
                player.setPosition(player.position() - 33)
                return
            elif event.key() == Qt.Key.Key_Right:
                player.setPosition(player.position() + 33)
                return

        # Table copy-paste handling
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_table_content()
        elif event.matches(QKeySequence.StandardKey.SelectAll):
            if self.table_widget.hasFocus():
                self.table_widget.selectAll()
        else:
            super().keyPressEvent(event)

    def copy_table_content(self):
        if not self.table_widget.hasFocus():
            return
            
        selected_ranges = self.table_widget.selectedRanges()
        if not selected_ranges:
            return

        header_text = "\t".join([self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())])
        
        s = header_text + "\n"

        for r in range(self.table_widget.rowCount()):
            row_data = []
            for c in range(self.table_widget.columnCount()):
                item = self.table_widget.item(r, c)
                if item and item.isSelected():
                    row_data.append(item.text())
            if row_data:
                 s += "\t".join(row_data) + "\n"
        
        QApplication.clipboard().setText(s)

    def add_record_to_table(self, start, end, interval):
        file_path = self.get_selected_filepath()
        if not file_path:
            return
            
        # Add record to current file's interval list
        self.file_data[file_path]['intervals'].append((start, end, interval))
        self.update_table_for_current_file()
        
    def update_table_for_current_file(self):
        """Update table widget with intervals for the current file"""
        self.table_widget.setRowCount(0)  # Clear table
        
        file_path = self.get_selected_filepath()
        if not file_path:
            return
            
        intervals = self.file_data[file_path].get('intervals', [])
        for start, end, interval in intervals:
            row_count = self.table_widget.rowCount()
            self.table_widget.insertRow(row_count)
            self.table_widget.setItem(row_count, 0, QTableWidgetItem(start))
            self.table_widget.setItem(row_count, 1, QTableWidgetItem(end))
            self.table_widget.setItem(row_count, 2, QTableWidgetItem(interval))
            
        # Resize columns after updating
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def format_time(self, ms):
        time = QTime(0, 0, 0, 0).addMSecs(ms)
        return time.toString("HH:mm:ss.zzz")

    def update_ui_for_current_file(self):
        file_path = self.get_selected_filepath()
        if not file_path:
            # Clear all UI elements
            self.video_control_widget.start_time_label.setText("Start: 00:00:00.000")
            self.video_control_widget.end_time_label.setText("End: 00:00:00.000")
            self.video_control_widget.interval_label.setText("Interval: 00:00:00.000")
            self.video_control_widget.start_frame_widget.setPixmap(QPixmap())
            self.video_control_widget.end_frame_widget.setPixmap(QPixmap())
            return

        data = self.file_data[file_path]
        start_time = data.get('start', 0)
        end_time = data.get('end', 0)
        start_frame = data.get('start_frame')
        end_frame = data.get('end_frame')

        # Update time labels
        self.video_control_widget.start_time_label.setText(f"Start: {self.format_time(start_time)}")
        self.video_control_widget.end_time_label.setText(f"End: {self.format_time(end_time)}")
        
        interval = abs(end_time - start_time) if end_time > 0 and start_time > 0 else 0
        self.video_control_widget.interval_label.setText(f"Interval: {self.format_time(interval)}")

        # Update frame images
        if start_frame and not start_frame.isNull():
            self.video_control_widget.start_frame_widget.setPixmap(start_frame)
        else:
            self.video_control_widget.start_frame_widget.setPixmap(QPixmap())

        if end_frame and not end_frame.isNull():
            self.video_control_widget.end_frame_widget.setPixmap(end_frame)
        else:
            self.video_control_widget.end_frame_widget.setPixmap(QPixmap())
            
        # Also update the table for the current file
        self.update_table_for_current_file()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
