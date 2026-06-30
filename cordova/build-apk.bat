@echo off
REM ============================================
REM  员工管理系统 APK 构建脚本
REM  需要先安装：Node.js + Cordova + Android SDK
REM ============================================

echo.
echo === 员工管理系统 APK 构建工具 ===
echo.
echo 前置要求：
echo   1. Node.js (https://nodejs.org)
echo   2. Android Studio + SDK (https://developer.android.com/studio)
echo   3. JAVA JDK 17+
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM 检查 Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未安装 Node.js，请先安装：https://nodejs.org
    pause
    exit /b 1
)

REM 检查 Cordova
where cordova >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [安装] 正在安装 Cordova...
    npm install -g cordova
)

echo [1/4] 创建 Cordova 项目...
if not exist "platforms" (
    cordova create . temp employee-management 2>nul
)

echo [2/4] 复制配置文件...
copy /Y config.xml config.xml.tmp 2>nul
copy /Y config.xml www/../ 2>nul

echo [3/4] 添加 Android 平台...
cordova platform add android --nofetch 2>nul
if %ERRORLEVEL% neq 0 (
    cordova platform add android
)

echo [4/4] 构建 APK...
cordova build android --release

echo.
if %ERRORLEVEL% equ 0 (
    echo ===== 构建成功！=====
    echo APK 位置：platforms\android\app\build\outputs\apk\release\
    echo.
    echo 将 APK 复制到手机即可安装使用。
) else (
    echo ===== 构建失败 =====
    echo 请检查 Android SDK 配置：
    echo 1. 设置 ANDROID_HOME 环境变量
    echo 2. 安装 Android SDK Platform 34
    echo 3. 安装 Android SDK Build-Tools
)

pause
