import sys
import re
import shutil
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QProgressBar, QFileDialog, QMessageBox,
    QStackedWidget, QFrame, QCheckBox
)


class SantixMartinez(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Santix Martinez")
        self.resize(1100, 760)

        self.config_path = None
        self.stream = None
        self.running = False
        self.devices = {}
        self.gain = 1.0
        self.peak = 0.0
        self.lock = threading.Lock()

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #101015;
                color: #eeeeee;
                font-family: Segoe UI;
            }
            QFrame#sidebar {
                background-color: #08080c;
                border-right: 1px solid #302027;
            }
            QPushButton {
                background-color: #211519;
                color: #eeeeee;
                border: 1px solid #47252d;
                border-radius: 6px;
                padding: 11px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #49232b;
            }
            QPushButton#primary {
                background-color: #a83242;
                font-weight: bold;
            }
            QPushButton#primary:hover {
                background-color: #c74355;
            }
            QComboBox {
                background-color: #211519;
                border: 1px solid #63303a;
                padding: 9px;
                border-radius: 5px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #39242a;
            }
            QSlider::handle:horizontal {
                background: #e45b69;
                width: 15px;
                margin: -5px 0;
                border-radius: 5px;
            }
            QProgressBar {
                background: #292329;
                border: none;
                height: 13px;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #db5361;
                border-radius: 5px;
            }
        """)

        self.build_ui()
        self.refresh_devices()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_meter)
        self.timer.start(50)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 20, 12, 15)

        logo = QLabel("𝐒ANTIX\nMARTINEZ")
        logo.setStyleSheet(
            "color:#e45b69;font-size:23px;font-weight:bold;"
        )
        side.addWidget(logo)

        side.addSpacing(25)

        self.pages = QStackedWidget()

        page_names = [
            "Home", "Loading", "Audio", "VST Host",
            "Effects", "Custom RPC", "Sounds", "Themes"
        ]

        for index, name in enumerate(page_names):
            button = QPushButton(name)
            button.clicked.connect(
                lambda checked=False, i=index:
                self.pages.setCurrentIndex(i)
            )
            side.addWidget(button)

        side.addStretch()

        version = QLabel("WINDOWS 11 • 64 BIT")
        version.setStyleSheet("color:#777777;font-size:10px;")
        side.addWidget(version)

        main.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 25, 28, 25)

        self.pages = QStackedWidget()

        self.pages.addWidget(self.home_page())
        self.pages.addWidget(self.loading_page())
        self.pages.addWidget(self.audio_page())
        self.pages.addWidget(self.vst_page())
        self.pages.addWidget(self.effects_page())
        self.pages.addWidget(self.rpc_page())
        self.pages.addWidget(self.sounds_page())
        self.pages.addWidget(self.themes_page())

        content_layout.addWidget(self.pages)
        main.addWidget(content)

    def heading(self, title, subtitle=""):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 15)

        label = QLabel(title)
        label.setStyleSheet(
            "font-size:25px;font-weight:bold;color:#e45b69;"
        )
        layout.addWidget(label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet("color:#999999;font-size:12px;")
            layout.addWidget(sub)

        return box

    def panel(self, title):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #19151a;
                border: 1px solid #38232a;
                border-radius: 9px;
            }
        """)
        layout = QVBoxLayout(frame)
        label = QLabel(title)
        label.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#e45b69;"
            "border:none;"
        )
        layout.addWidget(label)
        return frame, layout

    def home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self.heading(
            "Santix Martinez",
            "Professional Audio Control System"
        ))

        frame, box = self.panel("STATUS DO SISTEMA")
        self.home_status = QLabel("Motor de áudio parado")
        box.addWidget(self.home_status)

        self.home_input = QLabel("Entrada: não selecionada")
        box.addWidget(self.home_input)

        self.home_output = QLabel("Saída: não selecionada")
        box.addWidget(self.home_output)

        layout.addWidget(frame)
        layout.addStretch()
        return page

    def loading_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.heading(
            "Loading",
            "Inicialização e estado do motor de áudio"
        ))

        frame, box = self.panel("MOTOR DE ÁUDIO")
        self.loading_status = QLabel("Aguardando inicialização")
        box.addWidget(self.loading_status)
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def audio_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self.heading(
            "Audio",
            "Microfone, dispositivos e transmissão em tempo real"
        ))

        frame, box = self.panel("DISPOSITIVOS")

        box.addWidget(QLabel("Microfone de entrada"))
        self.input_box = QComboBox()
        box.addWidget(self.input_box)

        box.addWidget(QLabel("Saída virtual"))
        self.output_box = QComboBox()
        box.addWidget(self.output_box)

        refresh = QPushButton("Atualizar dispositivos")
        refresh.clicked.connect(self.refresh_devices)
        box.addWidget(refresh)

        layout.addWidget(frame)

        meter_frame, meter_box = self.panel("MONITORAMENTO")
        self.level_label = QLabel("Pico de entrada: 0%")
        meter_box.addWidget(self.level_label)

        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setValue(0)
        meter_box.addWidget(self.meter)

        layout.addWidget(meter_frame)

        gain_frame, gain_box = self.panel("GANHO")
        self.gain_label = QLabel("Ganho: 100%")
        gain_box.addWidget(self.gain_label)

        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 200)
        self.gain_slider.setValue(100)
        self.gain_slider.valueChanged.connect(self.set_gain)
        gain_box.addWidget(self.gain_slider)

        layout.addWidget(gain_frame)

        buttons = QHBoxLayout()

        start = QPushButton("INICIAR ÁUDIO")
        start.setObjectName("primary")
        start.clicked.connect(self.start_audio)

        stop = QPushButton("PARAR ÁUDIO")
        stop.clicked.connect(self.stop_audio)

        buttons.addWidget(start)
        buttons.addWidget(stop)

        layout.addLayout(buttons)
        layout.addStretch()
        return page

    def vst_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(self.heading(
            "VST Host",
            "Controles das linhas VST no Equalizer APO"
        ))

        select = QPushButton("Selecionar config.txt")
        select.clicked.connect(self.select_config)
        layout.addWidget(select)

        self.config_label = QLabel("Nenhum arquivo selecionado")
        self.config_label.setWordWrap(True)
        layout.addWidget(self.config_label)

        self.vst_controls = QVBoxLayout()
        layout.addLayout(self.vst_controls)

        layout.addStretch()
        return page

    def effects_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.heading(
            "Effects",
            "Área de processamento de voz"
        ))

        frame, box = self.panel("PROCESSAMENTO")
        box.addWidget(QLabel(
            "O motor atual possui controle de ganho."
        ))
        box.addWidget(QLabel(
            "Equalizador, compressor, limiter e redução "
            "de ruído serão adicionados nas próximas etapas."
        ))
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def rpc_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.heading(
            "Custom RPC",
            "Integração de status com aplicativos"
        ))

        frame, box = self.panel("INTEGRAÇÕES")
        box.addWidget(QLabel(
            "Integração Discord Rich Presence ainda não configurada."
        ))
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def sounds_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.heading(
            "Sounds",
            "Central de efeitos sonoros"
        ))

        frame, box = self.panel("SOUNDBOARD")
        box.addWidget(QLabel(
            "A soundboard será implementada na próxima etapa."
        ))
        layout.addWidget(frame)
        layout.addStretch()
        return page

    def themes_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self.heading(
            "Themes",
            "Personalização visual"
        ))

        frame, box = self.panel("TEMA")
        box.addWidget(QLabel("Tema atual: Dark Red"))

        button = QPushButton("Dark Red")
        button.clicked.connect(
            lambda: self.set_theme("#101015", "#e45b69")
        )
        box.addWidget(button)

        layout.addWidget(frame)
        layout.addStretch()
        return page

    def set_theme(self, background, accent):
        self.setStyleSheet(self.styleSheet().replace(
            "#e45b69", accent
        ))

    def refresh_devices(self):
        try:
            self.devices = {}
            inputs = []
            outputs = []

            for index, device in enumerate(sd.query_devices()):
                name = device["name"]
                label = f"{index} | {name}"
                self.devices[label] = index

                if device["max_input_channels"] > 0:
                    inputs.append(label)

                if device["max_output_channels"] > 0:
                    outputs.append(label)

            self.input_box.clear()
            self.output_box.clear()
            self.input_box.addItems(inputs)
            self.output_box.addItems(outputs)

            for i, name in enumerate(inputs):
                if "M7" in name.upper():
                    self.input_box.setCurrentIndex(i)
                    break

            for i, name in enumerate(outputs):
                if "CABLE INPUT" in name.upper():
                    self.output_box.setCurrentIndex(i)
                    break

        except Exception as error:
            QMessageBox.critical(self, "Áudio", str(error))

    def set_gain(self, value):
        self.gain = value / 100.0
        self.gain_label.setText(f"Ganho: {value}%")

    def audio_callback(self, indata, outdata, frames, time, status):
        audio = indata[:, 0].copy()

        peak = float(np.max(np.abs(audio)))

        with self.lock:
            self.peak = peak

        outdata[:, 0] = np.clip(
            audio * self.gain, -1.0, 1.0
        )

    def start_audio(self):
        if self.running:
            return

        try:
            input_label = self.input_box.currentText()
            output_label = self.output_box.currentText()

            if input_label not in self.devices:
                raise ValueError("Selecione o microfone.")

            if output_label not in self.devices:
                raise ValueError("Selecione a saída virtual.")

            input_id = self.devices[input_label]
            output_id = self.devices[output_label]

            self.stream = sd.Stream(
                device=(input_id, output_id),
                samplerate=48000,
                channels=(1, 1),
                dtype="float32",
                callback=self.audio_callback
            )

            self.stream.start()
            self.running = True

            self.home_status.setText("Áudio em tempo real ativo")
            self.loading_status.setText("Motor iniciado")

        except Exception as error:
            self.stream = None
            QMessageBox.critical(
                self, "Erro ao iniciar áudio", str(error)
            )

    def stop_audio(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

        self.stream = None
        self.running = False
        self.home_status.setText("Motor de áudio parado")
        self.loading_status.setText("Aguardando inicialização")

    def update_meter(self):
        if not hasattr(self, "meter"):
            return

        if self.running:
            with self.lock:
                peak = self.peak

            value = min(100, int(peak * 100))
            self.meter.setValue(value)
            self.level_label.setText(
                f"Pico de entrada: {value}%"
            )

    def select_config(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Equalizer APO config.txt",
            "",
            "Arquivos TXT (*.txt);;Todos os arquivos (*)"
        )

        if filename:
            self.config_path = Path(filename)
            self.config_label.setText(filename)
            self.load_vsts()

    def is_vst(self, line):
        return bool(re.match(
            r"^\s*(#\s*)?VSTPlugin\s*:",
            line, re.IGNORECASE
        ))

    def is_enabled(self, line):
        return bool(re.match(
            r"^\s*VSTPlugin\s*:",
            line, re.IGNORECASE
        ))

    def backup_config(self):
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        backup = self.config_path.with_name(
            self.config_path.name + "." +
            timestamp + ".bak"
        )

        shutil.copy2(self.config_path, backup)

    def load_vsts(self):
        while self.vst_controls.count():
            item = self.vst_controls.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        lines = self.config_path.read_text(
            encoding="utf-8-sig"
        ).splitlines(keepends=True)

        self.vst_indices = [
            i for i, line in enumerate(lines)
            if self.is_vst(line)
        ]

        for index in self.vst_indices:
            line = lines[index]

            match = re.search(
                r"([A-Za-z0-9_-]+\.dll)",
                line, re.IGNORECASE
            )

            name = match.group(1) if match else "Plugin VST"

            check = QCheckBox(name)
            check.setChecked(self.is_enabled(line))
            check.stateChanged.connect(
                lambda state, i=index:
                self.toggle_vst(i, state == Qt.Checked)
            )

            self.vst_controls.addWidget(check)

        if not self.vst_indices:
            self.vst_controls.addWidget(
                QLabel("Nenhuma linha VST encontrada.")
            )

    def toggle_vst(self, index, enabled):
        try:
            lines = self.config_path.read_text(
                encoding="utf-8-sig"
            ).splitlines(keepends=True)

            if index >= len(lines) or not self.is_vst(lines[index]):
                raise ValueError("O arquivo foi alterado externamente.")

            line = lines[index]

            if enabled:
                line = re.sub(
                    r"^(\s*)#\s*", r"\1",
                    line, count=1
                )
            else:
                if self.is_enabled(line):
                    line = re.sub(
                        r"^(\s*)", r"\1# ",
                        line, count=1
                    )

            lines[index] = line

            self.backup_config()
            self.config_path.write_text(
                "".join(lines), encoding="utf-8"
            )

        except Exception as error:
            QMessageBox.critical(self, "VST", str(error))
            self.load_vsts()

    def closeEvent(self, event):
        self.stop_audio()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SantixMartinez()
    window.show()

    timer = QTimer()
    timer.timeout.connect(window.update_meter)
    timer.start(50)

    sys.exit(app.exec())
        
