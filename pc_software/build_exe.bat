@echo off
title Build SI5351 Multi-Radio VFO EXE

echo.
echo ==========================================
echo  SI5351 Multi-Radio VFO - EXE Build
echo ==========================================
echo.

echo Cleaning old build folders...
if exist build rmdir /S /Q build
if errorlevel 1 goto BUILD_FAILED

if exist dist rmdir /S /Q dist
if errorlevel 1 goto BUILD_FAILED

if exist SI5351_Multi_Radio_VFO.spec del SI5351_Multi_Radio_VFO.spec
if errorlevel 1 goto BUILD_FAILED

echo.
echo Building fresh EXE with PyInstaller...
echo.

pyinstaller --onefile --windowed ^
 --icon=..\assets\SI5351_Multi_Radio_VFO.ico ^
 --add-data "radio_profiles.json;." ^
 --name SI5351_Multi_Radio_VFO ^
 main.py

if errorlevel 1 goto BUILD_FAILED

if not exist dist\SI5351_Multi_Radio_VFO.exe goto BUILD_FAILED

echo.
echo ==========================================
echo  BUILD SUCCESSFUL
echo ==========================================
echo.
echo Output file:
echo dist\SI5351_Multi_Radio_VFO.exe
echo.
pause
exit /b 0

:BUILD_FAILED
echo.
echo ==========================================
echo  BUILD FAILED
echo ==========================================
echo.
echo Possible causes:
echo - SI5351_Multi_Radio_VFO.exe is still running
echo - dist folder is locked
echo - antivirus is scanning the EXE
echo - icon file path is wrong
echo - PyInstaller error occurred
echo.
echo Check Task Manager for:
echo SI5351_Multi_Radio_VFO.exe
echo python.exe
echo.
pause
exit /b 1