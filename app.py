import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
import shutil
import re
import threading

import numpy as np
import sounddevice as sd


class SantixMartinez:
    def __init__(self, root):
        self.root = root
        self.root.title("Santix Martinez")
        self.root.geometry("760x820")
        self.root.configure(bg="#10131c")

        self.config_path = None
        self.stream = None
        self.running = False
        self.peak = 0.0
        self.rms = 0.0
        self.gain = 1.0
        self.lock = threading.Lock()
        self.devices = {}

        self.build_interface()
        self.refresh_devices()
        self.update_meter()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_interface(self):
        tk.Label(
            self.root, text="𝐒antix 𝐌artinez",
            font=("Segoe UI", 27, "bold"),
            fg="#62d9ff", bg="#10131c"
        ).pack(pady=(15, 3))

        tk.Label(
            self.root, text="PRO AUDIO CONTROL SYSTEM",
            fg="#aab4c8", bg="#10131c"
        ).pack()

        self.status = tk.Label(
            self.root, text="Sistema parado",
            fg="#f5c96a", bg="#10131c"
        )
        self.status.pack(pady=12)

        self.section("ENTRADA E SAÍDA DE ÁUDIO")

        self.input_box = self.device_box("Microfone de entrada")
        self.output_box = self.device_box("Saída virtual")

        tk.Button(
            self.root, text="ATUALIZAR DISPOSITIVOS",
            command=self.refresh_devices,
            bg="#303b50", fg="white",
            relief="flat", padx=12, pady=7
        ).pack(pady=8)

        self.rate_box = self.device_box("Frequência de áudio", False)
        self.rate_box["values"] = ["48000", "44100"]
        self.rate_box.set("48000")

        self.section("PROCESSAMENTO DE ÁUDIO")

        tk.Label(
            self.root, text="Ganho de entrada",
            fg="white", bg="#10131c"
        ).pack()

        self.gain_label = tk.Label(
            self.root, text="100%",
            fg="#62d9ff", bg="#10131c"
        )
        self.gain_label.pack()

        self.gain_slider = tk.Scale(
            self.root, from_=0, to=200,
            orient="horizontal", length=350,
            command=self.set_gain,
            bg="#10131c", fg="white",
            highlightthickness=0,
            troughcolor="#303b50"
        )
        self.gain_slider.set(100)
        self.gain_slider.pack()

        self.section("MEDIDOR DE MICROFONE")

        self.level_label = tk.Label(
            self.root, text="Nível: 0%",
            fg="#62d9ff", bg="#10131c",
            font=("Segoe UI", 13, "bold")
        )
        self.level_label.pack(pady=5)

        self.meter = ttk.Progressbar(
            self.root, length=430,
            maximum=100, mode="determinate"
        )
        self.meter.pack(pady=5)

        buttons = tk.Frame(self.root, bg="#10131c")
        buttons.pack(pady=15)

        self.start_button = tk.Button(
            buttons, text="INICIAR ÁUDIO",
            command=self.start_audio,
            bg="#087d58", fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=18, pady=12, relief="flat"
        )
        self.start_button.pack(side="left", padx=6)

        self.stop_button = tk.Button(
            buttons, text="PARAR ÁUDIO",
            command=self.stop_audio,
            bg="#a83242", fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=18, pady=12, relief="flat",
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=6)

        self.section("EQUALIZER APO E PLUGINS VST")

        tk.Button(
            self.root, text="SELECIONAR CONFIG.TXT",
            command=self.select_config,
            bg="#168ac4", fg="white",
            relief="flat", padx=12, pady=8
        ).pack(pady=5)

        self.config_label = tk.Label(
            self.root, text="Nenhum arquivo selecionado",
            fg="#aab4c8", bg="#10131c",
            wraplength=650
        )
        self.config_label.pack(pady=5)

        self.global_button = tk.Button(
            self.root, text="ATIVAR / DESATIVAR TODOS OS VST",
            command=self.toggle_all,
            bg="#303b50", fg="white",
            relief="flat", padx=12, pady=8,
            state="disabled"
        )
        self.global_button.pack(pady=7)

        self.plugins_frame = tk.Frame(
            self.root, bg="#10131c"
        )
        self.plugins_frame.pack(fill="x", padx=25)

        tk.Label(
            self.root,
            text="Santix Martinez | Windows 64 bits",
            fg="#8994a9", bg="#10131c"
        ).pack(pady=12)

    def section(self, title):
        tk.Label(
            self.root, text=title,
            fg="#62d9ff", bg="#10131c",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=(15, 8))

    def device_box(self, label, device=True):
        tk.Label(
            self.root, text=label,
            fg="white", bg="#10131c"
        ).pack(pady=(5, 2))

        box = ttk.Combobox(
            self.root, state="readonly", width=65
        )
        box.pack(pady=3)

        return box

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

            self.input_box["values"] = inputs
            self.output_box["values"] = outputs

            m7 = next(
                (x for x in inputs if "M7" in x.upper()),
                inputs[0] if inputs else ""
            )

            cable = next(
                (x for x in outputs
                 if "CABLE INPUT" in x.upper()),
                outputs[0] if outputs else ""
            )

            self.input_box.set(m7)
            self.output_box.set(cable)

            self.status.config(
                text="Dispositivos de áudio identificados",
                fg="#62d9ff"
            )

        except Exception as error:
            messagebox.showerror("Áudio", str(error))

    def set_gain(self, value):
        self.gain = float(value) / 100
        self.gain_label.config(text=f"{int(float(value))}%")

    def audio_callback(self, indata, outdata, frames, time, status):
        audio = indata[:, 0].copy()

        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio * audio)))

        with self.lock:
            self.peak = peak
            self.rms = rms

        outdata[:, 0] = np.clip(
            audio * self.gain, -1.0, 1.0
        )

    def start_audio(self):
        if self.running:
            return

        try:
            input_label = self.input_box.get()
            output_label = self.output_box.get()

            if input_label not in self.devices:
                raise ValueError("Selecione o microfone M7.")

            if output_label not in self.devices:
                raise ValueError("Selecione a saída virtual.")

            input_id = self.devices[input_label]
            output_id = self.devices[output_label]
            rate = int(self.rate_box.get())

            self.stream = sd.Stream(
                device=(input_id, output_id),
                samplerate=rate,
                channels=(1, 1),
                dtype="float32",
                callback=self.audio_callback,
                blocksize=0
            )

            self.stream.start()
            self.running = True

            self.status.config(
                text="ÁUDIO EM TEMPO REAL ATIVO",
                fg="#42df91"
            )
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

        except Exception as error:
            self.stream = None
            messagebox.showerror(
                "Não foi possível iniciar",
                f"{error}\n\nSe necessário, tente 44100 Hz."
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

        self.status.config(
            text="Sistema parado", fg="#f5c96a"
        )
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.meter["value"] = 0
        self.level_label.config(text="Nível: 0%")

    def update_meter(self):
        if self.running:
            with self.lock:
                peak = self.peak

            percent = min(100, int(peak * 100))
            self.meter["value"] = percent
            self.level_label.config(
                text=f"Pico de entrada: {percent}%"
            )

        self.root.after(50, self.update_meter)

    def select_config(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Configuração", "*.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if filename:
            self.config_path = Path(filename)
            self.config_label.config(text=str(self.config_path))
            self.global_button.config(state="normal")
            self.refresh_plugins()

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

    def plugin_name(self, line):
        match = re.search(
            r"([A-Za-z0-9_-]+\.dll)",
            line, re.IGNORECASE
        )
        return match.group(1) if match else "Plugin VST"

    def backup(self):
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
        destination = self.config_path.with_name(
            self.config_path.name + ".santix_" +
            timestamp + ".bak"
        )
        shutil.copy2(self.config_path, destination)

    def refresh_plugins(self):
        for widget in self.plugins_frame.winfo_children():
            widget.destroy()

        lines = self.config_path.read_text(
            encoding="utf-8-sig"
        ).splitlines(keepends=True)

        self.plugin_indices = [
            i for i, line in enumerate(lines)
            if self.is_vst(line)
        ]

        counts = {}

        for index in self.plugin_indices:
            line = lines[index]
            name = self.plugin_name(line)
            counts[name] = counts.get(name, 0) + 1

            label = name

            if name.lower() == "basiq.dll":
                label = (
                    "basiQ - Nice Vocal"
                    if counts[name] == 1
                    else "basiQ - Crystal Guitar Face"
                    if counts[name] == 2
                    else f"basiQ - Instância {counts[name]}"
                )

            variable = tk.BooleanVar(
                value=self.is_enabled(line)
            )

            row = tk.Frame(
                self.plugins_frame,
                bg="#202737", padx=10, pady=7
            )
            row.pack(fill="x", pady=3)

            tk.Label(
                row, text=label,
                fg="white", bg="#202737"
            ).pack(side="left")

            tk.Checkbutton(
                row, text="Ativo",
                variable=variable,
                command=lambda i=index, v=variable:
                    self.toggle_plugin(i, v),
                fg="#62d9ff", bg="#202737",
                selectcolor="#10131c",
                activebackground="#202737"
            ).pack(side="right")

    def change_plugin(self, index, enabled):
        lines = self.config_path.read_text(
            encoding="utf-8-sig"
        ).splitlines(keepends=True)

        if index >= len(lines) or not self.is_vst(lines[index]):
            raise ValueError(
                "O arquivo mudou. Selecione-o novamente."
            )

        line = lines[index]

        if enabled:
            line = re.sub(
                r"^(\s*)#\s*", r"\1", line, count=1
            )
        elif self.is_enabled(line):
            line = re.sub(
                r"^(\s*)", r"\1# ", line, count=1
            )

        lines[index] = line

        self.backup()
        self.config_path.write_text(
            "".join(lines), encoding="utf-8"
        )

    def toggle_plugin(self, index, variable):
        try:
            self.change_plugin(index, variable.get())
            self.refresh_plugins()
        except Exception as error:
            messagebox.showerror("VST", str(error))
            self.refresh_plugins()

    def toggle_all(self):
        try:
            lines = self.config_path.read_text(
                encoding="utf-8-sig"
            ).splitlines(keepends=True)

            indices = [
                i for i, line in enumerate(lines)
                if self.is_vst(line)
            ]

            if not indices:
                messagebox.showinfo(
                    "VST", "Nenhum plugin encontrado."
                )
                return

            enable = any(
                not self.is_enabled(lines[i])
                for i in indices
            )

            for i in indices:
                line = lines[i]

                if enable:
                    line = re.sub(
                        r"^(\s*)#\s*", r"\1",
                        line, count=1
                    )
                elif self.is_enabled(line):
                    line = re.sub(
                        r"^(\s*)", r"\1# ",
                        line, count=1
                    )

                lines[i] = line

            self.backup()
            self.config_path.write_text(
                "".join(lines), encoding="utf-8"
            )
            self.refresh_plugins()

        except Exception as error:
            messagebox.showerror("VST", str(error))

    def close(self):
        self.stop_audio()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SantixMartinez(root)
    root.mainloop()
    
