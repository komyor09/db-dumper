#!/usr/bin/env python3
"""
db_dump GUI — графический интерфейс для db_dump.py
Запуск: python db_dump_gui.py
"""

import json
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CONFIG_PATH = Path.home() / ".db_dump_config.json"

# ─────────────────────────────────────────────
# ЦВЕТА И СТИЛИ
# ─────────────────────────────────────────────
BG          = "#0f1117"
BG2         = "#1a1d27"
BG3         = "#222536"
BORDER      = "#2e3250"
ACCENT      = "#4f8ef7"
ACCENT2     = "#38c98a"
DANGER      = "#f7604f"
WARN        = "#f7c94f"
TEXT        = "#e8eaf0"
TEXT2       = "#8b90a8"
TEXT3       = "#555a73"
FONT_MONO   = ("Consolas", 10)
FONT_UI     = ("Segoe UI", 10)
FONT_LABEL  = ("Segoe UI", 9)
FONT_TITLE  = ("Segoe UI Semibold", 11)
FONT_HEAD   = ("Segoe UI Semibold", 13)


# ─────────────────────────────────────────────
# КОНФИГ
# ─────────────────────────────────────────────

def load_raw():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_raw(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# ГЛАВНОЕ ОКНО
# ─────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("db_dump  —  MySQL Dump & Restore")
        self.geometry("960x680")
        self.minsize(820, 580)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Иконка (игнорируем если нет)
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._build()
        self._load_config()

    def _build(self):
        # ── Левая панель ──────────────────────────
        left = tk.Frame(self, bg=BG2, width=200)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="🗄  db_dump", font=("Segoe UI Semibold", 14),
                 bg=BG2, fg=TEXT, pady=20).pack(fill="x", padx=16)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", padx=12)

        self._nav_btns = []
        nav_items = [
            ("⚙  Source",   self._show_source),
            ("⚙  Target",   self._show_target),
            ("📦  Dump",     self._show_dump),
            ("🔄  Restore",  self._show_restore),
            ("📋  Лог",      self._show_log),
        ]
        for label, cmd in nav_items:
            b = tk.Button(left, text=label, font=FONT_UI, anchor="w",
                          bg=BG2, fg=TEXT2, bd=0, padx=20, pady=10,
                          activebackground=BG3, activeforeground=TEXT,
                          cursor="hand2", relief="flat",
                          command=cmd)
            b.pack(fill="x")
            self._nav_btns.append(b)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)

        # Статус соединений
        self._src_status = tk.Label(left, text="● Source: —", font=FONT_LABEL,
                                     bg=BG2, fg=TEXT3, anchor="w", padx=16)
        self._src_status.pack(fill="x")
        self._tgt_status = tk.Label(left, text="● Target: —", font=FONT_LABEL,
                                     bg=BG2, fg=TEXT3, anchor="w", padx=16)
        self._tgt_status.pack(fill="x")

        # Версия
        tk.Label(left, text="v2.0", font=FONT_LABEL,
                 bg=BG2, fg=TEXT3).pack(side="bottom", pady=12)

        # ── Правая панель ─────────────────────────
        self._main = tk.Frame(self, bg=BG)
        self._main.pack(side="right", fill="both", expand=True)

        # Страницы
        self._pages = {}
        for Page in [SourcePage, TargetPage, DumpPage, RestorePage, LogPage]:
            p = Page(self._main, self)
            self._pages[Page.__name__] = p
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._show_source()

    def _show_page(self, name, btn_idx):
        self._pages[name].lift()
        for i, b in enumerate(self._nav_btns):
            b.configure(bg=BG3 if i == btn_idx else BG2,
                        fg=ACCENT if i == btn_idx else TEXT2)

    def _show_source(self):  self._show_page("SourcePage", 0)
    def _show_target(self):  self._show_page("TargetPage", 1)
    def _show_dump(self):    self._show_page("DumpPage", 2)
    def _show_restore(self): self._show_page("RestorePage", 3)
    def _show_log(self):     self._show_page("LogPage", 4)

    def _load_config(self):
        raw = load_raw()
        self._pages["SourcePage"].load(raw.get("source", {}))
        self._pages["TargetPage"].load(raw.get("target", {}))

    def log(self, text, tag=None):
        self._pages["LogPage"].append(text, tag)

    def set_src_status(self, ok):
        if ok:
            self._src_status.configure(text="● Source: ✓", fg=ACCENT2)
        else:
            self._src_status.configure(text="● Source: ✗", fg=DANGER)

    def set_tgt_status(self, ok):
        if ok:
            self._tgt_status.configure(text="● Target: ✓", fg=ACCENT2)
        else:
            self._tgt_status.configure(text="● Target: ✗", fg=DANGER)


