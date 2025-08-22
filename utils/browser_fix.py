#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器自动清理工具
当遇到浏览器启动问题时自动清理残留进程和锁定文件
"""

import os
import shutil
import psutil
import signal
import glob
import asyncio
from typing import Optional


class BrowserAutoFixer:
    """浏览器自动修复工具"""
    
    @staticmethod
    def is_browser_error(error_message: str) -> bool:
        """判断是否为浏览器相关错误"""
        browser_error_patterns = [
            "Target page, context or browser has been closed",
            "BrowserType.launch_persistent_context",
            "browser_context",
            "Connection closed",
            "Protocol error",
            "Target closed"
        ]
        
        return any(pattern in error_message for pattern in browser_error_patterns)
    
    @staticmethod
    def kill_browser_processes(verbose: bool = True) -> int:
        """终止残留的浏览器进程"""
        if verbose:
            print("📝 正在终止残留的浏览器进程...")
        
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
                        if verbose:
                            print(f"  终止进程 {proc.info['pid']}: {proc.info['name']}")
                        try:
                            os.kill(proc.info['pid'], signal.SIGTERM)
                            killed_count += 1
                        except (OSError, psutil.NoSuchProcess):
                            pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if verbose:
            print(f"✅ 已终止 {killed_count} 个浏览器进程")
        return killed_count
    
    @staticmethod
    def clean_browser_data(verbose: bool = True) -> int:
        """清理浏览器数据目录中的锁定文件"""
        if verbose:
            print("📝 正在清理浏览器数据目录...")
        
        data_dirs = [
            "./browser_data",
            "./crawler/browser_data", 
            "/root/dy-video-factory/crawler/browser_data"
        ]
        
        cleaned_count = 0
        for base_dir in data_dirs:
            if os.path.exists(base_dir):
                # 查找所有用户数据目录
                user_dirs = glob.glob(os.path.join(base_dir, "*user_data_dir*"))
                
                for user_dir in user_dirs:
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
                        lock_paths = glob.glob(os.path.join(user_dir, "**", lock_pattern), recursive=True)
                        lock_paths.extend(glob.glob(os.path.join(user_dir, lock_pattern)))
                        
                        for lock_path in lock_paths:
                            try:
                                if os.path.isfile(lock_path):
                                    os.remove(lock_path)
                                    cleaned_count += 1
                                elif os.path.isdir(lock_path):
                                    shutil.rmtree(lock_path)
                                    cleaned_count += 1
                            except (OSError, PermissionError):
                                pass
        
        if verbose:
            print(f"✅ 已清理 {cleaned_count} 个锁定文件/目录")
        return cleaned_count
    
    @staticmethod
    def clean_temp_files(verbose: bool = True) -> int:
        """清理临时文件"""
        if verbose:
            print("📝 正在清理临时文件...")
        
        temp_patterns = [
            "/tmp/.com.google.Chrome*",
            "/tmp/chrome_*",
            "/tmp/.org.chromium.Chromium*",
            "/tmp/kuaishou_*.png",
            "/tmp/douyin_*.png"
        ]
        
        temp_cleaned = 0
        for pattern in temp_patterns:
            temp_files = glob.glob(pattern)
            for temp_file in temp_files:
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        temp_cleaned += 1
                    elif os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                        temp_cleaned += 1
                except (OSError, PermissionError):
                    pass
        
        if verbose:
            print(f"✅ 已清理 {temp_cleaned} 个临时文件")
        return temp_cleaned
    
    @classmethod
    def auto_fix(cls, verbose: bool = True) -> bool:
        """自动修复浏览器问题"""
        if verbose:
            print("\n🔧 检测到浏览器启动问题，正在自动清理...")
            print("=" * 60)
        
        try:
            # 1. 终止残留进程
            killed = cls.kill_browser_processes(verbose)
            
            # 2. 清理浏览器数据目录中的锁定文件
            cleaned = cls.clean_browser_data(verbose)
            
            # 3. 清理临时文件
            temp_cleaned = cls.clean_temp_files(verbose)
            
            if verbose:
                print("=" * 60)
                print("🎉 自动清理完成！")
                print(f"📊 统计：终止进程 {killed} 个，清理锁定文件 {cleaned} 个，清理临时文件 {temp_cleaned} 个")
                
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ 自动清理过程中出现错误: {e}")
                print("建议手动运行：python fix_browser_issue.py")
            return False
    
    @classmethod
    async def auto_fix_with_retry(cls, func, max_retries: int = 2, verbose: bool = True) -> bool:
        """带自动清理的重试机制"""
        for attempt in range(max_retries + 1):
            try:
                await func()
                return True
            except Exception as e:
                error_message = str(e)
                
                # 检查是否是浏览器错误
                if cls.is_browser_error(error_message) and attempt < max_retries:
                    if verbose:
                        print(f"\n🤖 第 {attempt + 1} 次尝试失败，检测到浏览器问题，正在自动处理...")
                    
                    # 自动清理
                    if cls.auto_fix(verbose):
                        if verbose:
                            print(f"🔄 等待 3 秒后进行第 {attempt + 2} 次尝试...")
                        await asyncio.sleep(3)
                        continue
                    else:
                        if verbose:
                            print("❌ 自动清理失败")
                        break
                else:
                    # 非浏览器错误或重试次数已达上限
                    if verbose:
                        if cls.is_browser_error(error_message):
                            print(f"\n❌ 已重试 {max_retries} 次仍然失败")
                            print("📋 建议手动运行：python fix_browser_issue.py")
                        else:
                            print(f"\n📋 其他错误：{error_message}")
                    raise
        
        return False


# 保持向后兼容的函数
def auto_fix_browser_issue(verbose: bool = True) -> bool:
    """自动修复浏览器问题（向后兼容函数）"""
    return BrowserAutoFixer.auto_fix(verbose)


def is_browser_error(error_message: str) -> bool:
    """判断是否为浏览器相关错误（向后兼容函数）"""
    return BrowserAutoFixer.is_browser_error(error_message) 