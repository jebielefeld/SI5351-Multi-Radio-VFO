# EXE Build Guide

# SI5351 Multi-Radio VFO Control Platform

This document describes how to build the standalone Windows EXE package for the SI5351 Multi-Radio VFO Control Platform.

---

# PURPOSE

The EXE package allows non-programmer ham radio operators to run the application without installing:

- Python
- PySide6
- VS Code
- pip
- development tools

The EXE is built using PyInstaller.

---

# REQUIRED SOFTWARE

## Python

Recommended:

```text
Python 3.12 or newer
```

Download:

https://www.python.org/

---

## Visual Studio Code

Recommended editor:

https://code.visualstudio.com/

---

## GitHub Desktop

Recommended Git client:

https://desktop.github.com/

---

# REQUIRED PYTHON PACKAGES

Install required packages:

```powershell
python -m pip install pyinstaller
python -m pip install pyside6
python -m pip install pyserial
```

---

# OPENING THE PROJECT

Open the repository root in VS Code:

```text
SI5351-Multi-Radio-VFO
```

Do NOT open only:

```text
pc_software
```

Open the full repository root.

---

# OPENING THE TERMINAL

In VS Code:

```text
Terminal
→ New Terminal
```

The terminal should open at:

```text
PS ...\SI5351-Multi-Radio-VFO>
```

---

# FIRST-TIME BUILD TEST

Navigate to:

```powershell
cd pc_software
```

Run:

```powershell
python -m PyInstaller --onefile --windowed --name SI5351_Multi_Radio_VFO main.py
```

---

# DEBUG BUILD

If the EXE fails silently, build a console/debug version:

```powershell
python -m PyInstaller --onefile --console --name SI5351_VFO_Debug main.py
```

Run from terminal:

```powershell
.\dist\SI5351_VFO_Debug.exe
```

This allows crash/error messages to remain visible.

---

# IMPORTANT RUNTIME FILES

The application currently requires:

```text
radio_profiles.json
app_settings.json
```

These files must exist in the same folder as the EXE.

---

# WHY THE FIRST EXE FAILED

Initial EXE builds failed silently because:

```text
radio_profiles.json
app_settings.json
```

were not automatically included by PyInstaller.

This is normal behavior.

---

# BUILD SCRIPT

The project includes:

```text
installer/build_exe.ps1
```

This script:

- cleans old build output
- builds the EXE
- creates package folder
- copies required JSON files

---

# RUNNING THE BUILD SCRIPT

From repository root:

```powershell
.\installer\build_exe.ps1
```

---

# PACKAGE OUTPUT

The final package is created here:

```text
pc_software/dist/SI5351_Multi_Radio_VFO/
```

Contents:

```text
SI5351_Multi_Radio_VFO.exe
radio_profiles.json
app_settings.json
```

---

# TESTING THE EXE

Double-click:

```text
SI5351_Multi_Radio_VFO.exe
```

Expected behavior:

- Main GUI window appears
- Radio profiles load correctly
- COM port system operates
- No Python installation required

---

# COMMON WINDOWS BUILD ISSUES

## PermissionError / Access Denied

Example:

```text
PermissionError: [WinError 5]
```

Cause:

- EXE still running
- Windows Defender scanning
- Explorer locking file

Fix:

- close EXE
- kill process in Task Manager
- rebuild

---

# IMPORTANT GITHUB RULE

Do NOT commit:

```text
build/
dist/
```

generated files to GitHub.

Only commit:

- source code
- documentation
- build scripts
- installer scripts

---

# CURRENT BUILD ARCHITECTURE

Current EXE packaging architecture:

```text
PyInstaller
    ↓
Standalone EXE
    ↓
Package folder with JSON runtime files
    ↓
Future Windows installer
```

---

# FUTURE PACKAGING GOALS

Planned future improvements:

- application icon
- automatic runtime file inclusion
- installer generation
- Start Menu shortcuts
- desktop shortcut option
- automatic versioning
- signed installer package

---

# FUTURE INSTALLER PHASE

Future installer system will likely use:

```text
Inno Setup
```

to generate professional Windows installers.

---

# CURRENT STABLE FREEZE POINT

```text
SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE
```

---

# IMPORTANT ARCHITECTURE RULE

GUI owns all radio frequency translation math.

Arduino Nano firmware remains execution engine only.

Do not move profile math into firmware unless intentionally redesigning architecture.

---

# END OF EXE BUILD GUIDE