# ─────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ
# ─────────────────────────────────────────────

def field_row(parent, label, default="", show=None, width=28):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, font=FONT_LABEL, bg=BG, fg=TEXT2,
             width=18, anchor="w").pack(side="left")
    var = tk.StringVar(value=default)
    kw = {"show": show} if show else {}
    e = tk.Entry(row, textvariable=var, font=FONT_MONO, bg=BG3, fg=TEXT,
                 insertbackground=TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=width, **kw)
    e.pack(side="left", ipady=5, padx=(0, 4))
    return var

def section_title(parent, text):
    tk.Label(parent, text=text, font=FONT_HEAD, bg=BG, fg=TEXT,
             pady=10).pack(anchor="w")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

def accent_btn(parent, text, command, color=ACCENT, width=14):
    b = tk.Button(parent, text=text, command=command,
                  font=("Segoe UI Semibold", 10),
                  bg=color, fg="#ffffff", relief="flat", bd=0,
                  padx=16, pady=8, cursor="hand2",
                  activebackground=color, activeforeground="#ffffff",
                  width=width)
    return b

def ghost_btn(parent, text, command, width=14):
    b = tk.Button(parent, text=text, command=command,
                  font=FONT_UI, bg=BG3, fg=TEXT2, relief="flat", bd=0,
                  padx=14, pady=7, cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  highlightthickness=1, highlightbackground=BORDER,
                  width=width)
    return b


# ─────────────────────────────────────────────
# SOURCE PAGE
# ─────────────────────────────────────────────

class SourcePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=36, pady=28)

        section_title(pad, "Source — откуда дампить")

        self._host = field_row(pad, "Host",     "localhost")
        self._port = field_row(pad, "Port",     "3306")
        self._user = field_row(pad, "User",     "root")
        self._pass = field_row(pad, "Password", "", show="●")

        # Databases
        db_row = tk.Frame(pad, bg=BG)
        db_row.pack(fill="x", pady=3)
        tk.Label(db_row, text="Databases", font=FONT_LABEL, bg=BG, fg=TEXT2,
                 width=18, anchor="w").pack(side="left")
        self._db_var = tk.StringVar()
        tk.Entry(db_row, textvariable=self._db_var, font=FONT_MONO,
                 bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=40).pack(side="left", ipady=5)
        tk.Label(db_row, text="  (через пробел)", font=FONT_LABEL,
                 bg=BG, fg=TEXT3).pack(side="left")

        tk.Frame(pad, bg=BG, height=16).pack()

        row = tk.Frame(pad, bg=BG)
        row.pack(anchor="w", fill="x")
        accent_btn(row, "💾  Сохранить", self._save).pack(side="left", padx=(0, 8))
        ghost_btn(row, "🔌  Тест соединения", self._test).pack(side="left")

        # Статус
        self._status = tk.Label(pad, text="", font=FONT_LABEL, bg=BG, fg=TEXT2)
        self._status.pack(anchor="w", pady=(10, 0))

    def load(self, d):
        self._host.set(d.get("host", "localhost"))
        self._port.set(str(d.get("port", 3306)))
        self._user.set(d.get("user", "root"))
        self._db_var.set(" ".join(d.get("databases", [])))

    def _save(self):
        raw = load_raw()
        raw["source"] = {
            "host": self._host.get(),
            "port": int(self._port.get() or 3306),
            "user": self._user.get(),
            "password": "",
            "databases": self._db_var.get().split(),
        }
        save_raw(raw)
        self._status.configure(text="✓ Сохранено", fg=ACCENT2)

    def _test(self):
        self._status.configure(text="⏳ Подключение...", fg=WARN)
        self.update()
        def run():
            cfg = self._get_cfg()
            cmd = ["mysql",
                   f"--host={cfg['host']}", f"--port={cfg['port']}",
                   f"--user={cfg['user']}", f"--password={cfg['password']}",
                   "--default-character-set=utf8mb4", "-N", "-e", "SELECT VERSION();"]
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=8)
                if r.returncode == 0:
                    ver = r.stdout.decode("utf-8", errors="replace").strip()
                    self.after(0, lambda: self._status.configure(
                        text=f"✓ Подключено  ({ver})", fg=ACCENT2))
                    self.after(0, lambda: self.app.set_src_status(True))
                else:
                    err = r.stderr.decode("utf-8", errors="replace").strip()
                    self.after(0, lambda: self._status.configure(
                        text=f"✗ Ошибка: {err[:80]}", fg=DANGER))
                    self.after(0, lambda: self.app.set_src_status(False))
            except Exception as e:
                self.after(0, lambda: self._status.configure(
                    text=f"✗ {e}", fg=DANGER))
        threading.Thread(target=run, daemon=True).start()

    def _get_cfg(self):
        return {
            "host": self._host.get(),
            "port": int(self._port.get() or 3306),
            "user": self._user.get(),
            "password": self._pass.get(),
            "databases": self._db_var.get().split(),
        }

    def get(self):
        return self._get_cfg()


