import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import shutil
from datetime import datetime

APP_NAME = "Santix Martinez"

class SantixApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME + " - Pro Audio Control")
        root.geometry("980x650")
        root.minsize(780, 540)
        self.config_path = None
        self.original_text = None
        self.enabled = True
        self.bg = "#101114"
        self.panel = "#191b20"
        self.red = "#e5484d"
        root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=9)
        style.configure("TLabel", background=self.bg, foreground="#eeeeee", font=("Segoe UI", 10))
        style.configure("TFrame", background=self.bg)

        header = tk.Frame(root, bg=self.bg)
        header.pack(fill="x", padx=24, pady=(20,12))
        tk.Label(header, text="𝐒antix 𝐌artinez", bg=self.bg, fg=self.red,
                 font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(header, text="PRO AUDIO CONTROL PANEL  •  WINDOWS",
                 bg=self.bg, fg="#969ba5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(3,0))

        body = tk.Frame(root, bg=self.bg)
        body.pack(fill="both", expand=True, padx=24, pady=8)
        nav = tk.Frame(body, bg=self.panel, width=190)
        nav.pack(side="left", fill="y", padx=(0,16))
        nav.pack_propagate(False)
        tk.Label(nav, text="MENU", bg=self.panel, fg="#8e929b",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(18,10))
        for name in ["Home", "Audio", "VST Hook", "Custom FX", "Settings"]:
            tk.Button(nav, text="  "+name, anchor="w", relief="flat", bd=0,
                      bg=self.panel, fg="#eeeeee", activebackground="#292c33",
                      activeforeground="white", font=("Segoe UI", 11),
                      command=lambda n=name: self.show_section(n)).pack(fill="x", padx=8, pady=2, ipady=8)

        self.content = tk.Frame(body, bg=self.bg)
        self.content.pack(side="left", fill="both", expand=True)
        self.show_section("Home")

        footer = tk.Frame(root, bg=self.bg)
        footer.pack(fill="x", padx=24, pady=(5,18))
        self.status = tk.Label(footer, text="Nenhum arquivo do Equalizer APO selecionado",
                               bg=self.bg, fg="#aeb3bd", font=("Segoe UI", 9))
        self.status.pack(side="left")

    def card(self, parent, title, value, subtitle=""):
        f=tk.Frame(parent,bg=self.panel, padx=16,pady=14)
        tk.Label(f,text=title,bg=self.panel,fg="#aeb3bd",font=("Segoe UI",9,"bold")).pack(anchor="w")
        tk.Label(f,text=value,bg=self.panel,fg="#ffffff",font=("Segoe UI",18,"bold")).pack(anchor="w",pady=(7,2))
        if subtitle: tk.Label(f,text=subtitle,bg=self.panel,fg="#8e929b",font=("Segoe UI",9)).pack(anchor="w")
        return f

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def show_section(self, section):
        self.clear()
        tk.Label(self.content,text=section,bg=self.bg,fg="white",
                 font=("Segoe UI",20,"bold")).pack(anchor="w",pady=(5,18))
        if section == "Home":
            row=tk.Frame(self.content,bg=self.bg); row.pack(fill="x")
            self.card(row,"ENGINE","Equalizer APO","Integração por arquivo de configuração").pack(side="left",fill="x",expand=True,padx=(0,8))
            self.card(row,"STATUS","READY" if self.config_path else "SETUP","Selecione seu config.txt").pack(side="left",fill="x",expand=True,padx=8)
            self.card(row,"VST","DETECT","Plugins identificados no arquivo").pack(side="left",fill="x",expand=True,padx=(8,0))
            tk.Label(self.content,text="Controle principal",bg=self.bg,fg="#c6c9d0",
                     font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(28,10))
            self.toggle_btn=tk.Button(self.content,text="EFEITOS: ON",command=self.toggle,
                bg=self.red,fg="white",activebackground="#bd3439",relief="flat",
                font=("Segoe UI",13,"bold"),padx=24,pady=13)
            self.toggle_btn.pack(anchor="w")
            ttk.Button(self.content,text="Selecionar config.txt do Equalizer APO",command=self.choose_config).pack(anchor="w",pady=(22,8))
            ttk.Button(self.content,text="Verificar plugins VST",command=self.show_vsts).pack(anchor="w")
            tk.Label(self.content,text="A primeira alteração cria uma cópia de segurança ao lado do config.txt.",
                     bg=self.bg,fg="#969ba5",font=("Segoe UI",9)).pack(anchor="w",pady=20)
        elif section in ("Audio","VST Hook","Custom FX"):
            tk.Label(self.content,text="Este módulo será habilitado nas próximas etapas de integração.",
                     bg=self.bg,fg="#c6c9d0",font=("Segoe UI",11)).pack(anchor="w")
            if section=="VST Hook": self.show_vsts()
            if section=="Audio":
                tk.Label(self.content,text="O painel ainda não lê o nível de áudio em tempo real. Isso exige integração com a API de áudio do Windows.",
                         bg=self.bg,fg="#969ba5",wraplength=650,justify="left").pack(anchor="w",pady=15)
        else:
            ttk.Button(self.content,text="Selecionar config.txt",command=self.choose_config).pack(anchor="w")
            tk.Label(self.content,text="O arquivo original será preservado por backup antes de qualquer alteração.",
                     bg=self.bg,fg="#969ba5").pack(anchor="w",pady=12)

    def choose_config(self):
        p=filedialog.askopenfilename(title="Selecione o config.txt do Equalizer APO",
             filetypes=[("Arquivo de configuração","*.txt"),("Todos os arquivos","*.*")])
        if not p: return
        self.config_path=Path(p)
        try:
            self.original_text=self.config_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            self.original_text=self.config_path.read_text(encoding="cp1252")
        self.enabled=not any(line.startswith("# SANTIX_BYPASS ") for line in self.original_text.splitlines())
        self.status.config(text=f"Config: {self.config_path}")
        messagebox.showinfo(APP_NAME,"Configuração carregada. Nenhuma alteração foi feita.")
        self.show_section("Home")

    def toggle(self):
        if not self.config_path:
            messagebox.showwarning(APP_NAME,"Selecione primeiro o config.txt do Equalizer APO.")
            return
        current=self.config_path.read_text(encoding="utf-8-sig")
        if self.enabled:
            backup=self.config_path.with_name(self.config_path.name+".santix-backup")
            if not backup.exists(): shutil.copy2(self.config_path,backup)
            lines=current.splitlines()
            changed=[]
            for line in lines:
                if line.strip() and not line.lstrip().startswith("#"):
                    changed.append("# SANTIX_BYPASS "+line)
                else:
                    changed.append(line)
            self.config_path.write_text("\n".join(changed)+("\n" if current.endswith("\n") else ""),encoding="utf-8")
            self.enabled=False
        else:
            backup=self.config_path.with_name(self.config_path.name+".santix-backup")
            if backup.exists():
                # Restore exact original backup, including formatting.
                shutil.copy2(backup,self.config_path)
            else:
                lines=current.splitlines()
                restored=[line[len("# SANTIX_BYPASS "):] if line.startswith("# SANTIX_BYPASS ") else line for line in lines]
                self.config_path.write_text("\n".join(restored)+"\n",encoding="utf-8")
            self.enabled=True
        self.original_text=self.config_path.read_text(encoding="utf-8-sig")
        self.toggle_btn.config(text="EFEITOS: ON" if self.enabled else "EFEITOS: OFF",
                               bg=self.red if self.enabled else "#555a64")
        messagebox.showinfo(APP_NAME,"Estado alterado. Se o Equalizer APO não atualizar automaticamente, reinicie o áudio/aplicativo que usa o microfone.")

    def show_vsts(self):
        if not self.config_path:
            messagebox.showinfo(APP_NAME,"Selecione primeiro seu config.txt.")
            return
        text=self.config_path.read_text(encoding="utf-8-sig",errors="replace")
        found=[x.strip() for x in text.splitlines() if "VSTPlugin:" in x]
        msg="\n".join(found) if found else "Nenhuma linha VSTPlugin encontrada."
        messagebox.showinfo("Plugins encontrados",msg)

if __name__=="__main__":
    root=tk.Tk()
    app=SantixApp(root)
    root.mainloop()
