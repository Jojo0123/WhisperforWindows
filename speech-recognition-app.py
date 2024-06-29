import sys
import pyaudio
import numpy as np
import wave
import whisper
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTextEdit, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPointF
from PyQt6.QtGui import QPainterPath
from PyQt6.QtGui import QClipboard

class AudioThread(QThread):
    update_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.is_recording = False
        self.frames = []

    def run(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format, channels=self.channels, rate=self.rate,
                        input=True, frames_per_buffer=self.chunk_size)

        while True:
            data = np.frombuffer(stream.read(self.chunk_size), dtype=np.int16)
            self.update_signal.emit(data)
            if self.is_recording:
                self.frames.append(data.tobytes())

    def start_recording(self):
        self.is_recording = True
        self.frames = []

    def stop_recording(self):
        self.is_recording = False
        audio_data = b''.join(self.frames)
        with wave.open("debug_audio.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.rate)
            wf.writeframes(audio_data)
        return audio_data

class WhisperThread(QThread):
    text_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.model = whisper.load_model("base")
        self.audio_data = None

    def set_audio_data(self, audio_data):
        self.audio_data = audio_data

    def run(self):
        if self.audio_data:
            try:
                with wave.open("temp_audio.wav", "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(self.audio_data)

                options = whisper.DecodingOptions(language="de", without_timestamps=True)
                result = self.model.transcribe("temp_audio.wav", **options.__dict__)
                
                if result["text"]:
                    self.text_signal.emit(result["text"])
                else:
                    self.error_signal.emit("Keine Sprache erkannt.")
            except Exception as e:
                self.error_signal.emit(f"Fehler bei der Verarbeitung: {str(e)}")

class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 300)
        self.num_bands = 5
        self.data = np.zeros((self.num_bands, 360))
        self.smooth_data = np.zeros((self.num_bands, 360))
        self.scale_factor = np.ones(self.num_bands)
        self.is_recording = False
        self.is_processing = False
        self.transition_factor = 1.0
        self.pulse_factor = 1.0
        self.pulse_direction = 0.02
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_visualization)
        self.timer.start(50)  # Update every 50ms

    def update_data(self, new_data):
        if self.is_recording:
            # Split the data into frequency bands (this is a simple approximation)
            for i in range(self.num_bands):
                start = int(len(new_data) * i / self.num_bands)
                end = int(len(new_data) * (i + 1) / self.num_bands)
                band_data = new_data[start:end]
                self.data[i] = np.interp(np.linspace(0, len(band_data), 360), np.arange(len(band_data)), band_data)
            self.scale_factor = np.maximum(1, np.max(np.abs(self.data), axis=1) * 2)

    def update_visualization(self):
        if self.is_recording:
            self.transition_factor = 1.0
            # Smooth the data
            self.smooth_data = self.smooth_data * 0.9 + self.data * 0.1
        elif self.is_processing:
            # Transition to pulsing circle
            self.transition_factor = max(0, self.transition_factor - 0.05)
            if self.transition_factor == 0:
                # Pulsing effect
                self.pulse_factor += self.pulse_direction
                if self.pulse_factor > 1.2 or self.pulse_factor < 0.8:
                    self.pulse_direction *= -1
        else:
            # Reset when not recording or processing
            self.transition_factor = 1.0
            self.pulse_factor = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2)
        
        base_radius = min(width, height) * 0.35
        radius = base_radius * self.pulse_factor

        # Draw background circle
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(center, radius, radius)

        if self.is_recording or self.is_processing:
            colors = [QColor(0, 120, 255, 150), QColor(0, 200, 100, 150), 
                      QColor(255, 120, 0, 150), QColor(200, 0, 200, 150), 
                      QColor(255, 200, 0, 150)]

            for i in range(self.num_bands):
                path = QPainterPath()
                for j, value in enumerate(self.smooth_data[i]):
                    angle = j * (360 / len(self.smooth_data[i]))
                    r = radius + value * radius * self.transition_factor / (self.scale_factor[i] * 4)
                    x = center.x() + r * np.cos(np.radians(angle))
                    y = center.y() + r * np.sin(np.radians(angle))
                    if j == 0:
                        path.moveTo(x, y)
                    else:
                        path.lineTo(x, y)
                path.closeSubpath()

                painter.setPen(QPen(colors[i], 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)

        # Draw pulsing circle when processing
        if self.is_processing and self.transition_factor == 0:
            painter.setPen(QPen(QColor(0, 120, 255, 150), 2))
            painter.drawEllipse(center, radius, radius)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper for Windows by extensos")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.waveform_widget = WaveformWidget()
        main_layout.addWidget(self.waveform_widget)

        self.status_label = QLabel("Bereit zur Aufnahme")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        main_layout.addWidget(self.text_output)

        button_layout = QHBoxLayout()
        self.record_button = QPushButton("Aufnahme starten")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)

        self.copy_button = QPushButton("Text kopieren")
        self.copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(self.copy_button)

        main_layout.addLayout(button_layout)

        self.audio_thread = AudioThread()
        self.audio_thread.update_signal.connect(self.waveform_widget.update_data)
        self.audio_thread.start()

        self.whisper_thread = WhisperThread()
        self.whisper_thread.text_signal.connect(self.update_text_output)
        self.whisper_thread.error_signal.connect(self.show_error)

        self.is_recording = False

    def toggle_recording(self):
        if not self.is_recording:
            self.record_button.setText("Aufnahme beenden")
            self.is_recording = True
            self.waveform_widget.is_recording = True
            self.waveform_widget.is_processing = False
            self.audio_thread.start_recording()
            self.status_label.setText("Aufnahme läuft... Sprechen Sie jetzt.")
        else:
            self.record_button.setText("Aufnahme starten")
            self.is_recording = False
            self.waveform_widget.is_recording = False
            self.waveform_widget.is_processing = True
            audio_data = self.audio_thread.stop_recording()
            self.status_label.setText("Aufnahme beendet. Verarbeite Audio...")
            self.whisper_thread.set_audio_data(audio_data)
            self.whisper_thread.start()

    def update_text_output(self, text):
        self.text_output.setText(text)
        self.status_label.setText("Transkription abgeschlossen.")
        self.waveform_widget.is_processing = False

    def show_error(self, error_message):
        self.status_label.setText(f"Fehler: {error_message}")
        self.waveform_widget.is_processing = False

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_output.toPlainText())
        self.status_label.setText("Text in die Zwischenablage kopiert.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
