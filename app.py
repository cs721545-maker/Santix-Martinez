
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
import shutil
import re


class SantixMartinez:
    def __init__(self, root):
        self.root = root
        self.root.title("Santix Martinez")
        self.root.geometry("680x650")
        self.root.minsize(540, 480)
        self.root.configure(bg="#10131c")

        self.config_path = None

        tk.Label(
            root, text="𝐒antix 𝐌artinez",
            font=("Segoe UI", 25, "bold"),
            fg="#62d9ff", bg="#10131c"
        ).pack(pady=(20, 5))

        tk.Label(
            root, text="AUDIO CONTROL PANEL",
            font=("Segoe UI", 10),
            fg="#aab4c8", bg="#10131c"
        ).pack()

        self.path_label = tk.Label(
            root, text="Nenhum arquivo selecionado",
            fg="white", bg="#202737",
            wraplength=600, padx=12, pady=12
        )
        self.path_label.pack(fill="x", padx=22, pady=18)

        tk.Button(
            root, text="SELECIONAR CONFIG.TXT",
            command=self.select_file,
            bg="#168ac4", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=15, pady=10
        ).pack()

        self.status = tk.Label(
            root, text="Aguardando arquivo",
            fg="#f5c96a", bg="#10131c"
        )
        self.status.pack(pady=12)

        self.global_button = tk.Button(
            root, text="ON / OFF GERAL",
            command=self.toggle_all,
            bg="#303b50", fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=20, pady=12,
            state="disabled"
        )
        self.global_button.pack(pady=8)

        tk.Label(
            root, text="CONTROLES INDIVIDUAIS DOS VST",
            fg="#62d9ff", bg="#10131c",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(20, 10))

        self.plugins_frame = tk.Frame(root, bg="#10131c")
        self.plugins_frame.pack(fill="both", expand=True, padx=30)

        tk.Label(
            root,
            text="Backup automático antes de cada alteração",
            fg="#8994a9", bg="#10131c",
            font=("Segoe UI", 9)
        ).pack(pady=12)

    def read_lines(self):
        return self.config_path.read_text(
            encoding="utf-8-sig"
        ).splitlines(keepends=True)

    def is_vst_line(self, line):
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

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo do Equalizer APO",
            filetypes=[
                ("Configurações", "*.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not filename:
            return

        self.config_path = Path(filename)
        self.path_label.config(text=str(self.config_path))
        self.global_button.config(state="normal")
        self.refresh_plugins()

    def make_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = self.config_path.with_name(
            self.config_path.name + ".santix_" + timestamp + ".bak"
        )
        shutil.copy2(self.config_path, backup)

    def save_lines(self, lines):
        self.make_backup()
        self.config_path.write_text(
            "".join(lines),
            encoding="utf-8"
        )

    def refresh_plugins(self):
        for widget in self.plugins_frame.winfo_children():
            widget.destroy()

        try:
            lines = self.read_lines()
        except Exception as error:
            messagebox.showerror("Erro", str(error))
            return

        plugins = [
            (index, line)
            for index, line in enumerate(lines)
            if self.is_vst_line(line)
        ]

        if not plugins:
            tk.Label(
                self.plugins_frame,
                text="Nenhum plugin VST encontrado.",
                fg="white", bg="#10131c"
            ).pack()
            self.status.config(text="Nenhum VST encontrado")
            return

        counts = {}

        for index, line in plugins:
            name = self.plugin_name(line)
            counts[name] = counts.get(name, 0) + 1

            label = name

            if name.lower() == "basiq.dll":
                occurrence = counts[name]
                if occurrence == 1:
                    label = "basiQ - Nice Vocal"
                elif occurrence == 2:
                    label = "basiQ - Crystal Guitar Face"
                else:
                    label = f"basiQ - Instância {occurrence}"

            variable = tk.BooleanVar(
                value=self.is_enabled(line)
            )

            row = tk.Frame(
                self.plugins_frame,
                bg="#202737", padx=12, pady=9
            )
            row.pack(fill="x", pady=5)

            tk.Label(
                row, text=label,
                fg="white", bg="#202737",
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

            tk.Checkbutton(
                row, text="Ativo",
                variable=variable,
                command=lambda i=index, v=variable:
                    self.toggle_plugin(i, v),
                fg="#62d9ff", bg="#202737",
                selectcolor="#10131c",
                activebackground="#202737",
                activeforeground="white"
            ).pack(side="right")

        active = sum(
            1 for _, line in plugins
            if self.is_enabled(line)
        )

        self.status.config(
            text=f"{active} de {len(plugins)} plugins ativos"
        )

    def change_plugin(self, index, enabled):
        lines = self.read_lines()

        if index >= len(lines) or not self.is_vst_line(lines[index]):
            raise ValueError(
                "O arquivo mudou. Selecione-o novamente."
            )

        line = lines[index]

        if enabled:
            line = re.sub(
                r"^(\s*)#\s*",
                r"\1",
                line,
                count=1
            )
        else:
            if self.is_enabled(line):
                line = re.sub(
                    r"^(\s*)",
                    r"\1# ",
                    line,
                    count=1
                )

        lines[index] = line
        return lines

    def toggle_plugin(self, index, variable):
        try:
            lines = self.change_plugin(
                index, variable.get()
            )
            self.save_lines(lines)
            self.refresh_plugins()
        except Exception as error:
            messagebox.showerror("Erro", str(error))
            self.refresh_plugins()

    def toggle_all(self):
        if not self.config_path:
            return

        try:
            lines = self.read_lines()

            vst_indices = [
                i for i, line in enumerate(lines)
                if self.is_vst_line(line)
            ]

            if not vst_indices:
                messagebox.showinfo(
                    "Santix", "Nenhum VST encontrado."
                )
                return

            any_disabled = any(
                not self.is_enabled(lines[i])
                for i in vst_indices
            )

            enable_all = any_disabled

            for i in vst_indices:
                line = lines[i]

                if enable_all:
                    line = re.sub(
                        r"^(\s*)#\s*",
                        r"\1",
                        line,
                        count=1
                    )
                else:
                    if self.is_enabled(line):
                        line = re.sub(
                            r"^(\s*)",
                            r"\1# ",
                            line,
                            count=1
                        )

                lines[i] = line

            self.save_lines(lines)
            self.refresh_plugins()

            messagebox.showinfo(
                "Santix Martinez",
                "Todos os VSTs foram " +
                ("ativados." if enable_all else "desativados.")
            )

        except Exception as error:
            messagebox.showerror("Erro", str(error))
            self.refresh_plugins()


if __name__ == "__main__":
    root = tk.Tk()
    app = SantixMartinez(root)
    root.mainloop()
            
