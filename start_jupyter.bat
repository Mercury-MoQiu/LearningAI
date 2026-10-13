@echo off
setlocal
title JupyterLab - pythonProject

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "JUPYTER=%VENV_DIR%\Scripts\jupyter.exe"
set "VPYTHON=%VENV_DIR%\Scripts\python.exe"

REM ================== 首次运行自动初始化 ==================
if exist "%JUPYTER%" goto :run

echo [初始化] 首次运行，正在创建虚拟环境并安装 JupyterLab，请耐心等待...
set "BASE_PYTHON="
where python >nul 2>nul && set "BASE_PYTHON=python"
if not defined BASE_PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "BASE_PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined BASE_PYTHON if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe" set "BASE_PYTHON=%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe"
if not defined BASE_PYTHON (
    echo [错误] 未找到 Python，请先安装 python.org 官方版后重试。
    pause
    exit /b 1
)

"%BASE_PYTHON%" -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo [错误] 虚拟环境创建失败，请检查 Python 安装。
    pause
    exit /b 1
)

"%VPYTHON%" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
"%VPYTHON%" -m pip install jupyterlab ipykernel -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] JupyterLab 安装失败，请检查网络后重新运行本脚本。
    pause
    exit /b 1
)

:run
cd /d "%PROJECT_DIR%"
echo ============================================================
echo   JupyterLab 启动中，浏览器将自动打开...
echo.
echo   工作目录: %PROJECT_DIR%
echo   安装第三方库: 在笔记本单元格中执行  %%pip install 包名
echo   关闭本窗口即可停止 JupyterLab
echo ============================================================
"%JUPYTER%" lab

echo.
echo JupyterLab 已退出。
pause
