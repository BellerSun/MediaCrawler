@echo off
chcp 65001 >nul
echo ============================================================
echo Windows浏览器问题修复工具（批处理版本）
echo ============================================================
echo.

echo 正在检查浏览器数据目录...

REM 检查并删除浏览器数据目录
if exist "browser_data" (
    echo 找到browser_data目录
    if exist "browser_data\ks_user_data_dir" (
        echo 正在删除快手用户数据目录...
        rmdir /s /q "browser_data\ks_user_data_dir"
        if %errorlevel%==0 (
            echo 成功删除: browser_data\ks_user_data_dir
        ) else (
            echo 删除失败，请手动删除该目录
        )
    ) else (
        echo 未找到快手用户数据目录
    )
    
    REM 清理其他可能的快手相关目录
    for /d %%i in ("browser_data\*ks*") do (
        echo 删除目录: %%i
        rmdir /s /q "%%i"
    )
    
) else (
    echo 未找到browser_data目录
)

echo.
echo 正在清理临时文件...

REM 清理临时目录中的Chrome相关文件
if exist "%TEMP%\chrome_*" (
    echo 清理临时Chrome文件...
    del /s /q "%TEMP%\chrome_*" 2>nul
)

if exist "%TEMP%\Chromium_*" (
    echo 清理临时Chromium文件...
    del /s /q "%TEMP%\Chromium_*" 2>nul
)

echo.
echo ============================================================
echo 修复完成！
echo.
echo 如果问题仍然存在，请尝试以下步骤：
echo 1. 重启计算机
echo 2. 手动删除整个 browser_data 文件夹
echo 3. 使用任务管理器结束所有Chrome/Chromium进程
echo 4. 重新运行爬虫程序
echo ============================================================
echo.

pause 