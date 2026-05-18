@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запуск сервера парсера цен...
echo.
echo Браузер откроется через 2 секунды по адресу http://127.0.0.1:5000
echo Чтобы остановить сервер — закрой это окно или нажми Ctrl+C
echo.
start "" /b cmd /c "timeout /t 2 >nul && start "" http://127.0.0.1:5000"
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 server.py
) else (
    python server.py
)
pause
