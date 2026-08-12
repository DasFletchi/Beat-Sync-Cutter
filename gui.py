import sys
import os
import threading
import subprocess
import numpy as np
import librosa

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar, QDoubleSpinBox,
    QLineEdit, QComboBox, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon

def get_video_duration(video_path):
    cmd = ["ffprobe", "-i", video_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
            hours, mins, secs = float(parts[0]), float(parts[1]), float(parts[2])
            return hours * 3600 + mins * 60 + secs
    return 0.0

class WorkerSignals(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

class SyncWorker(threading.Thread):
    def __init__(self, video_path, audio_path, output_path, min_cut_dur, scale, signals):
        super().__init__()
        self.video_path = video_path
        self.audio_path = audio_path
        self.output_path = output_path
        self.min_cut_dur = min_cut_dur
        self.scale = scale
        self.signals = signals

    def run(self):
        try:
            self.signals.log_signal.emit("🎵 Loading audio file & analyzing transient onsets...")
            self.signals.progress_signal.emit(10)
            
            y, sr = librosa.load(self.audio_path)
            audio_duration = librosa.get_duration(y=y, sr=sr)

            self.signals.log_signal.emit("⚡ Extracting musical onset strength peaks...")
            self.signals.progress_signal.emit(25)
            
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
            onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_env,
                sr=sr,
                backtrack=True,
                pre_max=3, post_max=3, pre_avg=3, post_avg=5,
                delta=0.07, wait=4
            )
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)
            self.signals.log_signal.emit(f"✓ Detected {len(onset_times)} raw audio hits.")

            filtered_times = []
            last_t = -1.0
            for t in onset_times:
                if t - last_t >= self.min_cut_dur:
                    filtered_times.append(t)
                    last_t = t

            self.signals.log_signal.emit(f"✂️ Filtered to {len(filtered_times)} beat-synced cut points.")
            self.signals.progress_signal.emit(40)

            cut_times = [0.0] + filtered_times + [audio_duration]
            video_duration = get_video_duration(self.video_path)

            temp_dir = "/tmp/mc_cuts_gui"
            os.system(f"rm -rf {temp_dir} && mkdir -p {temp_dir}")
            segment_files = []
            concat_list_path = os.path.join(temp_dir, "concat.txt")

            src_cursor = 0.0
            total_cuts = len(cut_times) - 1
            self.signals.log_signal.emit(f"🎬 Slicing video into {total_cuts} scene clips...")

            for i in range(total_cuts):
                dur = cut_times[i+1] - cut_times[i]
                if dur <= 0.05:
                    continue

                if src_cursor + dur > video_duration - 1.0:
                    src_cursor = (src_cursor % 10.0)

                seg_out = os.path.join(temp_dir, f"cut_{i:04d}.mp4")
                cmd = [
                    "ffmpeg", "-y", "-ss", f"{src_cursor:.3f}", "-i", self.video_path,
                    "-t", f"{dur:.3f}", "-an",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24", "-vf", f"scale={self.scale}",
                    seg_out
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                segment_files.append(seg_out)

                src_cursor += dur + 3.1
                
                # Update progress bar gradually
                prog = 40 + int((i / total_cuts) * 45)
                self.signals.progress_signal.emit(prog)

            with open(concat_list_path, "w") as f:
                for seg in segment_files:
                    f.write(f"file '{seg}'\n")

            self.signals.log_signal.emit("🚀 Merging video clips with audio track...")
            self.signals.progress_signal.emit(90)

            final_cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_list_path,
                "-i", self.audio_path,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                self.output_path
            ]
            res = subprocess.run(final_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if res.returncode == 0:
                self.signals.progress_signal.emit(100)
                self.signals.log_signal.emit(f"🎉 SUCCESS! Synced video saved to:\n{self.output_path}")
                self.signals.finished_signal.emit(True, self.output_path)
            else:
                self.signals.finished_signal.emit(False, res.stderr)

        except Exception as e:
            self.signals.finished_signal.emit(False, str(e))

class BeatSyncGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beat-Sync Cutter 🎬🎵 (AI Slop Edition)")
        self.resize(700, 580)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15)

        # Title / Header
        title_label = QLabel("Beat-Sync Cutter")
        title_label.setFont(QFont("Sans-Serif", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Automated audio-onset video cutter & beat synchronizer")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888; font-size: 12px;")

        layout.addWidget(title_label)
        layout.addWidget(subtitle)

        # File Selection Group
        file_group = QGroupBox("1. File Selection")
        file_layout = QVBoxLayout(file_group)

        # Video Input
        v_layout = QHBoxLayout()
        self.video_edit = QLineEdit()
        self.video_edit.setPlaceholderText("Select input video file (.mp4, .webm, .mkv)...")
        btn_video = QPushButton("Browse Video")
        btn_video.clicked.connect(self.browse_video)
        v_layout.addWidget(self.video_edit)
        v_layout.addWidget(btn_video)

        # Audio Input
        a_layout = QHBoxLayout()
        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("Select input audio file (.mp3, .wav, .flac)...")
        btn_audio = QPushButton("Browse Audio")
        btn_audio.clicked.connect(self.browse_audio)
        a_layout.addWidget(self.audio_edit)
        a_layout.addWidget(btn_audio)

        # Output Input
        o_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select destination output file (.mp4)...")
        btn_output = QPushButton("Browse Save Path")
        btn_output.clicked.connect(self.browse_output)
        o_layout.addWidget(self.output_edit)
        o_layout.addWidget(btn_output)

        file_layout.addLayout(v_layout)
        file_layout.addLayout(a_layout)
        file_layout.addLayout(o_layout)
        layout.addWidget(file_group)

        # Settings Group
        settings_group = QGroupBox("2. Cut & Render Settings")
        settings_layout = QHBoxLayout(settings_group)

        # Min cut duration
        settings_layout.addWidget(QLabel("Min Cut Dur (sec):"))
        self.spin_min_dur = QDoubleSpinBox()
        self.spin_min_dur.setRange(0.1, 2.0)
        self.spin_min_dur.setSingleStep(0.05)
        self.spin_min_dur.setValue(0.35)
        settings_layout.addWidget(self.spin_min_dur)

        # Scale / Resolution
        settings_layout.addWidget(QLabel("Resolution:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1280:-2 (720p - Fast)", "1920:-2 (1080p - Full HD)", "3840:-2 (4K - High Quality)", "Original"])
        settings_layout.addWidget(self.combo_res)

        layout.addWidget(settings_group)

        # Action Button & Progress
        self.btn_render = QPushButton("🚀 Start Beat-Sync Render")
        self.btn_render.setFont(QFont("Sans-Serif", 12, QFont.Weight.Bold))
        self.btn_render.setStyleSheet("background-color: #007ACC; color: white; padding: 10px; border-radius: 5px;")
        self.btn_render.clicked.connect(self.start_render)
        layout.addWidget(self.btn_render)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Logs Window
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Render logs will appear here...")
        layout.addWidget(self.log_text)

        self.setCentralWidget(main_widget)

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.webm *.mkv *.avi *.mov)")
        if file_path:
            self.video_edit.setText(file_path)
            if not self.output_edit.text():
                dir_name = os.path.dirname(file_path)
                self.output_edit.setText(os.path.join(dir_name, "synced_output.mp4"))

    def browse_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.mp3 *.wav *.flac *.m4a)")
        if file_path:
            self.audio_edit.setText(file_path)

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Save Location", "synced_output.mp4", "MP4 Video (*.mp4)")
        if file_path:
            self.output_edit.setText(file_path)

    def append_log(self, text):
        self.log_text.append(text)

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def render_finished(self, success, message):
        self.btn_render.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", f"Video rendered successfully!\nSaved to: {message}")
        else:
            QMessageBox.critical(self, "Error", f"Rendering failed:\n{message}")

    def start_render(self):
        video = self.video_edit.text().strip()
        audio = self.audio_edit.text().strip()
        output = self.output_edit.text().strip()

        if not video or not os.path.exists(video):
            QMessageBox.warning(self, "Missing Input", "Please select a valid video file!")
            return
        if not audio or not os.path.exists(audio):
            QMessageBox.warning(self, "Missing Input", "Please select a valid audio file!")
            return
        if not output:
            QMessageBox.warning(self, "Missing Input", "Please select an output save path!")
            return

        res_map = {
            "1280:-2 (720p - Fast)": "1280:-2",
            "1920:-2 (1080p - Full HD)": "1920:-2",
            "3840:-2 (4K - High Quality)": "3840:-2",
            "Original": "-1:-1"
        }
        scale = res_map.get(self.combo_res.currentText(), "1280:-2")
        min_dur = self.spin_min_dur.value()

        self.btn_render.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        signals = WorkerSignals()
        signals.log_signal.connect(self.append_log)
        signals.progress_signal.connect(self.update_progress)
        signals.finished_signal.connect(self.render_finished)

        worker = SyncWorker(video, audio, output, min_dur, scale, signals)
        worker.start()

def main():
    app = QApplication(sys.argv)
    window = BeatSyncGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
