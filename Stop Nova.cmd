@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Nova.ps1" stop
if errorlevel 1 pause
