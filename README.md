# I'm too lazy to make a readme, here is an ai generated one
## 🎛️ Input Fields & Buttons
Script to build (Browse): Click to select the primary Python script (.py) you want to turn into an executable.

Icon file (Browse): Click to select an icon file (.ico) to give your executable a custom application icon.

Dist path: The folder where your finished, ready-to-use executable will be saved (defaults to dist).

Work path: The temporary folder used to compile your files during the build process (defaults to build).

Spec path: The folder where the PyInstaller .spec configuration file will be created (defaults to current directory .).

## ⚙️ Build Options (Checkboxes)
Onefile: * Checked: Packages everything into a single, standalone executable file.

Unchecked: Puts the executable inside a folder alongside its required dependency files.

No console / windowed: * Checked: Hides the command prompt window when the executable runs (ideal for GUI applications).

Unchecked: Shows the command prompt window (ideal for command-line scripts).

Clean build cache: Cleans out old temporary files before starting the new build to avoid conflicts.

Debug mode: Enables diagnostic tools to help troubleshoot errors if the executable fails to run.

Log level (Dropdown): Adjusts how much detail is shown in the build output window (INFO, WARN, DEBUG, etc.).

## 📥 Advanced Input Fields
Hidden imports: Let you manually type in any Python modules (separated by commas) that PyInstaller might fail to detect automatically.

Add data / Add binary: Let you embed external files (like images, configuration files, or external DLLs) into your executable using the source;destination format.
Note: Files/folders that you add need to be in the same directory as the primary python file

Example: To add 'config.json' to the executeable, use this 'config.json;.' (the dot means to use the root folder of the application)
Example: To add a folder named 'images' and its contents, use 'images/;images/'

Extra PyInstaller flags: A text box to type in any other official PyInstaller command-line arguments that aren't built into this GUI.

## 🚀 Action Controls
Build Executable (Button): Starts the compilation process using all your selected settings. It locks the interface and outputs progress in real-time.

Exit (Button): Closes the application.

Build output (Text Box): A live terminal feed that displays the status, warnings, and success/failure logs of your build.
