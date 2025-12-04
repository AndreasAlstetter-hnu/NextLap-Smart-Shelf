@echo off

rem --- [NEU] minimiert neu starten, falls noch nicht minimiert ---
if /i "%~1" neq "/min" (
  start "" /min "%~f0" /min
  exit /b
)
shift
rem --- [NEU] Ende Relaunch ---

setlocal

rem === muss zu Start-Skript passen ===
set "APP_DIR=C:\Users\Drohnen GmbH\source\repos\NextLap-Smart-Shelf\Next_Lab_Demo\Test_NextLab\Test_Code"
set "MAIN=main.py"

echo Suche laufende "%MAIN%" in:
echo   %APP_DIR%
echo.

rem PIDs der passenden Python-Prozesse ermitteln
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command ^
  "$dir=$env:APP_DIR; $target=$env:MAIN; " ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match [regex]::Escape($target) -and $_.CommandLine -like ('*'+$dir+'*') }; " ^
  "if($procs){ $procs | Select-Object -ExpandProperty ProcessId }"`) do (
  call :TRY_CTRLC %%P
)

echo.
echo Fertig. (Wenn etwas noch laeuft, bitte erneut ausfuehren.)
exit



:TRY_CTRLC
set "PID=%~1"
if "%PID%"=="" goto :eof
echo Versuche sanftes Beenden via Ctrl+C fuer PID %PID% ...

rem Temporäre PS1-Datei mit WinAPI-Aufruf erzeugen (Ctrl+C senden)
set "TMPPS=%TEMP%\_send_ctrl_c_%PID%.ps1"
> "%TMPPS%" (
  echo param([int]$Pid)
  echo Add-Type -TypeDefinition @" 
  echo using System;
  echo using System.Runtime.InteropServices;
  echo public static class CC {
  echo   [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint dwProcessId);
  echo   [DllImport("kernel32.dll", SetLastError=true, ExactSpelling=true)] public static extern bool FreeConsole();
  echo   public delegate bool ConsoleCtrlDelegate(uint CtrlType);
  echo   [DllImport("kernel32.dll", SetLastError=true)] public static extern bool SetConsoleCtrlHandler(ConsoleCtrlDelegate HandlerRoutine, bool Add);
  echo   [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GenerateConsoleCtrlEvent(uint dwCtrlEvent, uint dwProcessGroupId);
  echo }
  echo "@
  echo try {
  echo   ^[CC^]::SetConsoleCtrlHandler($null, $true) ^| Out-Null
  echo   ^[CC^]::AttachConsole([uint32]$Pid) ^| Out-Null
  echo   ^[CC^]::GenerateConsoleCtrlEvent(0, 0) ^| Out-Null    # 0 = CTRL_C_EVENT an alle in dieser Konsole
  echo   Start-Sleep -Milliseconds 800
  echo } finally {
  echo   try { ^[CC^]::FreeConsole() ^| Out-Null } catch {}
  echo   ^[CC^]::SetConsoleCtrlHandler($null, $false) ^| Out-Null
  echo }
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%TMPPS%" -Pid %PID% >nul 2>&1
del "%TMPPS%" >nul 2>&1

rem Kurze Wartezeit, dann prüfen ob noch läuft
timeout /t 1 >nul
tasklist /FI "PID eq %PID%" | find "%PID%" >nul
if errorlevel 1 (
  echo OK: Prozess %PID% wurde sanft beendet.
  goto :eof
)

echo Warnung: PID %PID% laeuft noch. Erzwinge Beenden ...
taskkill /PID %PID% /T /F >nul 2>&1
if errorlevel 1 (
  echo FEHLER: Konnte PID %PID% nicht beenden.
) else (
  echo OK: PID %PID% hart beendet.
)
goto :eof
