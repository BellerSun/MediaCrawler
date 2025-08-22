#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Windows浏览器问题修复工具 - 简化版
"""

import os
import sys
import glob
import shutil


def clean_browser_data_windows():
    """清理Windows下的浏览器数据目录"""
    print("正在清理浏览器数据目录...")
    
    # Windows下可能的浏览器数据目录
    data_dirs = [
        "./browser_data",
        ".\\browser_data",
        "browser_data"
    ]
    
    cleaned = False
    
    for base_dir in data_dirs:
        if os.path.exists(base_dir):
            print(f"找到目录: {base_dir}")
            
            # 查找快手相关的用户数据目录
            ks_pattern = os.path.join(base_dir, "*ks_user_data_dir*")
            ks_dirs = glob.glob(ks_pattern)
            
            if not ks_dirs:
                # 尝试其他可能的模式
                ks_dirs = [d for d in os.listdir(base_dir) if 'ks' in d.lower() and 'user_data' in d.lower()]
                ks_dirs = [os.path.join(base_dir, d) for d in ks_dirs]
            
            for ks_dir in ks_dirs:
                if os.path.exists(ks_dir):
                    print(f"清理快手数据目录: {ks_dir}")
                    try:
                        shutil.rmtree(ks_dir)
                        print(f"成功删除: {ks_dir}")
                        cleaned = True
                    except Exception as e:
                        print(f"删除失败: {e}")
                        print("请手动删除此目录")
    
    return cleaned


def clean_temp_files_windows():
    """清理Windows临时文件"""
    print("正在清理临时文件...")
    
    # Windows临时目录
    temp_dirs = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        'C:\\Windows\\Temp'
    ]
    
    patterns = [
        'chrome_*',
        'Chromium_*'
    ]
    
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            for pattern in patterns:
                temp_pattern = os.path.join(temp_dir, pattern)
                temp_files = glob.glob(temp_pattern)
                for temp_file in temp_files:
                    try:
                        if os.path.isfile(temp_file):
                            os.remove(temp_file)
                            print(f"删除临时文件: {temp_file}")
                        elif os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                            print(f"删除临时目录: {temp_file}")
                    except Exception as e:
                        print(f"无法删除 {temp_file}: {e}")


def main():
    print("=" * 60)
    print("Windows浏览器问题修复工具")
    print("=" * 60)
    
    try:
        # 清理浏览器数据
        cleaned = clean_browser_data_windows()
        
        # 清理临时文件
        clean_temp_files_windows()
        
        print("\n" + "=" * 60)
        if cleaned:
            print("修复完成！已清理浏览器数据目录。")
        else:
            print("未找到需要清理的浏览器数据目录。")
        
        print("\n手动解决方案（如果问题仍然存在）:")
        print("1. 手动删除目录: browser_data\\ks_user_data_dir")
        print("2. 重启计算机")
        print("3. 重新运行爬虫程序")
        print("=" * 60)
        
    except Exception as e:
        print(f"修复过程出现错误: {e}")
        print("\n请尝试手动解决方案:")
        print("1. 打开文件管理器")
        print("2. 删除整个 browser_data 文件夹")
        print("3. 重新运行程序")


if __name__ == "__main__":
    main() 