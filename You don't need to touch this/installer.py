import os
import sys
import shlex
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk

try:
    import PyInstaller.__main__ as pyinstaller_main
except ImportError:
    pyinstaller_main = None


class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        if message:
            self.text_widget.after(0, lambda: self._append(message))

    def flush(self):
        pass

    def _append(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)


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

        log_frame = ttk.LabelFrame(main_frame, text="Build output", padding=8)
        log_frame.grid(row=row, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.output_text = tk.Text(log_frame, width=80, height=18, wrap="word", state="normal")
        self.output_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=scrollbar.set)

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
        self.output_text.delete("1.0", tk.END)
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
            self.log_error("Error: Script path is required.\n")
            self.disable_controls(False)
            return

        if not os.path.exists(script_path):
            self.log_error(f"Error: Script not found: {script_path}\n")
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
            if os.path.exists(icon_path):
                args.extend(["--icon", icon_path])
            else:
                self.log_error(f"Warning: Icon file not found, ignoring: {icon_path}\n")

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
                self.log_error(f"Error parsing extra flags: {error}\n")
                self.disable_controls(False)
                return

        args.append(script_path)
        self.log_info(f"Running PyInstaller with arguments:\n  {' '.join(shlex.quote(arg) for arg in args)}\n\n")

        try:
            self.build_with_pyinstaller(args)
            self.log_info("\nBuild completed. Check the dist folder for the generated executable.\n")
        except subprocess.CalledProcessError as exc:
            self.log_error(f"Build failed: {exc}\n")
        except Exception as exc:
            self.log_error(f"Unexpected error: {exc}\n")
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
        if pyinstaller_main is not None:
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = TextRedirector(self.output_text)
            sys.stderr = TextRedirector(self.output_text)
            try:
                pyinstaller_main.run(args)
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
        else:
            command = [sys.executable, "-m", "PyInstaller"] + args
            self.log_info(f"PyInstaller module not available in embedded environment; executing: {' '.join(shlex.quote(p) for p in command)}\n")
            subprocess.run(command, check=True)

    def log_info(self, message):
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)

    def log_error(self, message):
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)


if __name__ == "__main__":
    app = InstallerGUI()
    app.mainloop()
