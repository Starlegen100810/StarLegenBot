@echo off
setlocal
rem գնա այս .bat-ի պապկա, անկախ որ տեղից ես բացում
pushd %~dp0

:loop
REM եթե Python-ը PATH-ում է՝ սա հերիք է
python "%~dp0main.py"

REM եթե «python is not recognized» լինի, փոխիր վերևի տողը այսով՝
REM "C:\Users\YOUR_USER\AppData\Local\Programs\Python\Python311\python.exe" "%~dp0main.py"

echo [%date% %time%] Bot exited. Restart in 5s...
timeout /t 5 /nobreak >nul
goto loop
