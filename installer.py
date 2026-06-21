import os
import sys
import shlex
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyInstaller Builder")
        self.resizable(True, True)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=12)
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.script_var = tk.StringVar()
        self.icon_var = tk.StringVar()
        self.dist_var = tk.StringVar(value="dist")
        self.work_var = tk.StringVar(value="build")
        self.spec_var = tk.StringVar(value=".")
        self.onefile_var = tk.BooleanVar(value=True)
        self.noconsole_var = tk.BooleanVar(value=True)
        self.clean_var = tk.BooleanVar(value=True)
        self.debug_var = tk.BooleanVar(value=False)
        self.loglevel_var = tk.StringVar(value="INFO")
        self.hidden_imports_var = tk.StringVar()
        self.add_data_text = None
        self.add_binary_text = None
        self.extra_args_var = tk.StringVar()

        row = 0
        self._add_labeled_entry(main_frame, "Script to build:", self.script_var, row, browse_command=self.browse_script)
        row += 1
        self._add_labeled_entry(main_frame, "Icon file (optional):", self.icon_var, row, browse_command=self.browse_icon)
        row += 1
        self._add_labeled_entry(main_frame, "Dist path:", self.dist_var, row)
        row += 1
        self._add_labeled_entry(main_frame, "Work path:", self.work_var, row)
        row += 1
        self._add_labeled_entry(main_frame, "Spec path:", self.spec_var, row)
        row += 1

        options_frame = ttk.LabelFrame(main_frame, text="Build options", padding=8)
        options_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 0))

        ttk.Checkbutton(options_frame, text="Onefile", variable=self.onefile_var).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(options_frame, text="No console / windowed", variable=self.noconsole_var).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(options_frame, text="Clean build cache", variable=self.clean_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(options_frame, text="Debug mode", variable=self.debug_var).grid(row=1, column=1, sticky="w")

        ttk.Label(options_frame, text="Log level:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.OptionMenu(options_frame, self.loglevel_var, self.loglevel_var.get(), "INFO", "WARN", "DEBUG", "TRACE", "ERROR").grid(row=2, column=1, sticky="ew", pady=(6, 0))
        row += 1

        self._add_labeled_entry(main_frame, "Hidden imports (comma-separated):", self.hidden_imports_var, row)
        row += 1
        self.add_data_text = self._add_labeled_text(main_frame, "Add data (each line src;dest):", row)
        row += 1
        self.add_binary_text = self._add_labeled_text(main_frame, "Add binary (each line src;dest):", row)
        row += 1
        self._add_labeled_entry(main_frame, "Extra PyInstaller flags:", self.extra_args_var, row)
        row += 1

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        ttk.Button(button_frame, text="Build Executable", command=self.on_build).grid(row=0, column=0, sticky="ew")
        ttk.Button(button_frame, text="Exit", command=self.destroy).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        row += 1

    def _add_labeled_entry(self, parent, label_text, text_variable, row, browse_command=None):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=(6, 0))
        entry = ttk.Entry(parent, textvariable=text_variable, width=72)
        entry.grid(row=row, column=1, sticky="ew", pady=(6, 0))
        if browse_command:
            ttk.Button(parent, text="Browse", command=browse_command).grid(row=row, column=2, padx=(8, 0), pady=(6, 0))
        parent.columnconfigure(1, weight=1)

    def _add_labeled_text(self, parent, label_text, row, height=4):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="nw", pady=(6, 0))
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=(6, 0))
        text_widget = tk.Text(frame, width=72, height=height, wrap="none")
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text_widget.configure(yscrollcommand=scrollbar.set)
        frame.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        return text_widget

    def browse_script(self):
        path = filedialog.askopenfilename(title="Select Python script", filetypes=[("Python files", "*.py"), ("All files", "*")])
        if path:
            self.script_var.set(path)

    def browse_icon(self):
        path = filedialog.askopenfilename(title="Select icon file", filetypes=[("Icon files", "*.ico"), ("All files", "*")])
        if path:
            self.icon_var.set(path)

    def on_build(self):
        self.disable_controls(True)
        thread = threading.Thread(target=self.run_build, daemon=True)
        thread.start()

    def disable_controls(self, disabled):
        for child in self.winfo_children():
            self._set_state_recursive(child, disabled)

    def _set_state_recursive(self, widget, disabled):
        if isinstance(widget, tk.Text):
            return
        try:
            widget.configure(state="disabled" if disabled else "normal")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_state_recursive(child, disabled)

    def run_build(self):
        script_path = self.script_var.get().strip()
        if not script_path:
            self.notify("Build error", "Error: Script path is required.", error=True)
            self.disable_controls(False)
            return

        if not os.path.exists(script_path):
            self.notify("Build error", f"Error: Script not found:\n{script_path}", error=True)
            self.disable_controls(False)
            return

        args = []
        if self.onefile_var.get():
            args.append("--onefile")
        else:
            args.append("--onedir")

        if self.noconsole_var.get():
            args.append("--noconsole")
        else:
            args.append("--console")

        if self.clean_var.get():
            args.append("--clean")

        if self.debug_var.get():
            args.append("--debug=all")

        log_level = self.loglevel_var.get().strip().upper()
        if log_level:
            args.append(f"--log-level={log_level}")

        icon_path = self.icon_var.get().strip()
        if icon_path:
            icon_path = os.path.normpath(os.path.abspath(os.path.expanduser(icon_path)))
            if os.path.isfile(icon_path):
                if os.name == "nt" and not icon_path.lower().endswith(".ico"):
                    self.notify("Build warning", "Windows icon files should use the .ico extension.", error=False)
                args.extend(["--icon", icon_path])
            else:
                self.notify("Build warning", f"Icon file not found or not a file, ignoring:\n{icon_path}")

        dist_path = self.dist_var.get().strip()
        if dist_path:
            args.extend(["--distpath", dist_path])

        work_path = self.work_var.get().strip()
        if work_path:
            args.extend(["--workpath", work_path])

        spec_path = self.spec_var.get().strip()
        if spec_path:
            args.extend(["--specpath", spec_path])

        self.add_path_flags(args, "--hidden-import", self.hidden_imports_var.get())
        self.add_data_or_binary(args, "--add-data", self.add_data_text.get("1.0", "end").strip())
        self.add_data_or_binary(args, "--add-binary", self.add_binary_text.get("1.0", "end").strip())

        extra = self.extra_args_var.get().strip()
        if extra:
            try:
                args.extend(shlex.split(extra))
            except ValueError as error:
                self.notify("Build error", f"Error parsing extra flags:\n{error}", error=True)
                self.disable_controls(False)
                return

        args.append(script_path)

        try:
            self.build_with_pyinstaller(args)
            self.notify("Build completed", "PyInstaller finished successfully. Check the dist folder for the generated executable.")
        except subprocess.CalledProcessError as exc:
            self.notify("Build failed", f"PyInstaller exited with error code {exc.returncode}.", error=True)
        except FileNotFoundError as exc:
            self.notify("Build failed", str(exc), error=True)
        except Exception as exc:
            self.notify("Build failed", f"Unexpected error:\n{exc}", error=True)
        finally:
            self.disable_controls(False)

    def add_path_flags(self, args, flag, value):
        if not value:
            return
        for item in value.split(","):
            normalized = item.strip()
            if normalized:
                args.extend([flag, normalized])

    def add_data_or_binary(self, args, flag, value):
        if not value:
            return
        lines = value.strip().splitlines()
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                if ";" in cleaned or ":" in cleaned:
                    args.extend([flag, cleaned])
                else:
                    args.extend([flag, f"{cleaned};."])

    def build_with_pyinstaller(self, args):
        python_command = self.find_python_command()
        command = python_command + ["-m", "PyInstaller"] + args
        #self.notify("Build started", "Build output will appear in a new terminal window.")

        if os.name == "nt":
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.run(command, check=True, creationflags=CREATE_NEW_CONSOLE)
        else:
            subprocess.run(command, check=True)

    def find_python_command(self):
        if not getattr(sys, "frozen", False):
            return [sys.executable]

        base_exec = getattr(sys, "_base_executable", None)
        if base_exec and os.path.basename(base_exec).lower().startswith("python"):
            return [base_exec]

        candidates = [["py", "-3"], ["python"], ["py"]]
        for candidate in candidates:
            if self._is_valid_python_command(candidate):
                return candidate

        raise FileNotFoundError("No Python interpreter found on PATH. Install Python and ensure it is available in PATH.")

    def _is_valid_python_command(self, candidate):
        try:
            subprocess.run(candidate + ["-c", "import sys"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False

    def notify(self, title, message, error=False):
        if error:
            self.after(0, lambda: messagebox.showerror(title, message))
        else:
            self.after(0, lambda: messagebox.showinfo(title, message))


if __name__ == "__main__":
    app = InstallerGUI()
    app.mainloop()
