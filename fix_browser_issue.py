#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器问题修复工具
用于解决 "Target page, context or browser has been closed" 错误
"""

import os
import sys
import shutil
import psutil
import signal
import glob
from pathlib import Path


def kill_browser_processes():
    """终止所有残留的浏览器进程"""
    print("正在查找并终止残留的浏览器进程...")
    
    browser_process_names = [
        'chrome', 'chromium', 'chromium-browser',
        'google-chrome', 'google-chrome-stable'
    ]
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            process_name = proc.info['name'].lower()
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            
            # 检查是否是浏览器进程
            if any(name in process_name for name in browser_process_names):
                # 进一步检查是否包含我们的用户数据目录
                if 'ks_user_data_dir' in cmdline or 'browser_data' in cmdline:
                    print(f"终止进程 {proc.info['pid']}: {proc.info['name']}")
                    try:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        killed_count += 1
                    except (OSError, psutil.NoSuchProcess):
                        pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"已终止 {killed_count} 个浏览器进程")


def clean_browser_data():
    """清理浏览器数据目录中的锁定文件"""
    print("正在清理浏览器数据目录...")
    
    # 查找可能的浏览器数据目录
    data_dirs = [
        "./browser_data",
        "./crawler/browser_data", 
        "/root/dy-video-factory/crawler/browser_data"
    ]
    
    for base_dir in data_dirs:
        if os.path.exists(base_dir):
            print(f"清理目录: {base_dir}")
            
            # 查找快手相关的用户数据目录
            ks_dirs = glob.glob(os.path.join(base_dir, "*ks_user_data_dir*"))
            
            for ks_dir in ks_dirs:
                print(f"处理快手数据目录: {ks_dir}")
                
                # 清理锁定文件
                lock_files = [
                    "SingletonLock",
                    "SingletonSocket", 
                    "SingletonCookie",
                    "Singleton",
                    ".com.google.Chrome*",
                    "chrome_debug_*.log"
                ]
                
                for lock_pattern in lock_files:
                    lock_paths = glob.glob(os.path.join(ks_dir, "**", lock_pattern), recursive=True)
                    lock_paths.extend(glob.glob(os.path.join(ks_dir, lock_pattern)))
                    
                    for lock_path in lock_paths:
                        try:
                            if os.path.isfile(lock_path):
                                os.remove(lock_path)
                                print(f"  删除锁定文件: {lock_path}")
                            elif os.path.isdir(lock_path):
                                shutil.rmtree(lock_path)
                                print(f"  删除锁定目录: {lock_path}")
                        except (OSError, PermissionError) as e:
                            print(f"  无法删除 {lock_path}: {e}")


def clean_temp_files():
    """清理临时文件"""
    print("正在清理临时文件...")
    
    temp_patterns = [
        "/tmp/.com.google.Chrome*",
        "/tmp/chrome_*",
        "/tmp/.org.chromium.Chromium*",
        "/tmp/kuaishou_*.png"
    ]
    
    for pattern in temp_patterns:
        temp_files = glob.glob(pattern)
        for temp_file in temp_files:
            try:
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
                    print(f"删除临时文件: {temp_file}")
                elif os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
                    print(f"删除临时目录: {temp_file}")
            except (OSError, PermissionError) as e:
                print(f"无法删除 {temp_file}: {e}")


def check_system_resources():
    """检查系统资源使用情况"""
    print("\n检查系统资源...")
    
    # 检查内存使用
    memory = psutil.virtual_memory()
    print(f"内存使用率: {memory.percent}%")
    
    # 检查磁盘使用
    disk = psutil.disk_usage('/')
    print(f"磁盘使用率: {disk.percent}%")
    
    # 检查是否有足够的空间
    if disk.percent > 95:
        print("警告: 磁盘空间不足，这可能导致浏览器启动失败")
    
    if memory.percent > 90:
        print("警告: 内存使用率过高，建议重启系统")


def main():
    """主函数"""
    print("=" * 50)
    print("浏览器问题修复工具")
    print("=" * 50)
    
    try:
        # 1. 终止残留进程
        kill_browser_processes()
        
        # 2. 清理浏览器数据
        clean_browser_data()
        
        # 3. 清理临时文件
        clean_temp_files()
        
        # 4. 检查系统资源
        check_system_resources()
        
        print("\n" + "=" * 50)
        print("修复完成！现在可以重新运行爬虫程序。")
        print("=" * 50)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"\n修复过程中出现错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 