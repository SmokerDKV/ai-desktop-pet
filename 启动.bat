@echo off
chcp 65001 >nul
echo 正在启动桌面宠物...
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

pip show pillow >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

python deskpet.py
if errorlevel 1 (
    echo 程序异常退出，按任意键查看错误信息
    pause
)
