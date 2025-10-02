@echo off
REM Переходим в папку проекта на диске E:
cd /d E:\myenv\ProjectX

REM Активируем виртуальное окружение (если оно в E:\myenv)
call ..\Scripts\activate.bat

REM Запускаем приложение
python main.py

pause