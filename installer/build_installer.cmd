@echo off
cd /d "%~dp0"

title Build SI5351 Multi-Radio VFO Installer

echo.
echo ==========================================
echo  SI5351 Multi-Radio VFO - Installer Build
echo ==========================================
echo.

set INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
set PROJECT_ROOT=..
set EXE_PATH=%PROJECT_ROOT%\pc_software\dist\SI5351_Multi_Radio_VFO.exe
set ISS_FILE=SI5351_Multi_Radio_VFO.iss

echo Checking required files...
echo.

if not exist "%INNO_COMPILER%" goto INNO_NOT_FOUND
if not exist "%EXE_PATH%" goto EXE_NOT_FOUND
if not exist "%ISS_FILE%" goto ISS_NOT_FOUND

echo Found Inno compiler:
echo %INNO_COMPILER%
echo.

echo Found EXE:
echo %EXE_PATH%
echo.

echo Found installer script:
echo %ISS_FILE%
echo.

echo Building installer...
echo.

"%INNO_COMPILER%" "%ISS_FILE%"

if errorlevel 1 goto BUILD_FAILED

echo.
echo ==========================================
echo  INSTALLER BUILD SUCCESSFUL
echo ==========================================
echo.
echo Check installer_output folder for setup EXE.
echo.
pause
exit /b 0

:INNO_NOT_FOUND
echo.
echo ==========================================
echo  BUILD FAILED
echo ==========================================
echo.
echo Inno Setup compiler not found:
echo %INNO_COMPILER%
echo.
pause
exit /b 1

:EXE_NOT_FOUND
echo.
echo ==========================================
echo  BUILD FAILED
echo ==========================================
echo.
echo Built application EXE not found:
echo %EXE_PATH%
echo.
echo Run build_exe.bat first.
echo.
pause
exit /b 1

:ISS_NOT_FOUND
echo.
echo ==========================================
echo  BUILD FAILED
echo ==========================================
echo.
echo Inno installer script not found:
echo %ISS_FILE%
echo.
pause
exit /b 1

:BUILD_FAILED
echo.
echo ==========================================
echo  INSTALLER BUILD FAILED
echo ==========================================
echo.
echo Check Inno Setup error messages above.
echo.
pause
exit /b 1