# ─────────────────────────────────────────────
# TARGET PAGE
# ─────────────────────────────────────────────

class TargetPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=36, pady=28)

        section_title(pad, "Target — куда восстанавливать")

        self._host = field_row(pad, "Host",     "localhost")
        self._port = field_row(pad, "Port",     "3306")
        self._user = field_row(pad, "User",     "root")
        self._pass = field_row(pad, "Password", "", show="●")

        tk.Frame(pad, bg=BG, height=16).pack()

        row = tk.Frame(pad, bg=BG)
        row.pack(anchor="w", fill="x")
        accent_btn(row, "💾  Сохранить", self._save).pack(side="left", padx=(0, 8))
        ghost_btn(row, "🔌  Тест соединения", self._test).pack(side="left")

        self._status = tk.Label(pad, text="", font=FONT_LABEL, bg=BG, fg=TEXT2)
        self._status.pack(anchor="w", pady=(10, 0))

    def load(self, d):
        self._host.set(d.get("host", "localhost"))
        self._port.set(str(d.get("port", 3306)))
        self._user.set(d.get("user", "root"))

    def _save(self):
        raw = load_raw()
        raw["target"] = {
            "host": self._host.get(),
            "port": int(self._port.get() or 3306),
            "user": self._user.get(),
            "password": "",
        }
        save_raw(raw)
        self._status.configure(text="✓ Сохранено", fg=ACCENT2)

    def _test(self):
        self._status.configure(text="⏳ Подключение...", fg=WARN)
        self.update()
        def run():
            cfg = self.get()
            cmd = ["mysql",
                   f"--host={cfg['host']}", f"--port={cfg['port']}",
                   f"--user={cfg['user']}", f"--password={cfg['password']}",
                   "--default-character-set=utf8mb4", "-N", "-e", "SELECT VERSION();"]
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=8)
                if r.returncode == 0:
                    ver = r.stdout.decode("utf-8", errors="replace").strip()
                    self.after(0, lambda: self._status.configure(
                        text=f"✓ Подключено  ({ver})", fg=ACCENT2))
                    self.after(0, lambda: self.app.set_tgt_status(True))
                else:
                    err = r.stderr.decode("utf-8", errors="replace").strip()
                    self.after(0, lambda: self._status.configure(
                        text=f"✗ Ошибка: {err[:80]}", fg=DANGER))
                    self.after(0, lambda: self.app.set_tgt_status(False))
            except Exception as e:
                self.after(0, lambda: self._status.configure(
                    text=f"✗ {e}", fg=DANGER))
        threading.Thread(target=run, daemon=True).start()

    def get(self):
        return {
            "host": self._host.get(),
            "port": int(self._port.get() or 3306),
            "user": self._user.get(),
            "password": self._pass.get(),
        }


# ─────────────────────────────────────────────
# DUMP PAGE
# ─────────────────────────────────────────────

class DumpPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._running = False
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=36, pady=28)

        section_title(pad, "Dump — создать резервную копию")

        # Dir
        dir_row = tk.Frame(pad, bg=BG)
        dir_row.pack(fill="x", pady=3)
        tk.Label(dir_row, text="Папка для дампа", font=FONT_LABEL,
                 bg=BG, fg=TEXT2, width=18, anchor="w").pack(side="left")
        self._dir = tk.StringVar(value="dump")
        tk.Entry(dir_row, textvariable=self._dir, font=FONT_MONO,
                 bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=30).pack(side="left", ipady=5)
        ghost_btn(dir_row, "📂", self._browse_dir, width=3).pack(side="left", padx=4)

        # Опции
        opt_row = tk.Frame(pad, bg=BG)
        opt_row.pack(fill="x", pady=(12, 4))
        tk.Label(opt_row, text="Опции", font=FONT_LABEL,
                 bg=BG, fg=TEXT2, width=18, anchor="w").pack(side="left")
        self._no_definer = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_row, text="Не чистить DEFINER",
                       variable=self._no_definer,
                       bg=BG, fg=TEXT2, selectcolor=BG3,
                       activebackground=BG, activeforeground=TEXT,
                       font=FONT_LABEL).pack(side="left")

        tk.Frame(pad, bg=BG, height=16).pack()

        # Прогрессбар
        self._progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor=BG3, background=ACCENT,
                        borderwidth=0, thickness=6)
        self._pb = ttk.Progressbar(pad, variable=self._progress_var,
                                   maximum=100, length=400,
                                   style="Custom.Horizontal.TProgressbar")
        self._pb.pack(anchor="w", pady=(0, 8))

        self._status = tk.Label(pad, text="Готов к запуску", font=FONT_LABEL,
                                bg=BG, fg=TEXT2)
        self._status.pack(anchor="w", pady=(0, 16))

        row = tk.Frame(pad, bg=BG)
        row.pack(anchor="w")
        self._run_btn = accent_btn(row, "▶  Запустить Dump", self._run, color=ACCENT)
        self._run_btn.pack(side="left", padx=(0, 8))

        # Мини лог
        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(20, 8))
        tk.Label(pad, text="Вывод", font=FONT_LABEL, bg=BG, fg=TEXT3).pack(anchor="w")
        log_frame = tk.Frame(pad, bg=BG3, highlightthickness=1,
                             highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        self._log = tk.Text(log_frame, font=FONT_MONO, bg=BG3, fg=TEXT2,
                            insertbackground=TEXT, relief="flat", bd=0,
                            state="disabled", wrap="word")
        sb = tk.Scrollbar(log_frame, command=self._log.yview, bg=BG3,
                          troughcolor=BG3, width=8)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=8, pady=6)
        self._log.tag_configure("ok",   foreground=ACCENT2)
        self._log.tag_configure("err",  foreground=DANGER)
        self._log.tag_configure("warn", foreground=WARN)
        self._log.tag_configure("head", foreground=ACCENT)

    def _browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self._dir.set(d)

    def _write(self, text, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag or "")
        self._log.see("end")
        self._log.configure(state="disabled")
        self.app.log(text, tag)

    def _run(self):
        if self._running:
            return
        self._running = True
        self._run_btn.configure(state="disabled", text="⏳ Выполняется...")
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._progress_var.set(0)

        src = self.app._pages["SourcePage"].get()
        dir_ = self._dir.get() or "dump"
        no_def = self._no_definer.get()

        def run():
            steps = ["config-show", None]  # dummy
            cmd = [sys.executable, "db_dump.py", "dump",
                   f"--src-host={src['host']}",
                   f"--src-port={src['port']}",
                   f"--src-user={src['user']}",
                   f"--src-password={src['password']}",
                   f"--dir={dir_}"]
            if src["databases"]:
                cmd += ["--src-db"] + src["databases"]
            if no_def:
                cmd.append("--no-clean-definer")

            step_map = {
                "1/6": 14, "2/6": 28, "3/6": 42,
                "4/6": 56, "5/6": 70, "6/6": 84, "POST": 92,
            }

            self.after(0, lambda: self._status.configure(
                text="Выполняется дамп...", fg=WARN))
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    bufsize=1
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    if not line:
                        continue
                    tag = None
                    if "✓" in line or "[OK]" in line:
                        tag = "ok"
                    elif "✗" in line or "ERROR" in line or "Ошибка" in line:
                        tag = "err"
                    elif "DUMP" in line or "STEP" in line or "─" in line:
                        tag = "head"
                    self.after(0, lambda l=line, t=tag: self._write(l, t))
                    for key, pct in step_map.items():
                        if key in line:
                            self.after(0, lambda p=pct: self._progress_var.set(p))
                proc.wait()
                ok = proc.returncode == 0
                self.after(0, lambda: self._progress_var.set(100 if ok else 0))
                self.after(0, lambda: self._status.configure(
                    text="✓ Дамп завершён успешно!" if ok else "✗ Дамп завершён с ошибками",
                    fg=ACCENT2 if ok else DANGER))
            except FileNotFoundError:
                self.after(0, lambda: self._write(
                    "✗ db_dump.py не найден в текущей папке", "err"))
                self.after(0, lambda: self._status.configure(
                    text="✗ Файл db_dump.py не найден", fg=DANGER))
            finally:
                self._running = False
                self.after(0, lambda: self._run_btn.configure(
                    state="normal", text="▶  Запустить Dump"))

        threading.Thread(target=run, daemon=True).start()


