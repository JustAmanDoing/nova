@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Nova.ps1" phone-disable
if errorlevel 1 pause
