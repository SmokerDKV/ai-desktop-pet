@echo off
chcp 65001 >nul
echo 正在初始化环境...
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 检测到Python版本：
python --version

echo.
echo 正在安装依赖包...
pip install pillow==10.4.0 requests==2.32.3

if errorlevel 1 (
    echo.
    echo 安装失败，尝试使用国内镜像...
    pip install pillow==10.4.0 requests==2.32.3 -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo 初始化完成！现在可以双击"启动.bat"运行程序。
pause
