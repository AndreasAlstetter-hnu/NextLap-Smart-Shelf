@echo off
setlocal ENABLEDELAYEDEXPANSION

rem --- [NEU] minimiert neu starten, falls noch nicht minimiert ---
if /i "%~1" neq "/min" (
  start "" /min "%~f0" /min
  exit /b
)
shift
rem --- [NEU] Ende Relaunch ---

rem === KONFIG ===
set "APP_DIR=C:\Users\Drohnen GmbH\source\repos\NextLap-Smart-Shelf\Next_Lab_Demo\Test_NextLab\Test_Code"
set "MAIN=main.py"
set "PORT=8310"   rem optional: gewünschter Port (wird als NEXTLAB_PORT gesetzt)

rem === Python wählen: venv -> py -3 -> python ===
set "PY_FILE="
set "PY_ARGS="

if exist "%APP_DIR%\venv\Scripts\python.exe" (
  "%APP_DIR%\venv\Scripts\python.exe" -c "print('ok')" >nul 2>&1 && set "PY_FILE=%APP_DIR%\venv\Scripts\python.exe"
)
if not defined PY_FILE (
  py -3 -c "print('ok')" >nul 2>&1 && ( set "PY_FILE=py" & set "PY_ARGS=-3" )
)
if not defined PY_FILE (
  python -c "print('ok')" >nul 2>&1 && set "PY_FILE=python"
)
if not defined PY_FILE (
  echo [FATAL] Kein funktionsfaehiger Python-Interpreter gefunden.
  pause & exit /b 1
)

if not exist "%APP_DIR%\%MAIN%" (
  echo [FATAL] Nicht gefunden: %APP_DIR%\%MAIN%
  pause & exit /b 1
)

cd /d "%APP_DIR%"
set "NEXTLAB_PORT=%PORT%"
echo Starte %MAIN% (Port %NEXTLAB_PORT%). Beenden mit STRG+C.

if defined PY_ARGS (
  call %PY_FILE% %PY_ARGS% -u "%MAIN%"
) else (
  call "%PY_FILE%" -u "%MAIN%"
)

echo.
echo Prozess beendet. Fenster kann geschlossen werden.
exit