# ─────────────────────────────────────────────
# RESTORE PAGE
# ─────────────────────────────────────────────

class RestorePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._running = False
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=36, pady=28)

        section_title(pad, "Restore — восстановить из дампа")

        dir_row = tk.Frame(pad, bg=BG)
        dir_row.pack(fill="x", pady=3)
        tk.Label(dir_row, text="Папка с дампом", font=FONT_LABEL,
                 bg=BG, fg=TEXT2, width=18, anchor="w").pack(side="left")
        self._dir = tk.StringVar(value="dump")
        tk.Entry(dir_row, textvariable=self._dir, font=FONT_MONO,
                 bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=30).pack(side="left", ipady=5)
        ghost_btn(dir_row, "📂", self._browse_dir, width=3).pack(side="left", padx=4)

        opt_row = tk.Frame(pad, bg=BG)
        opt_row.pack(fill="x", pady=(12, 4))
        tk.Label(opt_row, text="Опции", font=FONT_LABEL,
                 bg=BG, fg=TEXT2, width=18, anchor="w").pack(side="left")
        self._clean = tk.BooleanVar(value=True)
        self._force = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_row, text="--clean  (DROP+CREATE перед импортом)",
                       variable=self._clean,
                       bg=BG, fg=TEXT2, selectcolor=BG3,
                       activebackground=BG, activeforeground=TEXT,
                       font=FONT_LABEL).pack(side="left", padx=(0, 16))
        tk.Checkbutton(opt_row, text="--force  (продолжать при ошибках)",
                       variable=self._force,
                       bg=BG, fg=TEXT2, selectcolor=BG3,
                       activebackground=BG, activeforeground=TEXT,
                       font=FONT_LABEL).pack(side="left")

        tk.Frame(pad, bg=BG, height=16).pack()

        self._progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.configure("Restore.Horizontal.TProgressbar",
                        troughcolor=BG3, background=ACCENT2,
                        borderwidth=0, thickness=6)
        self._pb = ttk.Progressbar(pad, variable=self._progress_var,
                                   maximum=100, length=400,
                                   style="Restore.Horizontal.TProgressbar")
        self._pb.pack(anchor="w", pady=(0, 8))

        self._status = tk.Label(pad, text="Готов к запуску", font=FONT_LABEL,
                                bg=BG, fg=TEXT2)
        self._status.pack(anchor="w", pady=(0, 16))

        row = tk.Frame(pad, bg=BG)
        row.pack(anchor="w")
        self._run_btn = accent_btn(row, "▶  Запустить Restore",
                                   self._run, color=ACCENT2)
        self._run_btn.pack(side="left")

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(20, 8))
        tk.Label(pad, text="Вывод", font=FONT_LABEL, bg=BG, fg=TEXT3).pack(anchor="w")
        log_frame = tk.Frame(pad, bg=BG3, highlightthickness=1,
                             highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        self._log = tk.Text(log_frame, font=FONT_MONO, bg=BG3, fg=TEXT2,
                            insertbackground=TEXT, relief="flat", bd=0,
                            state="disabled", wrap="word")
        sb = tk.Scrollbar(log_frame, command=self._log.yview, bg=BG3,
                          troughcolor=BG3, width=8)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=8, pady=6)
        self._log.tag_configure("ok",   foreground=ACCENT2)
        self._log.tag_configure("err",  foreground=DANGER)
        self._log.tag_configure("warn", foreground=WARN)
        self._log.tag_configure("head", foreground=ACCENT)

    def _browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self._dir.set(d)

    def _write(self, text, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag or "")
        self._log.see("end")
        self._log.configure(state="disabled")
        self.app.log(text, tag)

    def _run(self):
        if self._running:
            return
        self._running = True
        self._run_btn.configure(state="disabled", text="⏳ Выполняется...")
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._progress_var.set(0)

        tgt = self.app._pages["TargetPage"].get()
        dir_ = self._dir.get() or "dump"

        def run():
            cmd = [sys.executable, "db_dump.py", "restore",
                   f"--tgt-host={tgt['host']}",
                   f"--tgt-port={tgt['port']}",
                   f"--tgt-user={tgt['user']}",
                   f"--tgt-password={tgt['password']}",
                   f"--dir={dir_}"]
            if self._clean.get():
                cmd.append("--clean")
            if self._force.get():
                cmd.append("--force")

            step_map = {
                "routines.sql": 14, "structure.sql": 28, "data.sql": 56,
                "views.sql": 70, "triggers.sql": 84, "events.sql": 96,
            }

            self.after(0, lambda: self._status.configure(
                text="Выполняется restore...", fg=WARN))
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace", bufsize=1
                )
                for line in proc.stdout:
                    line = line.rstrip()
                    if not line:
                        continue
                    tag = None
                    if "✓" in line:
                        tag = "ok"
                    elif "✗" in line or "ERROR" in line:
                        tag = "err"
                    elif "RESTORE" in line or "STEP" in line or "─" in line:
                        tag = "head"
                    self.after(0, lambda l=line, t=tag: self._write(l, t))
                    for key, pct in step_map.items():
                        if key in line:
                            self.after(0, lambda p=pct: self._progress_var.set(p))
                proc.wait()
                ok = proc.returncode == 0
                self.after(0, lambda: self._progress_var.set(100 if ok else 0))
                self.after(0, lambda: self._status.configure(
                    text="✓ Restore завершён успешно!" if ok else "✗ Restore завершён с ошибками",
                    fg=ACCENT2 if ok else DANGER))
            except FileNotFoundError:
                self.after(0, lambda: self._write(
                    "✗ db_dump.py не найден в текущей папке", "err"))
                self.after(0, lambda: self._status.configure(
                    text="✗ Файл db_dump.py не найден", fg=DANGER))
            finally:
                self._running = False
                self.after(0, lambda: self._run_btn.configure(
                    state="normal", text="▶  Запустить Restore"))

        threading.Thread(target=run, daemon=True).start()


# ─────────────────────────────────────────────
# LOG PAGE
# ─────────────────────────────────────────────

class LogPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=36, pady=28)

        hdr = tk.Frame(pad, bg=BG)
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(hdr, text="Полный лог", font=FONT_HEAD,
                 bg=BG, fg=TEXT).pack(side="left")
        ghost_btn(hdr, "🗑  Очистить",
                  lambda: self._clear(), width=12).pack(side="right")

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        log_frame = tk.Frame(pad, bg=BG3, highlightthickness=1,
                             highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)
        self._log = tk.Text(log_frame, font=FONT_MONO, bg=BG3, fg=TEXT2,
                            insertbackground=TEXT, relief="flat", bd=0,
                            state="disabled", wrap="word")
        sb = tk.Scrollbar(log_frame, command=self._log.yview,
                          bg=BG3, troughcolor=BG3, width=8)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=8, pady=6)
        self._log.tag_configure("ok",   foreground=ACCENT2)
        self._log.tag_configure("err",  foreground=DANGER)
        self._log.tag_configure("warn", foreground=WARN)
        self._log.tag_configure("head", foreground=ACCENT)

    def append(self, text, tag=None):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag or "")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
