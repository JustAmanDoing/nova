@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Nova.ps1" update
if errorlevel 1 pause
