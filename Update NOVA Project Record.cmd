@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Update-NovaProjectRecord.ps1"
if errorlevel 1 pause
